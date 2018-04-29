from __future__ import absolute_import
from __future__ import unicode_literals

from django.conf.urls import *

from cals import views as cviews
from cals.feature import views as fviews
from cals.feature.models import FeatureValue

# feature
urlpatterns = [
        url(r'^feature/', include('cals.feature.urls')),
]

# language
urlpatterns += [
        url(r'^language/', include('cals.language.urls')),
]

# people
urlpatterns += [
        url(r'^people/', include('cals.people.urls')),
]

# statistics
urlpatterns += [
        url(r'^statistics/', include('cals.statistics.urls')),
]

# value
value_list_dict = {
        'queryset': FeatureValue.objects.all().order_by('feature'),
        'extra_context': { 'me': 'feature' },
}

value_detail_dict = {
        'queryset': FeatureValue.objects.all().order_by('id'),
        'extra_context': { 'me': 'feature' },
}

urlpatterns += [
        url(r'^value/(?P<object_id>[0-9]+)/$',         fviews.show_featurevalue),
]

# other
urlpatterns += [
        url(r'^jrklist/$',                             cviews.language_jrklist),

        #url(r'^search([?](?P<action>[a-z]+))?$',                              views.search),
        #url(r'^search([?]q=.*)?$',                     cviews.search),

        url(r'^test/$',                                cviews.test),

        url(r'^$',                                     cviews.home),
]
