# Create your views here.
from pprint import pprint, pformat
import difflib

from cals import getLogger
LOG = getLogger('cals.tools')

from django.contrib.contenttypes.models import ContentType
from django.http import HttpResponseNotFound, HttpResponseForbidden
from django.shortcuts import render_to_response, get_object_or_404

from cals.models import *
from cals.forms import *

def get_languagefeature_descriptions(lang=None, feature=None, lf=None):
    assert (lang and feature) or lf
    if not lf:
        lf = get_object_or_404(LanguageFeature, language=lang, feature=feature)
    lf_type = ContentType.objects.get_for_model(lf)
    return Description.objects.filter(content_type=lf_type, object_id=lf.id).order_by('-last_modified')

def description_diff(oldest, newest, link_prefix):
    # should be template
    tableformat = u"""
    <table class="diff" id="difflib_chg_%(prefix)s_top">
        <colgroup span="3"></colgroup> <colgroup span="3"></colgroup>
        %(header_row)s
        <tbody>
        %(data_rows)s
        </tbody>
    </table>"""

    def make_link_piece(obj, piece):
        if obj:
            return '%s=%s' % (piece, obj.id)
        return u''

    url = u"""<a href="%s">%s</a>"""
    def get_next_prev_links(prevobj, nextobj, direction):
        if prevobj != nextobj:
            prev = make_link_piece(prevobj, 'oldid')
            next = make_link_piece(nextobj, 'newid')
            if next and prev:
                link = '%s%s&%s' % (link_prefix, prev, next)
                return url % (link, direction)
        return u''

    differ = difflib.HtmlDiff(wrapcolumn=80)
    differ._table_template = tableformat

    # should be template
    strf = u"""Revision as of %s<br />\n%s<br />\n%s %s"""
    old_prev_url = get_next_prev_links(oldest.prev_version(),
            newest, 'Previous')
    old_next_url = get_next_prev_links(oldest.next_version(),
            newest, 'Next')
    new_prev_url = get_next_prev_links(oldest,
            newest.prev_version(), 'Previous')
    new_next_url = get_next_prev_links(oldest,
            newest.next_version(), 'Next')
    return differ.make_table(
            oldest.freetext.split('\n'),
            newest.freetext.split('\n'),
            strf % (oldest.last_modified, oldest.last_modified_by, old_prev_url, old_next_url),
            strf % (newest.last_modified, newest.last_modified_by, new_prev_url, new_next_url),
            )

