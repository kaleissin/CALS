from django.conf.urls.defaults import *
from django.contrib.auth.models import User
from django.views.generic import RedirectView

from voting.views import vote_on_object

from cals.feature.models import Feature, FeatureValue, Category

FEATURE_RE = r'(?P<object_id>[0-9]+)/'
FEATURE_HISTORY_RE = r'^' + FEATURE_RE + r'history/'
SUGGESTED_RE = r'^suggested/'
SUGGESTED_FEATURE_RE = SUGGESTED_RE + FEATURE_RE

suggested_features_dict = {
        'queryset': Category.objects.filter(feature__active=False).distinct().order_by('id'),
        'template_name': 'cals/suggested_feature_list.html', 
        'extra_context': { 'me': 'feature' },
}

urlpatterns = patterns('',
        (r'^$',                            RedirectView.as_view(**{'url': '/feature/p1/'})),
#         (r'^suggested/$',                   'list_detail.object_list', suggested_features_dict),
)

urlpatterns += patterns('cals.feature.views',
        (r'^p(?P<page>[0-9]+)/$',          'list_feature'),
        (r'^'+FEATURE_RE+r'$',             'show_feature'),
        (r'^(?P<objects>[+0-9]+)/$',       'compare_feature'), 
        (r'^'+FEATURE_RE+r'change$',       'change_feature_description'),
        (r'^'+FEATURE_RE+r'use$',          'revert_feature_description'),
        (FEATURE_HISTORY_RE+r'$',          'show_feature_history'),
        (FEATURE_HISTORY_RE+r'compare$',   'compare_feature_history'),
#         (SUGGESTED_RE+r'new$',             'add_feature'),
#         (SUGGESTED_FEATURE_RE+r'$',        'show_suggested_feature'),
#         (SUGGESTED_FEATURE_RE+r'change$',  'change_feature'),
)

# ## voting
# vote_on_feature_dict = {
#         'model': Feature,
#         'post_vote_redirect': '/feature/suggested/',
#         'allow_xmlhttprequest': True,
#         'extra_context': { 'me': 'feature'},
# }
# 
# urlpatterns += patterns('',
#         (SUGGESTED_FEATURE_RE+'(?P<direction>up|down|clear)vote/?$', vote_on_object, vote_on_feature_dict),
#         (SUGGESTED_FEATURE_RE+r'comment/', include('nano.comments.urls', app_name='feature'), 
#                 {'model': Feature, 
#                 'object_arg': 'object_id',
#                 'extra_context': {'me': 'feature'}}),
# )
