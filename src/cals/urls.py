from django.conf.urls import *

from cals.feature.models import FeatureValue

# feature
urlpatterns = patterns('',
        (r'^feature/', include('cals.feature.urls')),
)

# language
urlpatterns += patterns('',
        (r'^language/', include('cals.language.urls')),
)

# people
urlpatterns += patterns('',
        (r'^people/', include('cals.people.urls')),
)

# statistics
urlpatterns += patterns('',
        (r'^statistics/', include('cals.statistics.urls')),
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
        (r'^value/(?P<object_id>[0-9]+)/$',         'show_featurevalue'),
)

# other
urlpatterns += patterns('cals.views',
        (r'^jrklist/$',                             'language_jrklist'),

        #(r'^search([?](?P<action>[a-z]+))?$',                              'search'),
        #(r'^search([?]q=.*)?$',                     'search'),

        (r'^test/$',                                'test'),

        (r'^$',                                     'home'),
)

