__all__ = [
        'show_people_map',
        'list_people',
        'show_profile',
        'change_profile', 
        'auth_login',
]

from pprint import pformat
from datetime import datetime

import logging
_LOG = logging.getLogger(__name__)
_LOG.info(__name__)

from actstream import action as streamaction

from django.contrib import auth, messages #.authenticate, auth.login
from django.contrib.auth.decorators import login_required
from django.contrib.auth.models import User
from django.http import HttpResponseRedirect, HttpResponseNotFound
from django.shortcuts import get_object_or_404, render
from django.views.generic.list_detail import object_list
from django.utils.encoding import smart_unicode
from django.db.models import Count

from cals.people.models import Profile
from cals.language.models import Language

from cals.models import asciify, slugify
from cals.forms import UserForm, ProfileForm

from translations.models import TranslationExercise

from nano.tools import render_page
from nano.privmsg.models import PM

class CALSError(Exception):
    pass

class CALSUserExistsError(CALSError):
    pass

def _get_profile(*args, **kwargs):
    return get_object_or_404(User, id=kwargs.get('object_id', None))

def show_people_map(request, *args, **kwargs):
    people = User.objects.filter(is_active=True)

def all_people_map(request, *args, **kwargs):
    people = User.objects.filter(is_active=True)

def list_people(request, template_name='cals/profile_list.html', *args, **kwargs):
    extra_context = {'me': 'people'}
    if 'prolificness' in request.GET:
        extra_context['prolificness'] = True
        queryset = User.objects.filter(profile__is_lurker=False).annotate(m=Count('manages'), e=Count('edits')).order_by('-m', '-e')
    else:
        queryset = Profile.objects.filter(is_lurker=False, is_visible=True).order_by('display_name')
    lurk_count = Profile.objects.filter(is_lurker=True, is_visible=True).count()
    extra_context['lurk_count'] = lurk_count
    return object_list(request, queryset=queryset, template_name=template_name,
            extra_context=extra_context, **kwargs)

def show_profile(request, *args, **kwargs):
    me = u'people'
    user = _get_profile(*args, **kwargs)
    profile = None
    whereami = request.META.get('PATH_INFO', None)
    try:
        profile = user.get_profile()
    except Profile.DoesNotExist:
        return HttpResponseNotFound()

    social_connections = []
    social_unconnected = []
    social = {
            u'twitter': {
                    u'link': u'http://twitter.com/account/redirect_by_id?id=%s',
                    u'icon': u'img/bird_blue_16.png',
                    u'provider': u'twitter',
            },
            u'github': {
                    u'link': u'https://github.com/%s',
                    u'icon': u'img/blacktocat-16.png',
                    u'provider': u'github',
            }
    }
    unsocial = social.keys()

    pms, pms_archived, pms_sent = (), (), ()

    seen = None

    looking_in_the_mirror = request.user == user
    if looking_in_the_mirror:
        seen = profile.seen_profile

        # social
        for sa in user.social_auth.all():
            provider = sa.provider
            if provider not in social:
                continue
            out = social[provider]
            out[u'connection'] = sa
            social_connections.append(out)
            unsocial.pop(provider, None)
        for us in unsocial:
            social_unconnected.append(social[us])
    
        # privmsg
        pms = PM.objects.received(user)
        pms_archived = PM.objects.archived(user)
        pms_sent = PM.objects.sent(user)

    data = {'object': user, 
            'profile': profile, 
            'me': me, 
            'seen': seen,

            'private': looking_in_the_mirror,

            'pms': pms,
            'pms_archived': pms_archived,
            'pms_sent': pms_sent,

            'social_connections': social_connections,
            'potential_social_connections': social_unconnected,
            
            'whereami': whereami,
            }
    return render_page(request, 'profile_detail.html', data)

@login_required
def change_profile(request, *args, **kwargs):
    me = 'people'
    user = _get_profile(*args, **kwargs)
    if user != request.user:
        return HttpResponseNotFound()
    profile = None
    try:
        profile = user.get_profile()
    except Profile.DoesNotExist:
        return HttpResponseNotFound()

    _LOG.info('User: %s', user)
    _LOG.info('Profile: %s', profile)
    uform = UserForm(instance=user)
    pform = ProfileForm(instance=profile)
    if request.method == 'POST':
        _LOG.debug('POST %s', request.POST)
        uform = UserForm(data=request.POST, instance=user)
        pform = ProfileForm(data=request.POST, instance=profile)
        if uform.is_valid() and pform.is_valid():
            _LOG.debug('Saving form')
            user = uform.save()
            profile = pform.save()
            _LOG.debug('Form saved')
            _LOG.debug('Country:', profile.country)
            return HttpResponseRedirect('/people/%i' % user.id)
    data = {'uform': uform,
            'pform': pform, 
            'me': me}
    return render_page(request, 'profile_form.html', data)

def check_for_ipv6(request, profile):
    if ':' in request.META.get('REMOTE_ADDR'):
        if not profile.seen_ipv6:
            profile.seen_ipv6 = datetime.now()
            messages.success(request, "Welcome, oh fellow user of IPv6! A badge is on the way.")
            profile.save()
    else:
        messages.success(request, 'Welcome!')

def auth_login(request, *args, **kwargs):
    me = 'people'
    nextfield = 'next'

    nexthop = request.REQUEST.get(nextfield, '/')
    if request.method == 'POST':
        # 1
        if not request.user.is_authenticated():
            username = asciify(smart_unicode(request.POST[u'username'], errors='ignore').strip())
            password = request.POST['password'].strip()
            # 2
            if username and password:
                _LOG.debug('Form valid')
                try:
                    user = User.objects.get(username=username)
                    profile = user.get_profile()
                except User.DoesNotExist:
                    try:
                        userslug = slugify(username)
                        profile = Profile.objects.get(slug=userslug)
                        user = profile.user
                    except Profile.DoesNotExist:
                        error = "User '%s' does not exist! Typo?" % username
                        messages.error(request, error)
                        _LOG.warn(error)
                except Profile.DoesNotExist:
                    error = "User %s is incomplete, lacks profile" % username
                    messages.error(request, error)
                    _LOG.warn(error)
                user = auth.authenticate(username=user.username, password=password)
                _LOG.info("User: %s", pformat(user))
                if user is not None:
                    auth.login(request, user)

                    check_for_ipv6(request, profile)

                else:
                    _LOG.warn("Invalid user for some reason")
                    error = "Couldn't log you in: Your username and/or password does not match with what is stored here."
                    messages.error(request, error)
                _LOG.info('Redirecting back to %s', nexthop)
                return HttpResponseRedirect(nexthop)
            # /2
        else:
            messages.info('You are already logged in')
            nexthop = request.user.get_profile().get_absolute_url()
            return HttpResponseRedirect(nexthop)
        # /1
    data = {'me': me, nextfield: nexthop}
    return render(request, 'login.html', data)
