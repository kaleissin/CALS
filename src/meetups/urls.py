from __future__ import absolute_import
from __future__ import unicode_literals

from django.conf.urls import *
from . import views

MEETUP_RE = '^(?P<group>[-a-z0-9]{1,32})/'

urlpatterns = [
    url(MEETUP_RE + '$', views.meetup_activate, name='meetup-activate'),
    url(MEETUP_RE + '(?P<key>[a-z0-9]{5})/$', views.meetup_direct_activate, name='meetup-direct_activate'),
]
