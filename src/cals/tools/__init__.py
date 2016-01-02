# -*- coding: utf8 -*-

from __future__ import unicode_literals
from __future__ import absolute_import

import unicodedata
import re
import difflib
from unidecode import unidecode

import logging
from six.moves import zip
_LOG = logging.getLogger(__name__)

from django.contrib.contenttypes.models import ContentType
from django.db import connection
from django.http import HttpResponseNotFound, HttpResponseForbidden
from django.shortcuts import get_object_or_404
from django.template import Template, Context, loader

class LANGTYPES(object):
    CONLANG = 1
    NATLANG = 2
    ALL = CONLANG + NATLANG

    types = (ALL, NATLANG, CONLANG)

def uslugify(value):
    "Strip diacritics then slugify"
    value = unidecode(value.strip()).lower()
    value = '-'.join(re.sub('[^\w\s-]', '', value).split())
    return value

def asciify(string):
    return unidecode(string)

def next_id(model):
    # postgres only
    table_name, pk_name = model._meta.db_table, model._meta.pk.column
    fetch_id = """SELECT nextval('\"%s_%s_seq\"')""" % (table_name, pk_name)
    cursor = connection.cursor()
    #cursor.execute(fetch_id, (table_name, pk_name))
    cursor.execute(fetch_id)
    return cursor.fetchone()[0]

def string_statistics(strings):
    """Counts how many times each string occurs and calculates percentages"""
    num_strings = float(len(strings))
    outdict = {}
    for string in strings:
        outdict[string] = outdict.get(string, 0) + 1 
    return [(string, count, count/num_strings*100) for (string, count) in outdict.items()]

class BetterHtmlDiff(difflib.HtmlDiff):
    _table_template = """
    <table class="diff" id="difflib_chg_%(prefix)s_top">
        <colgroup span="3"></colgroup> <colgroup span="3"></colgroup>
        %(header_row)s
        <tbody>
        %(data_rows)s
        </tbody>
    </table>"""

    def _format_line(self, side, flag, linenum, text):
        """Returns HTML markup of "from" / "to" text lines

        side -- 0 or 1 indicating "from" or "to" text
        flag -- indicates if difference on line
        linenum -- line number (used for line number column)
        text -- line text to be marked up
        """
        try:
            linenum = '%d' % linenum
            id = ' id="%s%s"' % (self._prefix[side], linenum)
        except TypeError:
            # handle blank lines where linenum is '>' or ''
            id = ''
        # replace those things that would get confused with HTML symbols
        text = text.replace("&", "&amp;").replace(">", "&gt;").replace("<", "&lt;")

        # make space non-breakable so they don't get compressed or line wrapped
        #text = text.replace(' ','&nbsp;').rstrip()

        text_class = 'class="diff_text%s"'
        changed = ' changed%s' % side if '\0' in text else ' unchanged'
        text_class = text_class % changed

        #return '<td class="diff_header"%s>%s</td><td %s nowrap="nowrap">%s</td>' \
        return '<td class="diff_header"%s>%s</td><td %s>%s</td>' \
               % (id, linenum, text_class, text)

def description_diff(oldest, newest, link_prefix, may_revert=False, may_remove=False):

    def make_link_piece(obj, piece):
        if obj:
            return '%s=%s' % (piece, obj.id)
        return ''

    url = """<a href="%s">%s</a>"""
    def get_next_prev_links(prevobj, nextobj, direction):
        if prevobj != nextobj:
            prev = make_link_piece(prevobj, 'oldid')
            next = make_link_piece(nextobj, 'newid')
            if next and prev:
                link = '%s%s&%s' % (link_prefix, prev, next)
                return url % (link, direction)
        return ''

    diff_header_template = loader.get_template('cals/diff_header.html')
    differ = BetterHtmlDiff()

    if may_revert:
        use_this_button = '<a href="../use?id=%i"><button>Use this</button></a>'
    else:
        use_this_button = ''

    if may_remove:
        remove_button = '<a href="./delete?id=%i"><button>Remove this</button></a>'
    else:
        remove_button = ''

    # prev header
    prev_use_this_button = use_this_button % oldest.id if may_revert else '' 
    prev_remove_button = remove_button % oldest.id if may_remove else ''
    prev_extra = prev_use_this_button + prev_remove_button
    old_prev_url = get_next_prev_links(oldest.prev_version(),
            newest, 'Previous')
    if not old_prev_url:
        old_prev_url = '<b>First</b>'
    else:
        old_prev_url = '← ' + old_prev_url
    old_next_url = get_next_prev_links(oldest.next_version(),
            newest, 'Next')
    if old_next_url:
        old_next_url += ' →'
    prev_version = Context({'prev_version': old_prev_url,
            'next_version': old_next_url,
            'extra': prev_extra,
            'last_modified': oldest.last_modified,
            'last_modified_by': oldest.last_modified_by })

    # next header
    next_extra = ''
    new_prev_url = get_next_prev_links(oldest,
            newest.prev_version(), 'Previous')
    if new_prev_url:
        new_prev_url = '← ' + new_prev_url
    new_next_url = get_next_prev_links(oldest,
            newest.next_version(), 'Next') + ' →'
    if newest.current:
        new_next_url = '<b>Current</b>'
    else:
        next_use_this_button = use_this_button % newest.id if may_revert else '' 
        next_remove_button = remove_button % newest.id if may_remove else ''
        next_extra = next_use_this_button + next_remove_button
        #new_extra = use_this_button % newest.id if use_this_button else u''
    
    next_version = Context({'prev_version': new_prev_url,
            'next_version': new_next_url,
            'extra': next_extra,
            'last_modified': newest.last_modified,
            'last_modified_by': newest.last_modified_by })

    return differ.make_table(
            oldest.freetext.split('\n'),
            newest.freetext.split('\n'),
            diff_header_template.render(prev_version),
            diff_header_template.render(next_version),
            )

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

