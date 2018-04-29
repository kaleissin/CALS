from django.conf.urls import *

from wordlist.language.views import LanguageWordListView, \
        LanguageListView, LanguageSenseDetailView, AddWordForLanguageView

PK_RE = r'(?P<pk>\d+)/'
WORDPK_RE = r'(?P<wordid>\d+)/'
LANGUAGE_RE =    r'^(?P<langslug>[-a-z0-9]+)/'
LANGUAGE_PK_RE = LANGUAGE_RE+PK_RE

# Language specific pages

urlpatterns = [
        url(LANGUAGE_PK_RE+r'$',
                LanguageSenseDetailView.as_view(),
                name='show_sense_for_language'),
        url(LANGUAGE_PK_RE+r'add/$',
                AddWordForLanguageView.as_view(),
                name='add_word_for_language'),
        url(LANGUAGE_PK_RE+WORDPK_RE+r'edit/$',
                AddWordForLanguageView.as_view(),
                name='edit_word_for_language'),
        url(LANGUAGE_RE+r'$',     
                LanguageWordListView.as_view(),
                name='show_words_for_language'),
        url(r'^$', 
                LanguageListView.as_view(),
                name='list_languages_with_words'),
]
