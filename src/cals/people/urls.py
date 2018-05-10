from __future__ import absolute_import
from __future__ import unicode_literals

from django.conf.urls import *
from django.views.generic.base import RedirectView

from cals.people import views

# people
urlpatterns = [
        url(r'^$', RedirectView.as_view(url='/people/p1/', permanent=False)),
]

urlpatterns += [
        url(r'^map$',                           views.show_people_map),
        url(r'^(?P<pk>[0-9]+)/$',               views.show_profile, name='user_show'),
        url(r'^(?P<object_id>[0-9]+)/change$',  views.change_profile),
        url(r'^p(?P<page>[0-9]+)/$',            views.list_people),
        url(r'^(?P<object_id>[0-9]+)/pm/',      include('nano.privmsg.urls')),
]
