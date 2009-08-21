# -*- coding: utf-8 -*-
# vim: set fileencoding=utf-8 :

from datetime import datetime
from random import choice
from math import modf, floor, ceil

from django import template
from django.contrib.auth.models import User
from django.contrib.sessions.models import Session
from django.conf import settings
from django.core.cache import cache

from pygooglechart import StackedVerticalBarChart, Axis

from nano.tools import getLogger, grouper
from nano.privmsg.models import PM
LOG = getLogger('cals.templatetags')

from cals.models import Language, Feature, Profile
from translation.models import Translation

MWF = Feature.MAX_WALS_FEATURE

MEDIA_URL = ''
if settings.MEDIA_URL:
    MEDIA_URL = settings.MEDIA_URL

register = template.Library()

_img_src = 'http://media.aldebaaran.uninett.no/CALS/img/'
_wals_img_src = _img_src + 'WALS.png'
_wals_img = '<img src="%s" alt="WALS" />' % _wals_img_src
_wals_path = 'http://wals.info/feature'
_wals_description = '<sup class="wals"><a href="%s/description/%%i" target="_blank">WALS</a></sup>' % _wals_path
_wals_feature = '<sup class="wals"><a href="%s/%%i" target="_blank">WALS</a><sup>' % _wals_path

def _get_display_name(user):
    """Given an id (int) or a user-object, returns preferred name to
    display and user-object.""" 
    if type(user) == type(User()):
        display_name = user.get_profile().display_name.strip()
    elif type(user) == type(Profile()):
        display_name = user.display_name.strip()
    elif type(user) == type(5):
        user = User.objects.get(id=int(user))
        display_name = user.get_profile().display_name.strip()
    else:
        raise TemplateSyntaxError, 'wrong argument type'
    return display_name, user

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
    users = Profile.objects.filter(user__id__in=uids).order_by('display_name')
    out = []
    for user in users:
        out.append(_make_userlink(user.user))
    return u','.join(out)

@register.simple_tag
def graphline(barsize):
    string = u'<img src="%simg/background.jpg" width="%%i" height="16" />' % MEDIA_URL
    return string % (int(barsize) * 10)

@register.simple_tag
def feature_graph(feature):
    values = []
    max_count = 0
    for value in feature.values.all():
        count = value.languagefeature_set.count()
        values.append(count)
        if count > max_count:
            max_count = count
    num_values = len(values)
    if not num_values or max_count == 0:
        return u''
    chart = StackedVerticalBarChart((num_values+1)*15, 100, y_range=(0, max_count))
    chart.set_bar_width(10)
    chart.add_data(values)
    chart.set_axis_labels(Axis.BOTTOM, map(str, xrange(1, num_values+1)))
    chart.set_axis_labels(Axis.LEFT, ['0', '', '', '', str(int(max_count))])
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
    if type(user) == type(Profile()):
        user = user.user
    elif type(user) == type(5):
        user = User.objects.get(id=user)
    return _make_userlink(user)

def make_greet_link(lang, ahref_to_object, greeting_trans=None):
    if not greeting_trans:
        return 'Hello, %s!' % ahref_to_object
    else:
        if not lang.greeting.strip():
            return 'Hello, %s!' % ahref_to_object
    _link = u'<a href="/language/%%(slug)s/">%%(%s)s</a>'
    _link1 = _link % u'greeting'
    _link_front = _link % u'front'
    _link_back = _link % u'back'
    _langlink1 = u'%s&nbsp;%%(objectlink)s!' % _link1
    _langlink2 = u'%s%%(objectlink)s%s' % (_link_front, _link_back)
    langd = {'slug': lang.slug, 
            'greeting': lang.greeting,
            'objectlink': ahref_to_object}
    if '$' in langd['greeting']:
        front, back = langd['greeting'].split('$', 1)
        langd['front'] = front
        langd['back'] = back
        greeting = _langlink2 % langd
    else:
        greeting = _langlink1 % langd
    return greeting

def greet_link(lang, ahref_to_object):
    greeting_trans = Translation.objects.filter(language=lang, exercise__id=1)
    return make_greet_link(lang, ahref_to_object, greeting_trans)

def greet(user, lang):
    return greet_link(lang, _make_userlink(user))

@register.simple_tag
def greetings(user):
    trans = cache.get('greeting')
    if not trans:
        trans = [trans for trans in Translation.objects.filter(exercise__id=1, translation__isnull=False)]
        cache.set('greeting', trans, 60*10)
    tran = choice(tuple(trans))
    greeting = greet(user, tran.language)
    return greeting

@register.simple_tag
def greet_user_in_lang(user, lang):
    return greet(user, lang)

@register.simple_tag
def greet_lang_in_lang(lang):
    return greet_link(lang, _make_langlink(lang, internal=True))

def latest_modified_languages(num_lang):
    try:
        num_lang = int(num_lang)
        langs = Language.objects.order_by('-last_modified')[:num_lang]
        return u'<ul>%s</ul>' % [_make_langlink(lang) for lang in langs]
    except ValueError:
        raise template.TemplateSyntaxError, 'must be integer'
    return ''

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

# --------------- Filters

@register.filter
def integer(text):
    _, integer = modf(float(text))
    return str(int(integer))
integer.is_safe = True

@register.filter
def fraction(text, arg=1):
    arg = int(arg)
    fraction, _ = modf(float(text))
    integer, fraction = str(fraction).split('.', 1)
    lf = len(fraction)
    fraction = fraction[:arg]
    if arg > lf:
        fraction = u'%s%s' % (fraction, '0'*(arg-lf))
    return fraction
fraction.is_safe = True

@register.filter
def nbr(text):
    pieces = text.split()
    text = u'\xa0'.join(pieces)
    return text.encode('utf8')
nbr.is_safe = True

@register.filter
def partition(iterable, cols=4):
    try:
        cols = int(cols)
    except (ValueError, TypeError):
        return None
    the_tuple = tuple(iterable)
    maxrows = int(ceil(len(the_tuple)/float(cols)))
    columns = grouper(maxrows, the_tuple)
    return zip(*tuple(columns))
