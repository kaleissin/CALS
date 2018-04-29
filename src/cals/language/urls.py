from __future__ import absolute_import
from __future__ import unicode_literals
from django.conf.urls import *

from taggit.models import Tag
from tagtools.views import tagged_object_list

from cals import views as cviews
from cals.language import views as clviews
from cals.language.models import Language, LanguageFamily

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

urlpatterns = [
        url(r'^tag/(?P<tag>[-\w\d]+)/$', tagged_object_list, tags_language_dict),
]

urlpatterns += [
        url(LANG_RE+r'comment/', include('nano.comments.urls', namespace='cals', app_name='language'),
                {'model': Language, 
                'object_arg': 'lang',
                'object_field': 'slug',
                'extra_context': {'me': 'language'}}),
]

urlpatterns += [
        url(LANG_RE+r'feature/$',              clviews.show_features_for_language),
        url(r'^tag/$',                         clviews.list_languagetags),
        url(LANG_NAMES_RE+r'change$',          clviews.change_languagenames),
        url(r'^family/$',                      clviews.list_languagefamilies),
        url(r'^family/'+SLUG_RE+r'$',          clviews.show_languagefamilies),
]

urlpatterns += [
        url(r'^search$',                         cviews.search_languages),
        url(r'^([?](?P<action>[a-z]+))?$',       cviews.list_languages),
        url(r'^jrklist/$',                       cviews.language_jrklist),
        url(r'^p(?P<page>[0-9]+)/$',             cviews.language_list),
        url(r'^new$',                            cviews.create_language),
        url(LANG_RE+r'$',                        cviews.show_language),
        url(LANG_RE+r'change$',                  cviews.change_language),
        url(MULTISLUGS_RE+r'clone$',             cviews.clone_language),
        url(MULTISLUGS_RE+r'(?P<opt>[^/]*?)/?$', cviews.compare_language),
]

urlpatterns += [
        url(r'^',                  include('cals.languagefeature.urls')),
]
