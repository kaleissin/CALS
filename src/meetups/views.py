from __future__ import absolute_import
from __future__ import unicode_literals

from datetime import date

from django import forms
from django.dispatch import receiver
from django.contrib.auth.decorators import login_required
from django.contrib import messages

from verification.views import AbstractClaimView, ClaimOnPostUrlView
from verification.signals import key_claimed

from nano.badge.models import Badge

from .models import Meetup

__all__ = [
    'meetup_direct_activate',
    'meetup_activate',
]

class KeyForm(forms.Form):
    key = forms.CharField(max_length=5, required=True)

class MeetupMixin(object):

    def dispatch(self, request, *args, **kwargs):
        """Get KeyGroup from context"""
        self.keygroup = self.kwargs['group']
        self.meetup = Meetup.objects.get(keygroup__name=self.keygroup)
        self.badge = self.meetup.badge
        return super(MeetupMixin, self).dispatch(request, *args, **kwargs)

    def get_template_names(self):
        valid_until = self.meetup.valid_until
        today = date.today()
        if not valid_until or today <= valid_until:
            names = [
                'meetups/%s/' % self.keygroup,
                'meetups/',
            ]
            return [name + self.template_name_suffix for name in names]
        else:
            return 'meetups/expired.html'

    def get_context_data(self, **kwargs):
        context = super(MeetupMixin, self).get_context_data(**kwargs)
        context['expired_on'] = self.meetup.valid_until
        return context

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
        return '/badge/%i/' % self.badge.pk

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
    try:
        meetup = Meetup.objects.get(keygroup__name=group.name)
    except Meetup.DoesNotExist:
        pass
    else:
        badge = meetup.badge
        try:
            claimant.badges.add(badge)
        except:
            pass
