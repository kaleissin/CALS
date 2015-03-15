from django.conf.urls import *
from . import views

MEETUP_RE = '^(?P<group>[-a-z0-9])/'

urlpatterns = patterns('',
    url(MEETUP_RE + '$', views.meetup_activate, name='meetup-activate'),
    url(MEETUP_RE + '(?P<key>[a-z0-9]{5})/$', views.meetup_direct_activate, name='meetup-direct_activate'),
)
