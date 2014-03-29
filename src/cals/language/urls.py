from django.conf.urls import *
from django.contrib.auth.models import User

from taggit.models import Tag

from cals.models import Language, LanguageFamily

LANG_RE = r'^(?P<lang>[-\w]+)/'
LANG_NAMES_RE = LANG_RE + r'names/'
MULTISLUGS_RE = r'^(?P<slugs>[-+\w]+)/'
SLUG_RE = r'(?P<slug>[-\w]+)/'

## tagging
tags_language_dict = {
        'queryset_or_model': Language,
        'template_name': 'cals/language_tag_list.html',
#        'extra_context': { 'me': 'language' },
}

urlpatterns = patterns('tagtools.views',
        (r'^tag/(?P<tag>[-\w\d]+)/$', 'tagged_object_list', tags_language_dict),
)

#urlpatterns += patterns('django.views.generic',
# #        (r'^latest/$', 'date_based.archive_index', language_by_date),
# #        (r'^(?P<year>\d{4})/$',            'date_based.archive_year', language_by_year),
        #(r'^(?P<year>\d{4})/w(?P<week>[a-z]{3})/$', 'date_based.archive_week', language_by_week),
#)

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
        (r'^',                  include('cals.languagefeature.urls')),
        (MULTISLUGS_RE+r'clone$',             'clone_language'),
        (MULTISLUGS_RE+r'(?P<opt>[^/]*?)/?$', 'compare_language'),
)

urlpatterns += patterns('cals.language.views',
        (r'^tag/$',                         'list_languagetags'),
        (LANG_NAMES_RE+r'change$',          'change_languagenames'),
        (r'^family/$',                      'list_languagefamilies'),
        (r'^family/'+SLUG_RE+r'$',          'show_languagefamilies'),
)
