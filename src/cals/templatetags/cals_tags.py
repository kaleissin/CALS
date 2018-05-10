# -*- coding: utf-8 -*-
# vim: set fileencoding=utf-8 :

from __future__ import absolute_import
from __future__ import unicode_literals

from random import choice
from math import modf, floor, ceil
import os.path
from collections import OrderedDict

from django import template
from django.contrib.auth import get_user_model
from django.contrib.sessions.models import Session
from django.conf import settings
from django.core.cache import cache
from django.core.urlresolvers import reverse
from django.utils.encoding import force_text
from django.utils.safestring import mark_safe
from django.utils.timezone import now as tznow
from django.utils.html import escape, format_html

import pygal

from nano.tools import grouper
from nano.tools.templatetags.nano_tags import *
from nano.badge.templatetags.badge_tags import show_badges
from nano.privmsg.models import PM

import logging
_LOG = logging.getLogger(__name__)

from cals.language.models import Language
from cals.languagefeature.models import LanguageFeature
from cals.feature.models import Feature
from cals.people.models import Profile
from translations.models import Translation

from cals import markup_as_restructuredtext


MWF = Feature.MAX_WALS_FEATURE

STATIC_URL = ''
if settings.STATIC_URL:
    STATIC_URL = settings.STATIC_URL

register = template.Library()

_IMG_SRC = mark_safe(os.path.join(STATIC_URL, 'img') + '/')
_wals_img = '<img src="{}WALS.png" alt="WALS" />'.format(_IMG_SRC)
_WALS_PATH = 'http://wals.info'
_wals_description = '<sup class="wals"><a href="{}/chapter/%i" target="_blank">WALS</a></sup>'.format(_WALS_PATH)
_wals_feature = '<sup class="wals"><a href="{}/feature/%i" target="_blank">WALS</a><sup>'.format(_WALS_PATH)


def _get_display_name(user):
    """Given an id (int), a user-object or a user-name, returns
    preferred name to display and user-object."""
    try:
        dispay_name = user.profile.display_name.strip()
        return dispay_name
    except AttributeError:
        User = get_user_model()
        if type(user) == type(Profile()):
            user = user.user
        elif type(user) == type(5):
            user = User.objects.get(id=int(user))
        else:
            try:
                user = User.objects.get(username=str(user))
            except:
                raise template.TemplateSyntaxError('wrong argument type: {}'.format(type(user)))
        # implicit fallback: User()
        display_name = user.profile.display_name.strip()
        return display_name
    except:
        raise


def _make_userlink(user, content=None):
    """Makes a link to a user-profile with the preferred form of the
    name."""
    if not content:
        content = _get_display_name(user)
    userdata = user_dict(user, content=content)
    formatstring = '<a href="{url}">{content}</a>'
    if userdata['extra']:
        formatstring = '<a href="{url}" {extra}>{content}</a>'
    return format_html(formatstring, **userdata)


def _make_langlink(lang, internal=False):
    """Makes a link to a language"""
    langdata = lang_dict(lang, internal)
    return format_html('<a href="{url}">{content}</a>', **langdata)


def fetch_lf_description(language, feature, value):
    lf =LanguageFeature.objects.get(language=language, feature=feature, value=value)
    return lf.description


@register.simple_tag
def show_language_tags(language):
    # django-tagging among others
    if type(language.tags) == type(''):
        return language.tags
    # django-taggit among others
    if getattr(language.tags, '__module__', False):
        return ', '.join(str(tag) for tag in language.tags.all())
    return ''


@register.simple_tag
def cals_tags_status(verbose=False):
    successmsg = 'cals_tags loaded successfully'
    _LOG.info(successmsg)
    if verbose:
        return successmsg
    return ''


@register.simple_tag
def currently_logged_in():
    now = tznow()
    sessions = Session.objects.filter(expire_date__gt=now)
    uids = []
    for s in sessions:
        session = s.get_decoded()
        if not s: continue
        uid = session.get('_auth_user_id', None)
        if not uid: continue
        uids.append(uid)
    users = Profile.objects.filter(user__in=uids).order_by('display_name')
    out = []
    for user in users:
        out.append(_make_userlink(user.user))
    return ','.join(out)


@register.simple_tag
def graphline(barsize):
    string = '<img src="{}img/gradient.png" width="{}" height="16" />'
    return format_html(string, mark_safe(STATIC_URL), int(barsize) * 10)


@register.simple_tag
def feature_graph(feature, ltype):
    natlang = False
    if ltype == 'nat':
        natlang = True
    values = []
    max_count = 0
    for value in feature.values.all():
        count = value.languages.filter(language__natlang=natlang).count()
        values.append(count)
        if count > max_count:
            max_count = count
    num_values = len(values)
    if not num_values or max_count == 0:
        return ''
    chart = pygal.Bar()
    chart.disable_xml_declaration = True
    chart.add('', values)
    return chart.render()
    return '<img src="{}" />' % chart.get_url()


@register.simple_tag
def show_lang(lang):
    return _make_langlink(lang)


@register.simple_tag
def wals(feature):
    try:
        int(feature)
    except ValueError:
        raise template.TemplateSyntaxError('must be integer')
    if feature <= MWF:
        return mark_safe(_wals_description % feature)
    return ''


@register.simple_tag
def walsfeature(feature):
    try:
        int(feature)
    except ValueError:
        raise template.TemplateSyntaxError('must be integer')
    if feature <= MWF:
        return mark_safe(_wals_description % feature)
    return ''


@register.simple_tag
def showuser(user):
    if not user:
        return 'Anonymous'
    if type(user) == type(Profile()):
        user = user.user
    elif type(user) == type(5):
        User = get_user_model()
        user = User.objects.get(id=user)
    userlink = _make_userlink(user)
    badges = show_badges(user)
    if badges:
        badges = mark_safe('&#160;' + badges)
        return userlink + badges
    return userlink


def _make_greet_link(greeting, objstring=''):
    "Greeting is a string or a Translation object"

    greetstring, language = prepare_greeting(greeting)
    _LOG.info('1 ' + greetstring)
    greetpieces = greetstring.split('$', 1)
    if language:
        langurl = reverse('language_show', kwargs={'lang': language.slug})
        html = '<a href="{}">{}</a>'
        greetstring = [format_html(html, mark_safe(langurl), piece) if piece else '' for piece in greetpieces]
    _LOG.info('3 ' + str( greetstring))
    return objstring.join(greetstring)


def get_greeting_of_lang(lang, fallback='Hello, $!'):
    greeting_trans = Translation.objects.filter(language=lang, exercise__id=1)
    greeting = lang.greeting.strip()
    if not (greeting_trans or greeting):
        return fallback
    if greeting_trans and not greeting:
        return greeting_trans.order_by('?')[0]
    return greeting


@register.simple_tag
def greetings(user):
    greetings = cache.get('greetings')
    if not greetings:
        translations = Translation.objects.filter(
            language__visible=True,
            exercise__id=1,
            translation__isnull=False,
        )
        greetings = [greeting for greeting in translations]
        cache.set('greetings', greetings, 60**2)
    tran = choice(tuple(greetings))
    greeting = _make_greet_link(tran, _make_userlink(user))
    return mark_safe(greeting)


@register.simple_tag
def greet_user_in_lang(user, lang):
    return _make_greet_link(tran, _make_userlink(user))


@register.simple_tag
def greet_lang_in_lang(lang):
    return _make_greet_link(lang, _make_langlink(lang, internal=True))


def latest_modified_languages(num_lang):
    try:
        num_lang = int(num_lang)
        langs = Language.objects.order_by('-last_modified')[:num_lang]
        return '<ul>{}</ul>' % [_make_langlink(lang) for lang in langs]
    except ValueError:
        raise template.TemplateSyntaxError('must be integer')
    return ''


def prepare_greeting(greeting):
    """Fix a greeting missing a name placeholder

    greeting: string, Translation or Language. Fallback: 'Hello, $!'
    """
    fallback = 'Hello, $!'
    if isinstance(greeting, Translation):
        greetstring = greeting.translation.strip()
        language = greeting.language
    elif isinstance(greeting, Language):
        greetstring = get_greeting_of_lang(greeting, fallback)
        language = greeting
    else:
        greetstring = str(greeting).strip() or fallback
        language = None
    _LOG.info('Raw greeting:', greetstring, language)
    if not '$' in greetstring:
        greetstring = greetstring + ' $'
    _LOG.info('Formatted greeting:', greetstring)
    return (greetstring, language)


def linkify_dict(url, content, classes=(), id_=None, **kwargs):
    link_dict = OrderedDict(
        url=mark_safe(url), content=content, extra=None)
    if id_ or classes or kwargs:
        extra = OrderedDict()
        if id_:
            extra['id'] = id_
        if classes:
            extra['classes'] = ' '.join(classes)
        for k, v in sorted(kwargs.items()):
            extra[str(k)] = str(v)
        extra_string=' '.join('{}="{}"'.format(k, v) for k, v in extra.items())
        link_dict['extra'] = mark_safe(extra_string)
    return link_dict


def user_dict(user, classes=(), id_=None, **kwargs):
    url = reverse('user_show', kwargs={'pk': user.pk})
    content = kwargs.pop('content', _get_display_name(user))
    return linkify_dict(url, content, classes, id_, **kwargs)


def lang_dict(language, internal=False, classes=(), id_=None, **kwargs):
    url = mark_safe(reverse('language_show', kwargs={'lang': language.slug}))
    if internal:
        content = language.get_name()
    else:
        content = str(language)
    return linkify_dict(url, content, classes, id_, **kwargs)


def greet_dict(greeting, user, classes=(), id_=None, **kwargs):
    if isinstance(greeting, Translation):
        language = greeting.language
    elif isinstance(greeting, Language):
        language = greeting
        greeting = get_greeting_of_lang(lang)
        if not greeting:
            greeting = 'Hello, $!'
    url = reverse('language_show', kwargs={'lang': language.slug})
    content = format_greeting(greeting, user)
    return linkify_dict(url, content, classes, id_, **kwargs)


@register.inclusion_tag('cals/language/family_path.html')
def show_family_path(language):
    return {'language': language}


@register.inclusion_tag('statistics/firstletter_stats.html')
def firstletter_stats(letters):
    return {'letters': letters}


@register.filter()
def restructuredtext(value):
    try:
        import docutils
    except ImportError:
        if settings.DEBUG:
            raise template.TemplateSyntaxError("Error in {% restructuredtext %} filter: The Python docutils library isn't installed.")
        return force_text(value)
    else:
        return mark_safe(markup_as_restructuredtext(value))
restructuredtext.is_safe = True


@register.inclusion_tag('shareicon.html', takes_context=True)
def shareicon(context):
    return { 'STATIC_URL': context['STATIC_URL'] }
shareicon.is_safe = True


@register.inclusion_tag('shareicon_library.html', takes_context=True)
def load_shareicon_library(context):
    return { 'STATIC_URL': context['STATIC_URL'] }
load_shareicon_library.is_safe = True


# -------------- nano.pm


@register.simple_tag
def messages_for_user(user):
    count = PM.objects.received(user).count()
    imgstring = '({} <img class="icon" src="{}{}" alt="PMs:" />) '
    icon = mark_safe('mail_generic.png')
    if count:
        imgstring = format_html(imgstring, count, _IMG_SRC, icon)
        return _make_userlink(user, imgstring)
    else:
        return ''


# -------------- Move to nano


import urllib
try:
    import hashlib
except ImportError:
    import md5 as hashlib


@register.simple_tag
def gravatar(obj, size=32, fallback='identicon'):
    # TODO:
    # - Size in a setting
    # - Fallback in a setting
    # - Fallback different from those provided by gravatar

    try:
        int(size)
    except TypeError:
        size = 32

    try:
        string = obj + ''
    except TypeError:
        User = get_user_model()
        if isinstance(obj, User):
            string = obj.email or '{} {}' % (obj.id, obj.date_joined)
        else:
            string = str(obj)

    url = "http://www.gravatar.com/avatar.php?"
    data = {
        'gravatar_id': hashlib.md5(string.encode('utf8')).hexdigest()+'.jpg',
        's': str(size),
        'd': fallback,
    }
    url += urllib.parse.urlencode(data)
    html = '<img src="{}" width="{}" height="{}" alt="" title="gravatar" class="gravatar" border="0" />'.format(url, size, size)
    return mark_safe(html)


# --------------- Inclusion tags


register.inclusion_tag('come_back.html', takes_context=True)(come_back)


# --------------- Filters


register.filter(nbr)
register.filter(integer)
register.filter(fraction)
register.filter(partition)
register.filter(startswith)
register.filter(endswith)
