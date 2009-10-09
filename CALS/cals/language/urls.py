from django.conf.urls.defaults import *
from django.contrib.auth.models import User

from tagging.models import Tag

from cals.models import Language, Feature, FeatureValue, Category, Profile

## tagging
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

urlpatterns = patterns('tagging.views',
        (r'^tag/(?P<tag>[- \w\d]+)/$', 'tagged_object_list', tags_language_dict),
)

urlpatterns += patterns('django.views.generic',
        (r'^tag/$',                        'list_detail.object_list', taglist_language_dict),
# #        (r'^latest/$', 'date_based.archive_index', language_by_date),
# #        (r'^(?P<year>\d{4})/$',            'date_based.archive_year', language_by_year),
        #(r'^(?P<year>\d{4})/w(?P<week>[a-z]{3})/$', 'date_based.archive_week', language_by_week),
)

# language
# language_detail_dict = {
#         'queryset': Language.objects.all().select_related(),
#         'extra_context': { 'me': 'language' },
# }

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

urlpatterns += patterns('cals.views',
        (r'^([?](?P<action>[a-z]+))?$', 'list_languages'),
        (r'^jrklist/$',                             'language_jrklist'),
        (r'^p(?P<page>[0-9]+)/$',          'language_list'),
        (r'^new$',                         'create_language'),
        url(r'^(?P<lang>[-\w]+)/$',           'show_language', {}, 'show_language'), 
        (r'^(?P<lang>[-\w]+)/feature/(?P<object_id>[0-9]+)/$', 'show_languagefeature'), 
        (r'^(?P<lang>[-\w]+)/feature/(?P<object_id>[0-9]+)/change$', 'describe_languagefeature'), 
        (r'^(?P<lang>[-\w]+)/feature/(?P<object_id>[0-9]+)/use$', 'revert_languagefeature_description'), 
        (r'^(?P<lang>[-\w]+)/feature/(?P<object_id>[0-9]+)/history/delete$', 'remove_languagefeature_description_version'), 
        (r'^(?P<lang>[-\w]+)/feature/(?P<object_id>[0-9]+)/history/$', 'show_languagefeature_history'), 
        (r'^(?P<lang>[-\w]+)/feature/(?P<object_id>[0-9]+)/history/compare$', 'compare_languagefeature_history'), 
        (r'^(?P<lang>[-\w]+)/change$',     'change_language'),
        (r'^(?P<slugs>[-+\w]+)/(?P<opt>[^/]*?)/?$',      'compare_language'), 
)

