from __future__ import absolute_import
from __future__ import unicode_literals

from django.conf.urls import *

from cals.feature.models import FeatureValue

# feature
urlpatterns = patterns('',
        url(r'^feature/', include('cals.feature.urls')),
)

# language
urlpatterns += patterns('',
        url(r'^language/', include('cals.language.urls')),
)

# people
urlpatterns += patterns('',
        url(r'^people/', include('cals.people.urls')),
)

# statistics
urlpatterns += patterns('',
        url(r'^statistics/', include('cals.statistics.urls')),
)

# value
value_list_dict = {
        'queryset': FeatureValue.objects.all().order_by('feature'),
        'extra_context': { 'me': 'feature' },
}

value_detail_dict = {
        'queryset': FeatureValue.objects.all().order_by('id'),
        'extra_context': { 'me': 'feature' },
}

urlpatterns += patterns('cals.feature.views',
        url(r'^value/(?P<object_id>[0-9]+)/$',         'show_featurevalue'),
)

# other
urlpatterns += patterns('cals.views',
        url(r'^jrklist/$',                             'language_jrklist'),

        #url(r'^search([?](?P<action>[a-z]+))?$',                              'search'),
        #url(r'^search([?]q=.*)?$',                     'search'),

        url(r'^test/$',                                'test'),

        url(r'^$',                                     'home'),
)

