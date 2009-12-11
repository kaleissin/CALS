# Create your views here.
from random import choice, sample
import time
import unicodedata
import string
import sys

import logging
_LOG = logging.getLogger(__name__)

from django.contrib.contenttypes.models import ContentType
from django.db import connection
from django.http import HttpResponseNotFound, HttpResponseForbidden
from django.shortcuts import render_to_response, get_object_or_404
from django.db.models import Q, Count, Avg, Max, Min

from pygooglechart import StackedVerticalBarChart, Axis, SimpleLineChart

from cals.models import *
from cals.forms import *
from translations.models import Translation

class LANGTYPES(object):
    CONLANG = 1
    NATLANG = 2
    ALL = CONLANG + NATLANG

    types = (ALL, NATLANG, CONLANG)

def firstletter_langnames(langtype=LANGTYPES.ALL):
    assert langtype in LANGTYPES.types
    if langtype == LANGTYPES.CONLANG:
        langs = Language.objects.conlangs()
    if langtype == LANGTYPES.NATLANG:
        langs = Language.natlangs.all()
    else:
        langs = Language.objects.all()
    return [l.name.upper().strip()[0] for l in langs.only('name').all()]

def string_statistics(strings):
    """Counts how many times each string occurs and calculates percentages"""
    num_strings = float(len(strings))
    outdict = {}
    for string in strings:
        outdict[string] = outdict.get(string, 0) + 1 
    return [(string, count, count/num_strings*100) for (string, count) in outdict.items()]

def language_alphabetic_letters(num = 10):
    letters = firstletter_langnames(langtype=LANGTYPES.CONLANG)
    letters = string_statistics(letters)

    return {'letters': [{'char': l, 'count': c, 'percentage': p} for l, c, p in letters]}

def language_first_letters(num = 10):
    letters = firstletter_langnames(langtype=LANGTYPES.CONLANG)
    letters = string_statistics(letters)

    #dsd
    letters = reversed(sorted([(c, l, p) for l, c, p in letters]))
    return {'letters': [{'char': l, 'count': c, 'percentage': p} for c, l, p in letters]}

def compare_value_sets(values1, values2):
    v1 = set(values1)
    v2 = set(values2)
    num_f = Feature.objects.active().count()
    return len(v1 & v2)

def compare_features(features, vfs):
    """Matrix comparing usage of two features.
    
    TODO: links in gridpoints to list of languages having both
    values."""

    # matrix is currently f1 horisontal, f2 vertical
    f1, f2 = features
    vf1, vf2 = vfs
    feature_comparison = """SELECT v1.value_id, v2.value_id, count(*) 
    FROM "cals_languagefeature" AS v1, "cals_languagefeature" AS v2 
    WHERE v1.language_id = v2.language_id
        AND v1.feature_id = %i 
        AND v2.feature_id = %i 
    GROUP BY v1.value_id, v2.value_id 
    ORDER BY v1.value_id, v2.value_id""" % (f1.id, f2.id)

    cursor = connection.cursor()
    cursor.execute(feature_comparison)

    # Prefill comparison-matrix with zeroes
    matrix = {}
    lvf2 = len(vf2)
    for v1 in vf1:
        matrix[v1.id] = dict(zip([v2.id for v2 in vf2], (0,)*lvf2))

    # Update the matrix with values from db
    for row in cursor.fetchall():
        v1, v2, count = row
        matrix[v1][v2] = count

    return matrix

def compare_languages(langs, same=True, different=True):
    """Side-by-side comparison of languages, all features at least one
    of the languages have is shown."""

    num_langs = len(langs)
    features = Feature.objects.active().order_by('id')
    comparison = [(None,) + tuple(langs)]
    num_features = tuple(['Number of features'] + [lang.num_features for lang in langs])
    _LOG.info('2: compare_languages: %s %s' % (same, different))
    _LOG.info('3: num_features %s' % `num_features`)
    a, b, c = 0, 0, 0
    d = 0
    for feature in features:
        d += 1
        lang_list = []
        for lang in langs:
            try:
                lf = lang.features.get(feature=feature)
            except LanguageFeature.DoesNotExist:
                lang_list.append(None)
            else:
                lang_list.append(lf.value)
        if any(lang_list):
            if same == different:
                comparison.append(tuple([feature] + lang_list))
                a += 1
            else:
                s = len(set(lang_list)) == 1
                d = len(set(lang_list)) > 1
                if same and s:
                    comparison.append(tuple([feature] + lang_list))
                    b += 1
                elif different and d:
                    comparison.append(tuple([feature] + lang_list))
                    c += 1
    _LOG.info('4: a %s b %s c %s d %s' % (a, b, c, d))
    return comparison

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

def feature_usage(langtype=LANGTYPES.ALL, limit=0):
    assert langtype in LANGTYPES.types

    fvs = FeatureValue.objects.filter(feature__active=True)
    ls = Language.objects
    if langtype == LANGTYPES.NATLANG:
        ls = ls.natlangs()
        fvs = fvs.filter(languagefeature__language__natlang=True)
    elif langtype == LANGTYPES.CONLANG:
        ls = ls.conlangs()
        fvs = fvs.filter(languagefeature__language__natlang=False)

    num_langs = ls.count()
    fvs = fvs.annotate(count=Count('languagefeature')).order_by('-count')

    if limit:
        fvs = fvs[:limit]

    rows = [{'value': fv,
            'feature': fv.feature,
            'languages': fv.count,
            'percentage': str(fv.count/float(num_langs)*100) }
            for fv in fvs]
    return rows

def language_most_average_internal(langtype=LANGTYPES.ALL):
    assert langtype in LANGTYPES.types
    features = {}
    for f in feature_usage(langtype=langtype):
        feature = f['feature']
        value = f['value']
        languages = f['languages']
        features.setdefault(feature, []).append((value, languages))
    max_values = {}
    for feature, values in features.items():
        c = 0
        for value, languages in values:
            if languages > c:
                c = languages
                max_values[feature] = {'value': value, 'count': languages}
    return max_values

def most_popular_values():
    # TODO, replaces language_most_average_internal
    # Uses the view cals_feature_value_maxcount
    max_value_string = """SELECT * FROM cals_feature_value_maxcount"""
    cursor = connection.cursor()
    cursor.execute(max_value_string)
    pass

def get_averageness_for_lang(lang, scale=100, max_values=None, average_features=None, langtype=LANGTYPES.ALL):
    assert langtype in LANGTYPES.types
    if not max_values:
        max_values = language_most_average_internal(langtype=langtype)
    if not average_features:
        average_features = [v['value'].id for k, v in max_values.items()]
    values = [lf.value.id for lf in lang.features.all()]
    if not values: 
        return 0
    frequency = compare_value_sets(average_features, values)
    return frequency

def set_averageness_for_langs(langtype=LANGTYPES.ALL):
    assert langtype in LANGTYPES.types
    max_values = language_most_average_internal(langtype=langtype)
    average_features = [v['value'].id for k, v in max_values.items()]
    for l in Language.objects.all():
        num = l.features.count()
        if not num: continue
        freq = get_averageness_for_lang(l, max_values=max_values, average_features=average_features)
        if freq == None: continue
        l.num_avg_features = freq
        l.num_features = num
        l.set_average_score()
        l.save(solo=False)

def joined():
    "Statistics over which days/weeks/months are most visited/update etc."
    joined = User.objects.dates('date_joined', 'day')
    login = User.objects.dates('last_login', 'day')
    created = Language.objects.dates('created', 'day')
    last_modified = Language.objects.dates('last_modified', 'day')
    _LOG.info('Joined: %s' % joined[:5])

def languages_ranked_by_averageness():
    unrankedlist = [(lang.average_score, lang) for lang in Language.objects.conlangs().all()]
    unranked = {}
    for short in shortlist:
        unranked.setdefault(short[0], []).append(short[1])
    order = reversed(sorted(unranked.keys()))
    i = 1
    ranked = {}
    for key in order:
        ranked[i] = unranked[key]
        i += len(unranked[key])
    return sorted(tuple(ranked.items()))

def vocab_size():
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
    natlangs = Language.natlangs.all()
    users = Profile.objects.filter(user__is_active=True, is_visible=True)
    lfs = LanguageFeature.objects.all()

    user100 = User.objects.get(id=139)
    user150 = User.objects.get(id=200)
    lang100 = conlangs.get(id=154)
    lang150 = conlangs.get(id=271)

    num_features = features.count()
    num_conlangs = conlangs.count()
    num_natlangs = natlangs.count()
    num_langs = num_conlangs + num_natlangs
    num_users = users.count()
    num_lfs = lfs.count()
    num_greetings = Language.objects.conlangs().exclude(greeting__isnull=True).count()
    num_backgrounds = Language.objects.conlangs().exclude(background__isnull=True).exclude(background='').count()
    num_translations = Translation.objects.count();
    num_countries = users.filter(country__isnull=False).count()
    num_lurkers = len(get_all_lurkers())

    most_average = conlangs.exclude(num_features=0).order_by('-average_score', '-num_features')
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
            'lang100': lang100,
            'user150': user150,
            'lang150': lang150}
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

