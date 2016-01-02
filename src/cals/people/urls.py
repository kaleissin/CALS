from __future__ import absolute_import
from __future__ import unicode_literals
from django.conf.urls import *
from django.views.generic.base import RedirectView

# people
urlpatterns = patterns('',
        url(r'^$', RedirectView.as_view(url='/people/p1/', permanent=False)),
)

urlpatterns += patterns('cals.people.views',
        url(r'^map$',                           'show_people_map'),
        url(r'^(?P<pk>[0-9]+)/$',               'show_profile'),
        url(r'^(?P<object_id>[0-9]+)/change$',  'change_profile'),
        url(r'^p(?P<page>[0-9]+)/$',            'list_people'),
        url(r'^(?P<object_id>[0-9]+)/pm/',      include('nano.privmsg.urls')),
)

