from datetime import date

from django import forms
from django.dispatch import receiver
from django.contrib.auth.decorators import login_required
from django.contrib import messages

from verification.views import AbstractClaimView, ClaimOnPostUrlView
from verification.signals import key_claimed

from nano.badge.models import Badge

from .settings import MEETUPS

__all__ = [
    'meetup_direct_activate',
    'meetup_activate',
]

class KeyForm(forms.Form):
    key = forms.CharField(max_length=5, required=True)

class MeetupMixin(object):

    def expired_on(self):
        until = MEETUPS[self.keygroup].get('until', None)
        if until:
            expired_on = date(*(int(piece) for piece in until.split('-')))
            return expired_on
        return None

    def dispatch(self, request, *args, **kwargs):
        """Get KeyGroup from context"""
        self.keygroup = self.kwargs['group']
        return super(MeetupMixin, self).dispatch(request, *args, **kwargs)

    def get_template_names(self):
        if self.expired_on() is None:
            names = [
                'meetups/%s/' % self.keygroup,
                'meetups/',
            ]
            return [name + self.template_name_suffix for name in names]
        else:
            return 'meetups/expired.html'

    def get_context_data(self, **kwargs):
        context = super(MeetupMixin, self).get_context_data(**kwargs)
        context['expired_on'] = self.expired_on()
        return context

    def get_badge(self):
        badge_dict = MEETUPS[self.keygroup]['badge']
        badge = Badge.objects.get(name=badge_dict['name'])
        return badge

    def form_valid(self, form):
        nextpage = super(MeetupMixin, self).form_valid(form)
        messages.success(self.request,
            """Tadaa! If your name isn't in the list of awardees
            below, wait a while then reload. If still not there, it'll
            turn up sometime in the next 24 hours, when all badges are
            recalculated."""
        )
        return nextpage

    def get_success_url(self):
        return '/badge/%i/' % self.get_badge().pk

class DirectActivateMeetupKeyView(MeetupMixin, ClaimOnPostUrlView):
    template_name_suffix = 'claim_verify.html'
meetup_direct_activate = login_required(DirectActivateMeetupKeyView.as_view())

class ActivateMeetupKeyView(MeetupMixin, AbstractClaimView):
    template_name_suffix = 'claim_key.html'
    form_class = KeyForm
meetup_activate = login_required(ActivateMeetupKeyView.as_view())

# -- signals

@receiver(key_claimed)
def user_claimed_key(sender, **kwargs):
    claimant = kwargs['claimant']
    group = kwargs['group']
    if group.name in MEETUPS.keys():
        badge_dict = MEETUPS[group.name]['badge']
        badge = Badge.objects.get(name=badge_dict['name'])
        try:
            claimant.badges.add(badge)
        except:
            pass
