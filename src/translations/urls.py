from __future__ import absolute_import
from __future__ import unicode_literals

from django.conf.urls import *

from translations import views
from translations.models import Translation


CATEGORY_RE = r'^(?P<category>\d+)/'
EXERCISE_RE = r'^(?P<exercise>[-_\w]+)/'
LANG_RE = r'language/(?P<language>[-\w]+)/'
EXERCISE_LANG_RE = EXERCISE_RE + LANG_RE
TRANSLATION_RE = EXERCISE_RE + r'language/(?P<language>\d+)/(?P<translator>\d+)/'

urlpatterns = [
        url(r'^$',                       views.list_all_translations, name='translation-home'),
        url(r'^\*/$',                    views.list_all_translationexercise_categories, name='translationexercise-category-home'),
        url(CATEGORY_RE,                 views.show_translationexercise_category, name='translationexercise-category'),
        url(EXERCISE_LANG_RE+r'$',       views.list_translation_for_language),
        url(EXERCISE_LANG_RE+r'new$',    views.add_languagetranslations),
        url(LANG_RE+r'$',                views.show_languagetranslations),
        url(TRANSLATION_RE+r'change$',   views.change_languagetranslations, name='translation-update'),
        url(TRANSLATION_RE+r'delete$',   views.delete_languagetranslations, name='translation-delete'),
        url(TRANSLATION_RE+r'$',         views.show_translation_for_language, name='translation-detail'),
        url(EXERCISE_RE+r'$',            views.show_translationexercise),
]
