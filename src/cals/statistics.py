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
from django.contrib.auth.models import User

import pygal
from pygal.style import LightGreenStyle, Style

from nano.countries.models import Country

from cals.forms import *
from cals.tools import compare_features
from cals.modeltools import LANGTYPES, language_alphabetic_letters, \
        language_first_letters
from cals.modeltools import languages_ranked_by_averageness, get_langs, \
        compare_value_sets, compare_languages, feature_usage, \
        language_most_average_internal, set_averageness_for_langs, \
        get_averageness_for_lang
from cals.feature.models import FeatureValue, Feature
from cals.language.models import Language
from cals.people.models import Profile
from cals.models import LanguageFeature

from translations.models import Translation

def country_most_common():
    return Country.objects.annotate(count=Count('profile')).filter(count__gt=0).order_by('-count')

def conlanger_map():
    foo = dict([(country.iso.lower(), country.count) for country in country_most_common()])

    chart = pygal.Worldmap(style=LightGreenStyle)
    chart.disable_xml_declaration = True
    chart.show_legend = False
    chart.add('Conlangers', foo)
    return chart.render()

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

def median(datapoints, n=0):
    n = n or len(datapoints)
    datapoints = sorted(datapoints)
    middle = n / 2
    if n % 2:
        # odd
        return datapoints[middle]
    else:
        # even
        return (datapoints[middle-1] + datapoints[middle]) / 2

def stddev(datapoints):
    from math import sqrt
    n = float(len(datapoints))
    mean = sum(datapoints)/n
    std = sqrt(sum((float(dp) - mean)**2 for dp in datapoints)/n)
    return std

def vocab_chart(rows):
    chart = pygal.Line(style=LightGreenStyle)
    chart.disable_xml_declaration = True
    chart.show_y_guides = False
    chart.show_dots = False
    chart.human_readable = True
    chart.show_legend = False
    chart.add('', rows)
    return chart.render()

def vocab_size():
    """Generate statistics on the vocabulary_size-field."""

    MAXSIZE = 10000

    ls = Language.objects.exclude(id=80).filter(vocabulary_size__gt=0, vocabulary_size__lte=MAXSIZE).conlangs()

    outliers = Language.objects.filter(vocabulary_size__gt=MAXSIZE).order_by('vocabulary_size')

    # Assumes unimodal distribution
    modes = [(mode['count'], mode['vocabulary_size'])
            for mode in ls.values('vocabulary_size').annotate(count=Count('vocabulary_size')).order_by('-count', '-vocabulary_size') 
            if mode['count'] > 5]
    mode = modes[0][1]

    avg_maximum_minimum = ls.aggregate(avg=Avg('vocabulary_size'), maximum=Max('vocabulary_size'), minimum=Min('vocabulary_size'))
    avg = avg_maximum_minimum['avg']
    maximum = avg_maximum_minimum['maximum']
    minimum = avg_maximum_minimum['minimum']

    curve = ls.order_by('-vocabulary_size')
    rows = [v.vocabulary_size for v in curve]

    chart_svg = vocab_chart(rows)

    # median
    med = median(rows)
    
    return {'average': avg, 
            'min': minimum, 
            'max': maximum, 
            'median': med, 
            'chart_svg': chart_svg,
            'mode': mode,
            'common': modes,
            'stddev': stddev(rows),
            'outliers': outliers,
            'upper_bound': MAXSIZE}

def get_all_lurkers():
    users = User.objects.filter(is_active=True, profile__is_visible=True)
    lurkers = users.filter(edits__isnull=True,
            manages__isnull=True,
            translations__isnull=True, 
            languages__isnull=True,
            translation_exercises__isnull=True, 
            languages_modified__isnull=True)
    return lurkers

def country():

    barchart = pygal.Bar(style=LightGreenStyle)
    barchart.add('', [c.count for c in country_most_common()])
    barchart.x_labels = [c.name for c in country_most_common()]
    barchart.x_label_rotation = 90

    return {
        'most_common': country_most_common(),
        'map': conlanger_map(),
        'chart': barchart.render(),
    }

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
    user250 = User.objects.get(id=336)
    lang100 = conlangs.get(id=154)
    lang150 = conlangs.get(id=271)
    lang200 = conlangs.get(id=466)
    lang250 = conlangs.get(id=526)

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

    features_mu = feature_usage(langtype=LANGTYPES.CONLANG, limit=20)
    natlang_features_mu = feature_usage(langtype=LANGTYPES.NATLANG, limit=20)
    not_used = unused_featurevalues()

    countries = country_most_common()
    cmap = conlanger_map()

    skeleton_langs = conlangs.filter(num_features=0)

    data = {}
    data['milestones'] = { 
            'user100': user100, 
            'user150': user150,
            'user200': user200,
            'user250': user250,
            'lang100': lang100,
            'lang150': lang150,
            'lang200': lang200,
            'lang250': lang250,
            }
    data['features'] = { 
            'number': num_features,
            'percentage_wals': str(142/float(num_features)*100),
            'most_used': features_mu,
            'natlang_most_used': natlang_features_mu,
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
            'first_letters': {
                    'conlangs': language_first_letters(), 
                    'natlangs': language_first_letters(langtype=LANGTYPES.NATLANG), 
            },
            'alpha_letters': {
                    'conlangs': language_alphabetic_letters(), 
                    'natlangs': language_alphabetic_letters(langtype=LANGTYPES.NATLANG), 
            },
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
            'country': country(),
            'percentage_countries': str(num_countries/float(num_users)*100),
            'percentage_lurkers': str(num_lurkers / float(num_users) * 100)
            }
    return data

