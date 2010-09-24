from django.conf.urls.defaults import *
from django.contrib.auth.models import User

from tagging.models import Tag

from cals.models import Language, LanguageFamily

LANG_RE = r'^(?P<lang>[-\w]+)/'
LANG_NAMES_RE = LANG_RE + r'names/'
LANG_FEAT_RE = LANG_RE + r'feature/(?P<object_id>[0-9]+)/'
LANG_FEAT_HIST_RE = LANG_FEAT_RE + r'history/'
MULTISLUGS_RE = r'^(?P<slugs>[-+\w]+)/'
SLUG_RE = r'(?P<slug>[-\w]+)/'

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

langfam_dict = {
    'queryset': LanguageFamily.objects.all(),
    'extra_context': { 'me': 'language' },
}

urlpatterns = patterns('tagging.views',
        (r'^tag/(?P<tag>[- \w\d]+)/$', 'tagged_object_list', tags_language_dict),
)

urlpatterns += patterns('django.views.generic',
        (r'^tag/$',                        'list_detail.object_list', taglist_language_dict),
        (r'^family/$',                      'list_detail.object_list', langfam_dict), 
        (r'^family/'+SLUG_RE+r'$',          'list_detail.object_detail', langfam_dict), 
# #        (r'^latest/$', 'date_based.archive_index', language_by_date),
# #        (r'^(?P<year>\d{4})/$',            'date_based.archive_year', language_by_year),
        #(r'^(?P<year>\d{4})/w(?P<week>[a-z]{3})/$', 'date_based.archive_week', language_by_week),
)

urlpatterns += patterns('',
        (LANG_RE+r'comment/', include('nano.comments.urls', app_name='language'),
                {'model': Language, 
                'object_arg': 'lang',
                'object_field': 'slug',
                'extra_context': {'me': 'language'}}),
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
        (r'^search$',                         'search_languages'),
        (r'^([?](?P<action>[a-z]+))?$',       'list_languages'),
        (r'^jrklist/$',                       'language_jrklist'),
        (r'^p(?P<page>[0-9]+)/$',             'language_list'),
        (r'^new$',                            'create_language'),
        (LANG_RE+r'$',                        'show_language'), 
        (LANG_RE+r'change$',                  'change_language'),
        (LANG_FEAT_RE+r'$',                   'show_languagefeature'), 
        (LANG_FEAT_RE+r'change$',             'describe_languagefeature'), 
        (LANG_FEAT_RE+r'use$',                'revert_languagefeature_description'), 
        (LANG_FEAT_HIST_RE+r'delete$',        'remove_languagefeature_description_version'), 
        (LANG_FEAT_HIST_RE+r'$',              'show_languagefeature_history'), 
        (LANG_FEAT_HIST_RE+r'compare$',       'compare_languagefeature_history'), 
        (MULTISLUGS_RE+r'clone$',             'clone_language'), 
        (MULTISLUGS_RE+r'(?P<opt>[^/]*?)/?$', 'compare_language'), 
)

urlpatterns += patterns('cals.language.views',
        (LANG_NAMES_RE+r'change$',            'change_languagenames'),
)
