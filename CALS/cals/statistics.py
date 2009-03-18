# Create your views here.
from pprint import pprint, pformat
from random import choice, sample
import time
import unicodedata
import string
import sys
sys.stderr = sys.stdout

from cals import getLogger
LOG = getLogger('cals.statistics')

from django.contrib.contenttypes.models import ContentType
from django.db import connection
from django.http import HttpResponseNotFound, HttpResponseForbidden
from django.shortcuts import render_to_response, get_object_or_404

from pygooglechart import StackedVerticalBarChart, Axis, SimpleLineChart

from cals.models import *
from cals.forms import *
from translation.models import Translation

def language_alphabetic_letters(num = 10):
    top_letters = """SELECT 
    substr(upper(name), 1, 1) AS char, 
    count(substr(upper(name), 1, 1)) 
    FROM cals_language GROUP BY char ORDER BY char, count DESC
    """

    num_langs = Language.objects.count()
    cursor = connection.cursor()
    cursor.execute(top_letters)
    max_count = 0
    rows = []
    for row in cursor.fetchall():
        count = row[1]
        rows.append({'char': row[0], 'count': count, 'percentage':
            row[1]/float(num_langs)*100})
        if count > max_count:
            max_count = count
    num_letters = len(rows)
    cursor.close()
    return {'letters':rows}

def language_first_letters(num = 10):
    top_letters = """SELECT 
    substr(upper(name), 1, 1) AS char, 
    count(substr(upper(name), 1, 1)) 
    FROM cals_language GROUP BY char ORDER BY count DESC, char
    """

    num_langs = Language.objects.count()
    cursor = connection.cursor()
    cursor.execute(top_letters)
    max_count = 0
    rows = []
    for row in cursor.fetchall():
        count = row[1]
        rows.append({'char': row[0], 'count': count, 'percentage':
            row[1]/float(num_langs)*100})
        if count > max_count:
            max_count = count
    num_letters = len(rows)
    cursor.close()
    return {'letters':rows}

def compare_value_sets(values1, values2):
    v1 = set(values1)
    v2 = set(values2)
    num_f = Feature.objects.count()
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
    features = Feature.objects.all().order_by('id')
    comparison = [(None,) + tuple(langs)]
    num_features = tuple(['Number of features'] + [lang.num_features for lang in langs])
    LOG.info('2: compare_languages: %s %s' % (same, different))
    LOG.info('3: num_features %s' % `num_features`)
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
    LOG.info('4: a %s b %s c %s d %s' % (a, b, c, d))
    return comparison

def country_most_common():
    count_countries = """SELECT country_id, count(country_id) 
    FROM "cals_profile" 
    WHERE country_id IS NOT NULL 
    GROUP BY country_id
    ORDER BY count DESC"""

    cursor = connection.cursor()
    cursor.execute(count_countries)
    return [{'country': Country.objects.get(iso=country[0]), 'count': country[1]} 
            for country in cursor.fetchall()]

def feature_usage(feature_order=False, max_count=None, limit=0):
    feature_usage = """SELECT fv.*, count(lf.id) AS languages
    FROM "cals_featurevalue" AS fv 
    LEFT JOIN "cals_languagefeature" AS lf ON lf.value_id = fv.id
    %s 
    GROUP BY fv.id, fv.feature_id, fv.name, fv.position 
    %s
    %s
    """

    where_unused = 'WHERE lf.id IS NULL '
    having_count = 'HAVING count(lf.id) = %i '
    order_feature = 'ORDER BY fv.feature_id, fv.position ' 
    order_languages = 'ORDER BY languages DESC '

    where = ''
    having = ''
    if max_count is not None:
        if max_count == 0:
            where = where_unused
        elif max_count > 0:
            having = having_count % max_count
    else:
        where = ''
    if feature_order:
        order = order_feature
    else:
        order = order_languages
    if limit:
        feature_usage += 'LIMIT '+str(limit)

    num_langs = Language.objects.count()
    cursor = connection.cursor()
    cursor.execute(feature_usage % (where, having, order))
    rows = [{'value': FeatureValue.objects.get(id=row[0]),
            'feature': Feature.objects.get(id=row[1]), 
            'languages': row[4],
            'percentage': str(row[4]/float(num_langs)*100) }
            for row in cursor.fetchall()]
    cursor.close()
    return rows

def language_most_average_internal():
    features = {}
    for f in feature_usage():
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

def get_averageness_for_lang(lang, scale=100, max_values=None, average_features=None):
    if not max_values:
        max_values = language_most_average_internal()
    if not average_features:
        average_features = [v['value'].id for k, v in max_values.items()]
    values = [lf.value.id for lf in lang.features.all()]
    if not values: 
        return 0
    frequency = compare_value_sets(average_features, values)
    return frequency

def set_averageness_for_langs():
    max_values = language_most_average_internal()
    average_features = [v['value'].id for k, v in max_values.items()]
    for l in Language.objects.all():
        num = l.features.count()
        if not num: continue
        freq = get_averageness_for_lang(l, max_values=max_values, average_features=average_features)
        if freq == None: continue
        l.num_avg_features = freq
        l.set_average_score()
        l.save(solo=False)

def joined():
    "Statistics over which days/weeks/months are most visited/update etc."
    joined = User.objects.dates('date_joined', 'day')
    login = User.objects.dates('last_login', 'day')
    created = Language.objects.dates('created', 'day')
    last_modified = Language.objects.dates('last_modified', 'day')
    LOG.info('Joined: %s' % joined[:5])

def languages_ranked_by_averageness():
    unrankedlist = [(lang.average_score, lang) for lang in Language.objects.all()]
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

    avg_max_min = """SELECT AVG(vocabulary_size),
    MAX(vocabulary_size),
    MIN(vocabulary_size)
    FROM cals_language
    WHERE vocabulary_size IS NOT NULL AND id != 80"""

    cursor.execute(avg_max_min)
    for row in cursor.fetchall():
        avg, max, min = row
        break

    curve = """SELECT vocabulary_size 
    FROM cals_language
    WHERE vocabulary_size IS NOT NULL AND id != 80 
    ORDER BY vocabulary_size DESC"""

    cursor.execute(curve)
    rows = [row[0] for row in cursor.fetchall()]

    chart = SimpleLineChart(400, 200, y_range=(0, max))
    chart.add_data(rows)
    chart.set_axis_labels(Axis.LEFT, ['0', '2000', '4000',
    '6000', '8000', '10000', '12000', '14000', str(int(max))])
    chart_url = chart.get_url()
#     median = """SELECT vocabulary_size as median FROM
#         (SELECT l1.id, l1.vocabulary_size, COUNT(l1.vocabulary_size) AS rank
#         FROM cals_language AS l1, cals_language AS l2
#         WHERE l1.vocabulary_size < l2.vocabulary_size
#             OR (l1.vocabulary_size = l2.vocabulary_size AND l1.id <= l2.id)
#         GROUP BY l1.id, l1.vocabulary_size
#         ORDER BY l1.vocabulary_size DESC) AS l3
#     WHERE rank = (SELECT (COUNT(*)+1 DIV 2 FROM cals_language)"""
#     
#     cursor.execute(median)
#     for row in cursor.fetchall():
#         median = row
#         break
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

def generate_global_stats():
    "Used by the statistics-view"
    features = Feature.objects.all()
    fvs = FeatureValue.objects.all() #value_counts()
    langs = Language.objects.all()
    users = Profile.objects.filter(is_visible=True)
    lfs = LanguageFeature.objects.all()

    user100 = User.objects.get(id=139)
    lang100 = Language.objects.get(id=154)

    num_features = features.count()
    num_langs = langs.count()
    num_users = users.count()
    num_lfs = lfs.count()
    num_greetings = Language.objects.exclude(greeting__isnull=True).count()
    num_backgrounds = Language.objects.exclude(background__isnull=True).exclude(background='').count()
    num_translations = Translation.objects.count();
    num_countries = users.filter(country__isnull=False).count()

    most_average = langs.exclude(num_features=0).order_by('-average_score', '-num_features')
    lma = most_average.count()
    least_average = tuple(most_average)[-10:]
    most_average = most_average[:20]

    features_mu = feature_usage(limit=20)
    not_used = feature_usage(feature_order=True, max_count=0)

    countries = country_most_common()

    skeleton_langs = langs.filter(num_features=0)

    data = {}
    data['milestones'] = { 
            'user100': user100, 
            'lang100': lang100}
    data['features'] = { 
            'number': num_features,
            'percentage_wals': str(142/float(num_features)*100),
            'most_used': features_mu,
            #'least_used': tuple(reversed(features_mu))[:20],
            'not_used': not_used,
            'num_not_used': len(not_used),
            }
    data['langs'] = { 
            'number': num_langs, 
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
            }
    return data

