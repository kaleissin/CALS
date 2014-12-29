# -*- coding: utf-8 -*-
# vim: set fileencoding=utf-8 :

from datetime import datetime
from random import choice
from math import modf, floor, ceil
import os.path

from django import template
from django.contrib.auth import get_user_model
from django.contrib.sessions.models import Session
from django.conf import settings
from django.core.cache import cache
from django.utils.encoding import smart_str, force_unicode
from django.utils.safestring import mark_safe

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

_img_src = os.path.join(STATIC_URL, 'img') + '/'
_wals_img_src = _img_src + 'WALS.png'
_wals_img = '<img src="%s" alt="WALS" />' % _wals_img_src
_wals_path = 'http://wals.info'
_wals_description = '<sup class="wals"><a href="%s/chapter/%%i" target="_blank">WALS</a></sup>' % _wals_path
_wals_feature = '<sup class="wals"><a href="%s/feature/%%i" target="_blank">WALS</a><sup>' % _wals_path

def _get_display_name(user):
    """Given an id (int), a user-object or a user-name, returns
    preferred name to display and user-object.""" 
    try:
        dispay_name = user.profile.display_name.strip()
        return dispay_name, user
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
                raise template.TemplateSyntaxError, 'wrong argument type: %s' % type(user)
        # implicit fallback: User()
        display_name = user.profile.display_name.strip()
        return display_name, user
    except:
        raise

#def _make_userlink(user):
def _make_userlink(user, icon=False):
    """Makes a link to a user-profile with the preferred form of the
    name."""
    if icon:
        display = icon
    else:
        display, _ = _get_display_name(user)
    return u'<a href="/people/%i/">%s</a>' % (user.id, display) 

def _make_langlink(lang, internal=False):
    """Makes a link to a language"""
    langname = lang.name
    if internal:
        langname = lang.get_name()
    return u'<a href="/language/%s/">%s</a>' % (lang.slug, langname) 

def fetch_lf_description(language, feature, value):
    lf =LanguageFeature.objects.get(language=language, feature=feature, value=value)
    return lf.description

@register.simple_tag
def show_language_tags(language):
    # django-tagging among others
    if type(language.tags) == type(u''):
        return language.tags
    # django-taggit among others
    if getattr(language.tags, '__module__', False):
        return u', '.join(unicode(tag) for tag in language.tags.all())
    return u''

@register.simple_tag
def cals_tags_status(verbose=False):
    successmsg = u'cals_tags loaded successfully'
    _LOG.info(successmsg)
    if verbose:
        return successmsg
    return u''

@register.simple_tag
def currently_logged_in():
    now = datetime.now()
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
    return u','.join(out)

@register.simple_tag
def graphline(barsize):
    string = u'<img src="%simg/gradient.png" width="%%i" height="16" />' % STATIC_URL
    return string % (int(barsize) * 10)

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
        return u''
    chart = pygal.Bar()
    chart.disable_xml_declaration = True
    chart.add('', values)
    return chart.render()
    return u'<img src="%s" />' % chart.get_url()

@register.simple_tag
def show_lang(lang):
    return _make_langlink(lang)

@register.simple_tag
def wals(feature):
    try:
        int(feature)
    except ValueError:
        raise template.TemplateSyntaxError, u'must be integer'
    if feature <= MWF:
        return _wals_description % feature
    return ''

@register.simple_tag
def walsfeature(feature):
    try:
        int(feature)
    except ValueError:
        raise template.TemplateSyntaxError, u'must be integer'
    if feature <= MWF:
        return _wals_description % feature
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
    badges = show_badges(user)
    if badges:
        badges = u' ' + badges
    return _make_userlink(user) + badges

def _make_greet_link(greeting, objstring=''):
    "Greeting is a string or a Translation object"

    langlink = None
    try:
        # string!
        greetstring = greeting + u''
    except TypeError: # Translation!
        langlink = u'<a href="/language/%s/">%%s</a>'
        try:
            greetstring = greeting.translation.strip()
            langlink = langlink % greeting.language.slug
        except AttributeError: # Language!
            greetstring = get_greeting_of_lang(greeting)
            langlink = langlink % greeting.slug
    _LOG.info('1 ' + greetstring)
    if not u'$' in greetstring:
        greetstring = greetstring + u' $'
    greetstring = greetstring.split(u'$', 1)
    _LOG.info('2 ' + str( greetstring))
    if langlink:
        greetstring = [langlink % greetbit if greetbit else u'' for greetbit in greetstring]
    _LOG.info('3 ' + str( greetstring))
    _LOG.info('4 ' + objstring.join(greetstring))
    return objstring.join(greetstring)

def get_greeting_of_lang(lang):
    greeting_trans = Translation.objects.filter(language=lang, exercise__id=1)
    greeting = lang.greeting.strip()
    if not (greeting_trans or greeting):
        return 'Hello, %s!' % ahref_to_object
    if not greeting:
        greeting = greeting_trans.order_by('?')[0]
    return greeting

def make_greet_link(lang, ahref_to_object):
    greeting = get_greeting_of_lang(lang)
    if not greeting:
        return 'Hello, %s!' % ahref_to_object
    _link = u'<a href="/language/%%(slug)s/">%%(%s)s</a>'
    _link1 = _link % u'greeting'
    _link_front = _link % u'front'
    _link_back = _link % u'back'
    _langlink1 = u'%s&nbsp;%%(objectlink)s!' % _link1
    _langlink2 = u'%s%%(objectlink)s%s' % (_link_front, _link_back)
    langd = {'slug': lang.slug, 
            'greeting': greeting,
            'objectlink': ahref_to_object}
    if u'$' in langd['greeting']:
        front, back = langd['greeting'].split('$', 1)
        langd['front'] = front
        langd['back'] = back
        greeting = _langlink2 % langd
    else:
        greeting = _langlink1 % langd
    return greeting

def greet_link(lang, ahref_to_object):
    return make_greet_link(lang, ahref_to_object)

def greet(user, lang):
    return greet_link(lang, _make_userlink(user))

@register.simple_tag
def greetings(user):
    greetings = cache.get('greetings')
    if not greetings:
        greetings = [greeting for greeting in Translation.objects.filter(exercise__id=1, translation__isnull=False)]
        cache.set('greetings', greetings, 60**2)
    tran = choice(tuple(greetings))
    greeting = _make_greet_link(tran, _make_userlink(user))
    return greeting

@register.simple_tag
def greet_user_in_lang(user, lang):
    return greet(user, lang)

@register.simple_tag
def greet_lang_in_lang(lang):
    return _make_greet_link(lang, _make_langlink(lang, internal=True))

def latest_modified_languages(num_lang):
    try:
        num_lang = int(num_lang)
        langs = Language.objects.order_by('-last_modified')[:num_lang]
        return u'<ul>%s</ul>' % [_make_langlink(lang) for lang in langs]
    except ValueError:
        raise template.TemplateSyntaxError, 'must be integer'
    return ''

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
            raise template.TemplateSyntaxError, "Error in {% restructuredtext %} filter: The Python docutils library isn't installed."
        return force_unicode(value)
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
    imgstring = u'(%%s <img class="icon" src="%s%s" alt="PMs:" />) '
    icon = u'mail_generic.png'
    if count:
        imgstring = imgstring % (_img_src, icon)
        return _make_userlink(user, imgstring % count)
    else:
        return u''

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
        string = obj + u''
    except TypeError:
        User = get_user_model()
        if isinstance(obj, User):
            string = obj.email or u'%s %s' % (obj.id, obj.date_joined)
        else:
            string = unicode(obj)

    url = "http://www.gravatar.com/avatar.php?"
    url += urllib.urlencode({ 'gravatar_id': hashlib.md5(string).hexdigest()+'.jpg', 's': str(size), 'd': fallback })
    return """<img src="%s" width="%s" height="%s" alt="" title="gravatar" class="gravatar" border="0" />""" % (url, size, size)

# --------------- Inclusion tags

register.inclusion_tag('come_back.html', takes_context=True)(come_back)

# --------------- Filters

register.filter(nbr)
register.filter(integer)
register.filter(fraction)
register.filter(partition)
register.filter(startswith)
register.filter(endswith)
