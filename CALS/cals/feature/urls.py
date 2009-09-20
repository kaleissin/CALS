from django.conf.urls.defaults import *
from django.contrib.auth.models import User

from tagging.models import Tag
from voting.views import vote_on_object

from cals.models import Feature, FeatureValue, Category

feature_list_dict = {
        'queryset': Category.active_objects.filter(feature__active=True).distinct().order_by('id'),
        'template_name': 'cals/feature_list.html', 
        'extra_context': { 'me': 'feature' },
}

suggested_features_dict = {
        'queryset': Category.objects.filter(feature__active=False).distinct().order_by('id'),
        'template_name': 'cals/suggested_feature_list.html', 
        'extra_context': { 'me': 'feature' },
}

# feature_detail_dict = {
#         'queryset': Feature.objects.all().select_related(),
#         'extra_context': { 'me': 'feature' },
# }

feature_description = {
        'queryset': Feature.objects.active(),
        'template_name': 'cals/feature_description.html', 
        'extra_context': { 'me': 'feature' },
}

urlpatterns = patterns('django.views.generic',
        (r'^$',                             'simple.redirect_to', {'url': '/feature/p1/'}),
        (r'^p(?P<page>[0-9]+)/$',           'list_detail.object_list', feature_list_dict),
        (r'^suggested/$',                   'list_detail.object_list', suggested_features_dict),
        (r'^(?P<object_id>[0-9]+)/description/$', 'list_detail.object_detail', feature_description),
        #(r'^(?P<object_id>[0-9]+)/$',       'list_detail.object_detail', feature_detail_dict),
)

urlpatterns += patterns('cals.views',
        (r'^(?P<objects>[+0-9]+)/$',        'compare_feature'), 
        (r'^(?P<object_id>[0-9]+)/$',       'show_feature'),
        (r'^(?P<object_id>[0-9]+)/description/change$', 'change_description'),
        (r'^suggested/new$',                  'add_feature'),
        (r'^suggested/(?P<object_id>[0-9]+)/$', 'show_suggested_feature'),
        (r'^suggested/(?P<object_id>[0-9]+)/change$', 'change_feature'),
)

## voting
vote_on_feature_dict = {
        'model': Feature,
        'post_vote_redirect': '/feature/suggested/',
        'allow_xmlhttprequest': True,
        'extra_context': { 'me': 'feature'},
}

urlpatterns += patterns('',
        (r'^suggested/(?P<object_id>[0-9]+)/(?P<direction>up|down|clear)vote/?$', vote_on_object, vote_on_feature_dict),
)