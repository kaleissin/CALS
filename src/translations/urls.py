from django.conf.urls import *

from translations.models import Translation

EXERCISE_RE = r'^(?P<exercise>[-_\w]+)/'
LANG_RE = r'language/(?P<language>[-\w]+)/'
EXERCISE_LANG_RE = EXERCISE_RE + LANG_RE
TRANSLATION_RE = r'^(?P<slug>'+Translation.RE+r')$'

urlpatterns = patterns('translations.views',
        (r'^$',                       'list_all_translations'),
        (EXERCISE_LANG_RE+r'$',       'list_translation_for_language'), 
        (EXERCISE_LANG_RE+r'new$',    'add_languagetranslations'), 
        (EXERCISE_LANG_RE+r'change$', 'change_languagetranslations'), 
        (EXERCISE_LANG_RE+r'delete$', 'delete_languagetranslations'), 
        (LANG_RE+r'$',                'show_languagetranslations'), 
        (TRANSLATION_RE,              'show_translation_for_language'), 
        (EXERCISE_RE+r'$',            'show_translationexercise'),
)
