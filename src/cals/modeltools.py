# -*- coding: utf8 -*-

from __future__ import absolute_import
from __future__ import unicode_literals

import unicodedata
from pprint import pformat
import difflib

import logging
from six.moves import zip
_LOG = logging.getLogger(__name__)

from django.contrib.contenttypes.models import ContentType
from django.db import connection
from django.db.models import Q, Count, Avg, Max, Min
from django.http import HttpResponseNotFound, HttpResponseForbidden
from django.shortcuts import get_object_or_404
from django.template import Template, Context, loader

from cals.feature.models import Feature, FeatureValue
from cals.tools.models import Description
from cals.language.models import Language
from cals.languagefeature.models import LanguageFeature

class LANGTYPES(object):
    CONLANG = 1
    NATLANG = 2
    ALL = CONLANG + NATLANG

    types = (ALL, NATLANG, CONLANG)

def compare_value_sets(values1, values2):
    v1 = set(values1)
    v2 = set(values2)
    num_f = Feature.objects.active().count()
    return len(v1 & v2)

def get_languagefeature_descriptions(lang=None, feature=None, lf=None):
    assert (lang and feature) or lf
    if not lf:
        lf = get_object_or_404(LanguageFeature, language=lang, feature=feature)
    lf_type = ContentType.objects.get_for_model(lf)
    return Description.objects.filter(content_type=lf_type, object_id=lf.id).order_by('-last_modified')

def get_langs(langtype=LANGTYPES.ALL):
    assert langtype in LANGTYPES.types
    if langtype == LANGTYPES.CONLANG:
        langs = Language.objects.conlangs()
    if langtype == LANGTYPES.NATLANG:
        langs = Language.objects.natlangs()
    else:
        langs = Language.objects.all()
    return langs

def firstletter_langnames(langtype=LANGTYPES.ALL):
    assert langtype in LANGTYPES.types
    langs = get_langs(langtype=langtype)
    return [l.name.upper().strip()[0] for l in langs.only('name').all()]

def string_statistics(strings):
    """Counts how many times each string occurs and calculates percentages"""
    num_strings = float(len(strings))
    outdict = {}
    for string in strings:
        outdict[string] = outdict.get(string, 0) + 1 
    return [(string, count, count/num_strings*100) for (string, count) in outdict.items()]

def make_lang_firstletter_stats(langtype=LANGTYPES.CONLANG):
    assert langtype in LANGTYPES.types
    letters = firstletter_langnames(langtype=langtype)
    return string_statistics(letters)

def language_alphabetic_letters(num=10, langtype=LANGTYPES.CONLANG):
    letters = make_lang_firstletter_stats(langtype)

    letters = sorted((l, c, p) for l, c, p in letters)
    return {'letters': [{'char': l, 'count': c, 'percentage': p} for l, c, p in letters]}

def language_first_letters(num=10, langtype=LANGTYPES.CONLANG):
    letters = make_lang_firstletter_stats(langtype)

    #dsd
    letters = reversed(sorted([(c, l, p) for l, c, p in letters]))
    return {'letters': [{'char': l, 'count': c, 'percentage': p} for c, l, p in letters]}


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

    features = Feature.objects.active().order_by('id')
    comparison = [(None,) + tuple(langs)]
    num_features = tuple(['Number of features'] + [lang.num_features for lang in langs])
    _LOG.info('2: compare_languages: %s %s' % (same, different))
    _LOG.info('3: num_features %s' % str(num_features))
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

def feature_usage(langtype=LANGTYPES.ALL, limit=0):
    assert langtype in LANGTYPES.types

    fvs = FeatureValue.objects.filter(feature__active=True)
    ls = Language.objects
    if langtype == LANGTYPES.NATLANG:
        ls = ls.natlangs()
        fvs = fvs.filter(languages__language__natlang=True)
    elif langtype == LANGTYPES.CONLANG:
        ls = ls.conlangs()
        fvs = fvs.filter(languages__language__natlang=False)

    num_langs = ls.count()
    fvs = fvs.annotate(count=Count('languages')).order_by('-count')

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

def get_averageness_for_lang(lang, scale=100, max_values=None, average_features=None, langtype=LANGTYPES.ALL):
    assert langtype in LANGTYPES.types
    if not max_values:
        max_values = language_most_average_internal(langtype=langtype)
    if not average_features:
        average_features = [v['value'].id for _, v in max_values.items()]
    values = [lf.value.id for lf in lang.features.all()]
    if not values: 
        return 0
    frequency = compare_value_sets(average_features, values)
    return frequency

def set_averageness_for_langs(langtype=LANGTYPES.ALL):
    assert langtype in LANGTYPES.types
    max_values = language_most_average_internal(langtype=langtype)
    average_features = [v['value'].id for _, v in max_values.items()]
    for l in get_langs(langtype=langtype):
        num = l.features.count()
        if not num: 
            continue
        freq = get_averageness_for_lang(l, max_values=max_values, average_features=average_features, langtype=langtype)
        if freq == None: 
            continue
        l.num_avg_features = freq
        l.num_features = num
        l.set_average_score()
        l.save(solo=False)

def languages_ranked_by_averageness():
    unrankedlist = [(lang.average_score, lang) for lang in Language.objects.conlangs().all()]
    unranked = {}
    for short in unrankedlist:
        unranked.setdefault(short[0], []).append(short[1])
    order = reversed(sorted(unranked.keys()))
    i = 1
    ranked = {}
    for key in order:
        ranked[i] = unranked[key]
        i += len(unranked[key])
    return sorted(tuple(ranked.items()))

