from __future__ import unicode_literals
from __future__ import absolute_import

__all__ = [
        'show_people_map',
        'list_people',
        'show_profile',
        'change_profile', 
        'auth_login',
]

from pprint import pformat

import logging
_LOG = logging.getLogger(__name__)
_LOG.info(__name__)

from actstream import action as streamaction

from django.contrib import auth, messages #.authenticate, auth.login
from django.contrib.auth.decorators import login_required
from django.contrib.auth import get_user_model
from django.http import HttpResponseRedirect, HttpResponseNotFound, Http404
from django.shortcuts import get_object_or_404, render
from django.utils.encoding import smart_text
from django.utils.timezone import now as tznow
from django.db.models import Count
from django.views.generic import ListView, DetailView

from cals.people.models import Profile
from cals.language.models import Language

from cals.tools import asciify, uslugify
from cals.forms import UserForm, ProfileForm

from nano.privmsg.models import PM

SOCIAL = {
        'twitter': {
                'link': 'http://twitter.com/account/redirect_by_id?id=%s',
                'icon': 'img/bird_blue_16.png',
                'provider': 'twitter',
        },
        'github': {
                'link': 'https://github.com/%s',
                'icon': 'img/blacktocat-16.png',
                'provider': 'github',
        }
}


def get_user_model_w_related():
    return get_user_model().objects.prefetch_related('badges', 'profile')


class CALSError(Exception):
    pass

class CALSUserExistsError(CALSError):
    pass

def _get_profile(*args, **kwargs):
    return get_object_or_404(get_user_model(), id=kwargs.get('object_id', None))

def show_people_map(request, *args, **kwargs):
    people = get_user_model().objects.filter(is_active=True)

def all_people_map(request, *args, **kwargs):
    people = get_user_model().objects.filter(is_active=True)

class ListPeopleView(ListView):
    queryset = get_user_model_w_related().filter(profile__is_lurker=False, profile__is_visible=True)
    template_name = 'cals/profile_list.html'
    http_method_names = ['get', 'head', 'options', 'trace']

    def __init__(self, **kwargs):
        super(ListPeopleView, self).__init__(**kwargs)
        self.lurk_count = Profile.objects.filter(is_lurker=True, is_visible=True).count()
        self.prolificness = False

    def get(self, request, *args, **kwargs):
        if 'prolificness' in self.request.GET:
            self.prolificness = True
        return super(ListPeopleView, self).get(request, *args, **kwargs)

    def get_queryset(self):
        queryset = super(ListPeopleView, self).get_queryset()
        if self.prolificness:
            queryset = queryset.annotate(m=Count('manages'), e=Count('edits')).order_by('-m', '-e')
        else:
            queryset = queryset.order_by('profile__display_name')
        return queryset

    def get_context_data(self, **kwargs):
        context = super(ListPeopleView, self).get_context_data(**kwargs)
        context['me'] = 'people'
        context['prolificness'] = self.prolificness
        context['lurk_count'] = self.lurk_count
        return context
list_people = ListPeopleView.as_view()

class DetailPeopleView(DetailView):
    queryset = get_user_model_w_related()
    model = get_user_model()
    template_name = 'profile_detail.html'

    def get_object(self, queryset=None):
        obj = super(DetailPeopleView, self).get_object(queryset)
        try:
            profile = obj.profile
        except Profile.DoesNotExist:
            raise Http404("No user found matching the query")
        return obj

    def social(self):
        user = self.get_object()
        social_connections = []
        social_unconnected = []
        unsocial = set(SOCIAL.keys())

        # social
        for sa in user.social_auth.all():
            provider = sa.provider
            if provider not in SOCIAL:
                continue
            out = SOCIAL[provider]
            out['connection'] = sa
            social_connections.append(out)
            unsocial.discard(provider)
        for us in unsocial:
            social_unconnected.append(SOCIAL[us])

        return {
            'social_connections': social_connections,
            'potential_social_connections': social_unconnected,
        }

    def pms(self):
        user = self.get_object()
        return {
            'pms': PM.objects.received(user),
            'pms_archived': PM.objects.archived(user),
            'pms_sent': PM.objects.sent(user),
        }

    def get_context_data(self, **context):
        context = super(DetailPeopleView, self).get_context_data(**context)
        private = self.request.user == self.object
        seen = self.object.profile.seen_profile
        public_context = {
            'user': self.request.user,
            'me': 'people',
            'whereami': self.request.META.get('PATH_INFO', None),
            'seen': seen,
            'profile': self.object.profile,
            'private': private,
        }
        private_context = {}
        if private:
            private_context.update(self.pms())
            private_context.update(self.social())
        context.update(public_context)
        context.update(private_context)
        return context
show_profile = DetailPeopleView.as_view()

@login_required
def change_profile(request, *args, **kwargs):
    me = 'people'
    user = _get_profile(*args, **kwargs)
    if user != request.user:
        return HttpResponseNotFound()
    profile = None
    try:
        profile = user.profile
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
    return render(request, 'profile_form.html', data)

def check_for_ipv6(request, profile):
    if ':' in request.META.get('REMOTE_ADDR'):
        if not profile.seen_ipv6:
            profile.seen_ipv6 = tznow()
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
            username = asciify(smart_text(request.POST['username'], errors='ignore').strip())
            password = request.POST['password'].strip()
            # 2
            if username and password:
                _LOG.debug('Form valid')
                try:
                    user = get_user_model().objects.get(username=username)
                    profile = user.profile
                except get_user_model().DoesNotExist:
                    try:
                        userslug = uslugify(username)
                        profile = Profile.objects.get(slug=userslug)
                        user = profile.user
                    except Profile.DoesNotExist:
                        error = "User '%s' does not exist! Typo?" % username
                        messages.error(request, error)
                        _LOG.warn(error)
                        return HttpResponseRedirect(nexthop)
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
            messages.info(request, 'You are already logged in')
            nexthop = request.user.profile.get_absolute_url()
            return HttpResponseRedirect(nexthop)
        # /1
    data = {'me': me, nextfield: nexthop}
    return render(request, 'login.html', data)
