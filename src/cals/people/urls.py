from django.conf.urls import *
from django.views.generic.base import RedirectView

# people
urlpatterns = patterns('',
        (r'^$',                       RedirectView.as_view(url='/people/p1/')),
)

urlpatterns += patterns('cals.people.views',
        (r'^map$',                           'show_people_map'),
        (r'^(?P<object_id>[0-9]+)/$',        'show_profile'), 
        (r'^(?P<object_id>[0-9]+)/change$',  'change_profile'), 
        (r'^p(?P<page>[0-9]+)/$',            'list_people'),
        (r'^(?P<object_id>[0-9]+)/pm/',      include('nano.privmsg.urls')),
)

