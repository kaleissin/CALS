from django.conf.urls.defaults import *

EXERCISE_RE = r'^(?P<exercise>[-_\w]+)/'
LANG_RE = r'language/(?P<lang>[-\w]+)/'
EXERCISE_LANG_RE = EXERCISE_RE + LANG_RE

urlpatterns = patterns('translations.views',
        (LANG_RE+r'$', 'show_languagetranslations'), 
        (EXERCISE_LANG_RE+r'$', 'list_translation_for_language'), 
        (EXERCISE_LANG_RE+r'new$', 'add_languagetranslations'), 
        (EXERCISE_LANG_RE+r'change$', 'change_languagetranslations'), 
        (EXERCISE_LANG_RE+r'delete$', 'delete_languagetranslations'), 
        (EXERCISE_LANG_RE+r'(?P<user>[-\w]+)/$', 'show_translation_for_language'), 
        (EXERCISE_RE+r'$', 'show_translationexercise'),
        (r'^$', 'list_all_translations'),
)
