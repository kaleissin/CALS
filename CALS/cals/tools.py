
# -*- coding: utf8 -*-

from pprint import pprint, pformat
import difflib

from cals import getLogger
LOG = getLogger('cals.tools')

from django.contrib.contenttypes.models import ContentType
from django.http import HttpResponseNotFound, HttpResponseForbidden
from django.shortcuts import render_to_response, get_object_or_404
from django.template import Template, Context, loader

from cals.models import *
from cals.forms import *

def get_languagefeature_descriptions(lang=None, feature=None, lf=None):
    assert (lang and feature) or lf
    if not lf:
        lf = get_object_or_404(LanguageFeature, language=lang, feature=feature)
    lf_type = ContentType.objects.get_for_model(lf)
    return Description.objects.filter(content_type=lf_type, object_id=lf.id).order_by('-last_modified')

class BetterHtmlDiff(difflib.HtmlDiff):
    _table_template = u"""
    <table class="diff" id="difflib_chg_%(prefix)s_top">
        <colgroup span="3"></colgroup> <colgroup span="3"></colgroup>
        %(header_row)s
        <tbody>
        %(data_rows)s
        </tbody>
    </table>"""

    def _format_line(self,side,flag,linenum,text):
        """Returns HTML markup of "from" / "to" text lines

        side -- 0 or 1 indicating "from" or "to" text
        flag -- indicates if difference on line
        linenum -- line number (used for line number column)
        text -- line text to be marked up
        """
        try:
            linenum = '%d' % linenum
            id = ' id="%s%s"' % (self._prefix[side],linenum)
        except TypeError:
            # handle blank lines where linenum is '>' or ''
            id = ''
        # replace those things that would get confused with HTML symbols
        text=text.replace("&","&amp;").replace(">","&gt;").replace("<","&lt;")

        # make space non-breakable so they don't get compressed or line wrapped
        #text = text.replace(' ','&nbsp;').rstrip()

        text_class = 'class="diff_text%s"'
        changed = ' changed%s' % side if '\0' in text else ' unchanged'
        text_class = text_class % changed

        #return '<td class="diff_header"%s>%s</td><td %s nowrap="nowrap">%s</td>' \
        return '<td class="diff_header"%s>%s</td><td %s>%s</td>' \
               % (id,linenum,text_class,text)

def description_diff(oldest, newest, link_prefix):

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

    diff_header_template = loader.get_template('cals/diff_header.html')
    differ = BetterHtmlDiff()

    # prev header
    old_prev_url = get_next_prev_links(oldest.prev_version(),
            newest, 'Previous')
    if not old_prev_url:
        old_prev_url = '<b>First</b>'
    else:
        old_prev_url = u'← ' + old_prev_url
    old_next_url = get_next_prev_links(oldest.next_version(),
            newest, 'Next') + u' →'
    prev_version = Context({'prev_version': old_prev_url,
            'next_version': old_next_url,
            'last_modified': oldest.last_modified,
            'last_modified_by': oldest.last_modified_by })

    new_prev_url = u'← ' + get_next_prev_links(oldest,
            newest.prev_version(), 'Previous')
    new_next_url = get_next_prev_links(oldest,
            newest.next_version(), 'Next') + u' →'
    if newest.current:
        new_next_url = '<b>Current</b>'

    next_version = Context({'prev_version': new_prev_url,
            'next_version': new_next_url,
            'last_modified': newest.last_modified,
            'last_modified_by': newest.last_modified_by })

    return differ.make_table(
            oldest.freetext.split('\n'),
            newest.freetext.split('\n'),
            diff_header_template.render(prev_version),
            diff_header_template.render(next_version),
            )
