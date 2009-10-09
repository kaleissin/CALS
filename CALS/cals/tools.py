
# -*- coding: utf8 -*-

from pprint import pprint, pformat
import difflib

import logging
_LOG = logging.getLogger(__name__)

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

def description_diff(oldest, newest, link_prefix, may_revert=False, may_remove=False):

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

    if may_revert:
        use_this_button = u'<a href="../use?id=%i"><button>Use this</button></a>'
    else:
        use_this_button = u''

    if may_remove:
        remove_button = u'<a href="./delete?id=%i"><button>Remove this</button></a>'
    else:
        remove_button = u''

    # prev header
    prev_use_this_button = use_this_button % oldest.id if may_revert else u'' 
    prev_remove_button = remove_button % oldest.id if may_remove else u''
    prev_extra = prev_use_this_button + prev_remove_button
    old_prev_url = get_next_prev_links(oldest.prev_version(),
            newest, 'Previous')
    if not old_prev_url:
        old_prev_url = '<b>First</b>'
    else:
        old_prev_url = u'← ' + old_prev_url
    old_next_url = get_next_prev_links(oldest.next_version(),
            newest, 'Next')
    if old_next_url:
        old_next_url += u' →'
    prev_version = Context({'prev_version': old_prev_url,
            'next_version': old_next_url,
            'extra': prev_extra,
            'last_modified': oldest.last_modified,
            'last_modified_by': oldest.last_modified_by })

    # next header
    new_extra = ''
    new_prev_url = get_next_prev_links(oldest,
            newest.prev_version(), 'Previous')
    if new_prev_url:
        new_prev_url = u'← ' + new_prev_url
    new_next_url = get_next_prev_links(oldest,
            newest.next_version(), 'Next') + u' →'
    if newest.current:
        new_next_url = '<b>Current</b>'
    else:
        next_use_this_button = use_this_button % newest.id if may_revert else u'' 
        next_remove_button = remove_button % newest.id if may_remove else u''
        next_extra = next_use_this_button + next_remove_button
        new_extra = use_this_button % newest.id if use_this_button else u''
    
    next_version = Context({'prev_version': new_prev_url,
            'next_version': new_next_url,
            'extra': new_extra,
            'last_modified': newest.last_modified,
            'last_modified_by': newest.last_modified_by })

    return differ.make_table(
            oldest.freetext.split('\n'),
            newest.freetext.split('\n'),
            diff_header_template.render(prev_version),
            diff_header_template.render(next_version),
            )

