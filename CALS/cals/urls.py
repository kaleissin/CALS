from django.conf.urls.defaults import *
from django.contrib.auth.models import User

from tagging.models import Tag

from cals.models import Language, Feature, FeatureValue, Category, Profile

# language_detail_dict = {
#         'queryset': Language.objects.all().select_related(),
#         'extra_context': { 'me': 'language' },
# }

feature_list_dict = {
        'queryset': Category.active_objects.all().order_by('id'),
        'template_name': 'cals/feature_list.html', 
        'extra_context': { 'me': 'feature' },
}

suggested_features_dict = {
        'queryset': Category.objects.all().order_by('id'),
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

people_list_dict = {
        'queryset': Profile.objects.all().order_by('display_name'),
        'extra_context': { 'me': 'people' },
}

people_detail_dict = {
        'queryset': User.objects.all().select_related(),
        'extra_context': { 'me': 'people' },
}

value_list_dict = {
        'queryset': FeatureValue.objects.all().order_by('feature'),
        'extra_context': { 'me': 'feature' },
}

value_detail_dict = {
        'queryset': FeatureValue.objects.all().order_by('id'),
        'extra_context': { 'me': 'feature' },
}

tags_language_dict = {
        'queryset_or_model': Language,
        'template_name': 'cals/language_tag_list.html',
#        'extra_context': { 'me': 'language' },
}
taglist_language_dict = {
        'queryset': Tag.objects.all(), #usage_for_model(Language, counts=True),
#        'template_name': 'tagging/tag_list.html',
        'extra_context': { 'me': 'language' },
}

language_by_year = {
        'queryset': Language.objects.all().order_by('-last_modified'),
        'date_field': 'last_modified',
        'make_object_list': True,
        'extra_context': { 'me': 'language' },
        }

language_by_date = {
        'queryset': Language.objects.all().order_by('-last_modified'),
        'date_field': 'last_modified',
        'extra_context': { 'me': 'language' },
        }

urlpatterns = patterns('tagging.views',
        (r'^language/tag/(?P<tag>[- \w\d]+)/$', 'tagged_object_list', tags_language_dict),
)

urlpatterns += patterns('django.views.generic',
        (r'^language/tag/$',                        'list_detail.object_list', taglist_language_dict),
# #        (r'^language/latest/$', 'date_based.archive_index', language_by_date),
# #        (r'^language/(?P<year>\d{4})/$',            'date_based.archive_year', language_by_year),
        #(r'^language/(?P<year>\d{4})/w(?P<week>[a-z]{3})/$', 'date_based.archive_week', language_by_week),
)

urlpatterns += patterns('django.views.generic',
        (r'^feature/$',                             'simple.redirect_to', {'url': '/feature/p1/'}),
        (r'^feature/p(?P<page>[0-9]+)/$',           'list_detail.object_list', dict(feature_list_dict)),
     #   (r'^feature/suggest/$',                     'list_detail.object_list', dict(suggested_features_dict)),
        #(r'^feature/(?P<object_id>[0-9]+)/$',       'list_detail.object_detail', dict(feature_detail_dict)),
)

urlpatterns += patterns('django.views.generic',
        (r'^people/$',                              'simple.redirect_to', {'url': '/people/p1/'}),
        (r'^people/p(?P<page>[0-9]+)/$',            'list_detail.object_list', dict(people_list_dict)),
        (r'^value/(?P<object_id>[0-9]+)/$',         'list_detail.object_detail', dict(value_detail_dict)),
)

urlpatterns += patterns('cals.views',
        (r'^language/([?](?P<action>[a-z]+))?$', 'list_languages'),
        (r'^jrklist/$',                             'language_jrklist'),
        (r'^language/p(?P<page>[0-9]+)/$',          'language_list'),
        (r'^language/new$',                         'create_language'),
        (r'^language/(?P<lang>[-\w]+)/$',           'show_language'), 
#XXX: versioning is no good
        (r'^language/(?P<lang>[-\w]+)/feature/(?P<object_id>[0-9]+)/$', 'show_languagefeature'), 
        (r'^language/(?P<lang>[-\w]+)/feature/(?P<object_id>[0-9]+)/change$', 'describe_languagefeature'), 
        (r'^language/(?P<lang>[-\w]+)/change$',     'change_language'),
        (r'^language/(?P<slugs>[-+\w]+)/(?P<opt>[^/]*?)/?$',      'compare_language'), 
)


urlpatterns += patterns('cals.views',
        (r'^people/map$',                           'show_people_map'),
        (r'^people/(?P<object_id>[0-9]+)/$',        'show_profile'), 
        (r'^people/(?P<object_id>[0-9]+)/change$',  'change_profile'), 
        (r'^people/(?P<object_id>[0-9]+)/pm/',      include('nano.privmsg.urls')),
     #   (r'^feature/suggest/new$',                  'change_or_add_feature'),
        (r'^feature/(?P<objects>[+0-9]+)/$',        'compare_feature'), 
        (r'^feature/(?P<object_id>[0-9]+)/$',       'show_feature'),
        (r'^feature/(?P<object_id>[0-9]+)/description/change$', 'change_description'),

        (r'^statistics/$',                          'show_stats'),

        (r'^test/$',                                'test'),

        (r'^$',                                     'auth_login'),
)

urlpatterns += patterns('django.views.generic',
        (r'^feature/(?P<object_id>[0-9]+)/description/$', 'list_detail.object_detail', dict(feature_description)),
)
