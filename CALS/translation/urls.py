from django.conf.urls.defaults import *

urlpatterns = patterns('translation.views',
        (r'^(?P<exercise>[-_\w]+)/language/(?P<lang>[-\w]+)/$', 'list_translation_for_language'), 
        (r'^(?P<exercise>[-_\w]+)/language/(?P<lang>[-\w]+)/new$', 'add_languagetranslations'), 
        (r'^(?P<exercise>[-_\w]+)/language/(?P<lang>[-\w]+)/change$', 'change_languagetranslations'), 
        (r'^(?P<exercise>[-_\w]+)/language/(?P<lang>[-\w]+)/delete$', 'delete_languagetranslations'), 
        (r'^(?P<exercise>[-_\w]+)/language/(?P<lang>[-\w]+)/(?P<user>[-\w]+)/$', 'show_translation_for_language'), 
        (r'^language/(?P<lang>[-\w]+)/$', 'show_languagetranslations'), 
        (r'^(?P<exercise>[-_\w]+)/$', 'show_translationexercise'),
        (r'^$', 'list_all_translations'),
)
