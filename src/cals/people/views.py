__all__ = [
        'show_people_map',
        'list_people',
        'show_profile',
        'change_profile', 
        'auth_login'
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
from django.shortcuts import get_object_or_404
from django.views.generic.list_detail import object_list
from django.utils.encoding import smart_unicode
from django.db.models import Count

from cals.people.models import Profile
from cals.language.models import Language

from cals.models import asciify, slugify
from cals.forms import UserForm, ProfileForm

from translations.models import TranslationExercise

from nano.tools import render_page
from nano.blog.tools import get_nano_blog_entries
from nano.privmsg.models import PM

from tagtools import get_tagcloud_for_model

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
    me = 'people'
    user = _get_profile(*args, **kwargs)
    profile = None
    whereami = request.META.get('PATH_INFO', None)
    try:
        profile = user.get_profile()
    except Profile.DoesNotExist:
        return HttpResponseNotFound()

    social_links = {
            'twitter': 'http://twitter.com/account/redirect_by_id?id=%s',
            'github': 'https://github.com/%s'
    }
    social_unconnected = set(social_links.keys())

    looking_in_the_mirror = request.user == user

    seen = profile.seen_profile
    
    pms, pms_archived, pms_sent = (), (), ()
    social_connections = []
    if looking_in_the_mirror:
        pms = PM.objects.received(user)
        pms_archived = PM.objects.archived(user)
        pms_sent = PM.objects.sent(user)

        for sa in user.social_auth.all():
            out = {}
            provider = sa.provider
            social_unconnected.discard(provider)
            link = social_links[provider] 
            out['provider'] = provider
            out['link'] = link % sa.id
            out['connection'] = sa
            social_connections.append(out)
    
    data = {'object': user, 
            'profile': profile, 
            'me': me, 
            'seen': seen,

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

def auth_login(request, *args, **kwargs):
    _LOG.info('Starting auth_login')
    greeting = None
    nexthop = ''
    nextfield = u'next'
    langs = Language.objects.exclude(slug__startswith='testarossa')
    langs_newest = langs.order_by('-created')[:5]
    langs_modified = langs.order_by('-last_modified')[:5]
    people = User.objects.exclude(username='countach')
    people_recent = people.order_by('-date_joined')[:5]
    trans_ex_recent = TranslationExercise.objects.order_by('-added')[:5]
    if nextfield in request.REQUEST:
        nexthop = request.REQUEST[nextfield]
    if request.method == 'POST':
        _LOG.debug('request: %s', request.POST)

        # Login
        if not request.user.is_authenticated():
            username = asciify(smart_unicode(request.POST[u'username'], errors='ignore').strip())
            password = request.POST['password'].strip()
            if username and password:
                try:
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
                            _LOG.warn("User '%s' does not exist", username)
                            if nextfield in request.REQUEST:
                                _LOG.warn("Redirecting back to '%s' after failed login", request.POST[nextfield] or '[redirect missing]')
                                return HttpResponseRedirect(request.POST[nextfield])
                    except Profile.DoesNotExist:
                        error = "User %s is incomplete, lacks profile" % username
                        messages.error(request, error)
                        _LOG.warn(error)
                        if nextfield in request.REQUEST:
                            _LOG.warn("Redirecting back to '%s' after failed login", request.POST[nextfield] or '[redirect missing]')
                            return HttpResponseRedirect(request.POST[nextfield])
                    user = auth.authenticate(username=user.username, password=password)
                    _LOG.info("User: %s", pformat(user))
                    if user is not None:
                        auth.login(request, user)

                        # IPv6
                        if ':' in request.META.get('REMOTE_ADDR'):
                            profile.seen_ipv6 = datetime.now()
                            messages.success(request, "Welcome, oh fellow user of IPv6! A badge is on the way.")
                            profile.save()
                        else:
                            messages.success(request, 'Welcome!')

                    else:
                        _LOG.warn("Invalid user for some reason")
                        error = "Couldn't log you in: Your username and/or password does not match with what is stored here."
                        messages.error(request, error)
                except CALSUserExistsError, e:
                    error = "Couldn't sign you up: " + e
                    messages.error(request, error)
            if nextfield in request.REQUEST:
                _LOG.info('Redirecting back to %s', request.POST[nextfield])
                return HttpResponseRedirect(request.POST[nextfield])

    l_cloud = get_tagcloud_for_model(Language, steps=7, min_count=2)

    news, devel_news = get_nano_blog_entries()

    data = {'me': 'home', 
            'next': nexthop,
            'news': news,
            'devel_news': devel_news,
            'language_cloud': l_cloud,
            'langs_newest': langs_newest,
            'langs_modified': langs_modified,
            'trans_exs_newest': trans_ex_recent,
            'people': people_recent,}
    return render_page(request, 'index.html', data)

