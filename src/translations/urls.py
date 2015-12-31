from __future__ import absolute_import
from __future__ import unicode_literals

from django.conf.urls import *

from translations.models import Translation

EXERCISE_RE = r'^(?P<exercise>[-_\w]+)/'
LANG_RE = r'language/(?P<language>[-\w]+)/'
EXERCISE_LANG_RE = EXERCISE_RE + LANG_RE
TRANSLATION_RE = EXERCISE_RE + r'language/(?P<language>\d+)/(?P<translator>\d+)/'

urlpatterns = patterns('translations.views',
        url(r'^$',                       'list_all_translations', name='translation-home'),
        url(EXERCISE_LANG_RE+r'$',       'list_translation_for_language'),
        url(EXERCISE_LANG_RE+r'new$',    'add_languagetranslations'),
        url(LANG_RE+r'$',                'show_languagetranslations'),
        url(TRANSLATION_RE+r'change$',   'change_languagetranslations', name='translation-update'),
        url(TRANSLATION_RE+r'delete$',   'delete_languagetranslations', name='translation-delete'),
        url(TRANSLATION_RE+r'$',         'show_translation_for_language', name='translation-detail'),
        url(EXERCISE_RE+r'$',            'show_translationexercise'),
)
