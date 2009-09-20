from django.conf.urls.defaults import *
from django.contrib.auth.models import User

from cals.models import Profile

# people
people_list_dict = {
        'queryset': Profile.objects.all().order_by('display_name'),
        'extra_context': { 'me': 'people' },
}

people_detail_dict = {
        'queryset': User.objects.all().select_related(),
        'extra_context': { 'me': 'people' },
}

# people
urlpatterns = patterns('django.views.generic',
        (r'^$',                              'simple.redirect_to', {'url': '/people/p1/'}),
        (r'^p(?P<page>[0-9]+)/$',            'list_detail.object_list', dict(people_list_dict)),
)

urlpatterns += patterns('cals.views',
        (r'^map$',                           'show_people_map'),
        (r'^(?P<object_id>[0-9]+)/$',        'show_profile'), 
        (r'^(?P<object_id>[0-9]+)/change$',  'change_profile'), 
        (r'^(?P<object_id>[0-9]+)/pm/',      include('nano.privmsg.urls')),
)
