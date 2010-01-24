# Create your views here.
from random import choice, sample
import time
import unicodedata
import sys

import logging
_LOG = logging.getLogger(__name__)

from django.db import connection
from django.http import HttpResponseNotFound, HttpResponseForbidden
from django.shortcuts import render_to_response, get_object_or_404
from django.db.models import Q, Count, Avg, Max, Min

from pygooglechart import Axis, SimpleLineChart

from cals.models import *
from cals.models import Country, FeatureValue, Language, User, \
        Feature, Profile, LanguageFeature
from cals.forms import *
from cals.tools import LANGTYPES, language_alphabetic_letters, \
        language_first_letters
from cals.tools import languages_ranked_by_averageness, get_langs, \
        compare_value_sets, compare_languages, feature_usage, \
        language_most_average_internal, set_averageness_for_langs, \
        get_averageness_for_lang, compare_features

from translations.models import Translation

def country_most_common():
    return Country.objects.annotate(count=Count('profile')).filter(count__gt=0).order_by('-count')

def unused_featurevalues():
    """Returns feature values not used by conlangs.
    
    That is, values only used by natlangs are also included.
    """

    fvs = FeatureValue.objects.filter(feature__active=True)
    unused_fvs = fvs.filter(languagefeature__isnull=True)
    natlang_only_fvs = fvs.filter(languagefeature__language__natlang=True).exclude(languagefeature__language__natlang=False)

    if not natlang_only_fvs:
        # Natlangs had no unique features so return early
        return unused_fvs

    # dsd
    decorate = ((fv.id, fv) for fv in set(unused_fvs) | set(natlang_only_fvs))
    sort = sorted(decorate)
    return [fv for (_, fv) in sort]

def timeline():
    "Statistics over which days/weeks/months are most visited/update etc."
    joined = User.objects.dates('date_joined', 'day')
    login = User.objects.dates('last_login', 'day')
    created = Language.objects.dates('created', 'day')
    last_modified = Language.objects.dates('last_modified', 'day')
    _LOG.info('Joined: %s' % joined[:5])

def vocab_size():
    """Generate statistics on the vocabulary_size-field."""

    mode = """SELECT vocabulary_size, count(*) AS c 
    FROM cals_language
    WHERE vocabulary_size IS NOT NULL AND id != 80 
    GROUP BY vocabulary_size 
    ORDER BY c DESC LIMIT 1"""

    cursor = connection.cursor()
    cursor.execute(mode)
    for row in cursor.fetchall():
        mode = row[0]
        break

    ls = Language.objects.only('vocabulary_size').conlangs().filter(vocabulary_size__isnull=False).exclude(id=80)
    avg_max_min = ls.aggregate(avg=Avg('vocabulary_size'), max=Max('vocabulary_size'), min=Min('vocabulary_size'))
    avg = avg_max_min['avg']
    max = avg_max_min['max']
    min = avg_max_min['min']

    curve = ls.order_by('-vocabulary_size')
    rows = [v.vocabulary_size for v in curve]

    chart = SimpleLineChart(400, 200, y_range=(0, max))
    chart.add_data(rows)
    chart.set_axis_labels(Axis.LEFT, 
            ['0', '2000', '4000',
            '6000', '8000', '10000', 
            '12000', '14000', str(int(max))])
    chart_url = chart.get_url()

    # median
    num_rows = len(rows)
    middle = num_rows / 2
    if num_rows % 2:
        median = rows[middle-1]
    else:
        median = (rows[middle] + rows[middle+1]) / 2
    
    return {'average': avg, 
            'min': min, 
            'max': max, 
            'median': median, 
            'chart': chart_url,
            'mode': mode }

def get_all_lurkers():
    users = User.objects.filter(is_active=True, profile__is_visible=True)
    lurkers = users.filter(edits__isnull=True,
            manages__isnull=True,
            translations__isnull=True, 
            languages__isnull=True,
            translation_exercises__isnull=True, 
            languages_modified__isnull=True)
    return lurkers

def generate_global_stats():
    "Used by the statistics-view"
    features = Feature.objects.active()
    fvs = FeatureValue.objects.filter(feature__active=True) #value_counts()
    langs = Language.objects.all()
    conlangs = Language.objects.conlangs()
    natlangs = Language.objects.natlangs()
    users = Profile.objects.filter(user__is_active=True, is_visible=True)
    lfs = LanguageFeature.objects.all()

    user100 = User.objects.get(id=139)
    user150 = User.objects.get(id=200)
    user200 = User.objects.get(id=284)
    lang100 = conlangs.get(id=154)
    lang150 = conlangs.get(id=271)
    lang200 = conlangs.get(id=466)

    num_features = features.count()
    num_conlangs = conlangs.count()
    num_natlangs = natlangs.count()
    num_langs = num_conlangs + num_natlangs
    num_users = users.count()
    num_lfs = lfs.count()
    num_greetings = Language.objects.conlangs().exclude(greeting__isnull=True).count()
    num_backgrounds = Language.objects.conlangs().exclude(background__isnull=True).exclude(background='').count()
    num_translations = Translation.objects.count()
    num_countries = users.filter(country__isnull=False).count()
    num_lurkers = len(get_all_lurkers())

    most_average = conlangs.exclude(num_features=0).order_by('-average_score', '-num_features')
    most_average_natlangs = natlangs.order_by('-average_score', '-num_features')[:20]
    lma = most_average.count()
    least_average = tuple(most_average)[-10:]
    most_average = most_average[:20]

    features_mu = feature_usage(limit=20)
    not_used = unused_featurevalues()

    countries = country_most_common()

    skeleton_langs = conlangs.filter(num_features=0)

    data = {}
    data['milestones'] = { 
            'user100': user100, 
            'user150': user150,
            'user200': user200,
            'lang100': lang100,
            'lang150': lang150,
            'lang200': lang200,
            }
    data['features'] = { 
            'number': num_features,
            'percentage_wals': str(142/float(num_features)*100),
            'most_used': features_mu,
            #'least_used': tuple(reversed(features_mu))[:20],
            'not_used': not_used,
            'num_not_used': len(not_used),
            }
    data['langs'] = { 
            'number': num_conlangs, 
            'number_natlangs': num_natlangs, 
            'features_per_lang': str(num_lfs/float(num_langs)),
            'percentage_greetings': str(num_greetings/float(num_langs)*100),
            'percentage_backgrounds': str(num_backgrounds/float(num_langs)*100),
            'num_translations': num_translations,
            'first_letters': language_first_letters(),
            'alpha_letters': language_alphabetic_letters(),
            'most_average': most_average,
            'most_average_natlangs': most_average_natlangs,
            'least_average': least_average,
            'lma': lma-10,
            'skeleton_langs': skeleton_langs,
            'vocabulary': vocab_size(),
            }
    data['users'] = { 
            'number': num_users,
            'langs_per_user': str(num_langs/float(num_users)),
            'countries': countries,
            'percentage_countries': str(num_countries/float(num_users)*100),
            'percentage_lurkers': str(num_lurkers / float(num_users) * 100)
            }
    return data

