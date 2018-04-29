from __future__ import absolute_import
from __future__ import unicode_literals
from django.conf.urls import *

from wordlist.views import LanguageWordListView, WordlistView, \
        LanguageListView, LanguageSenseDetailView, AddWordForLanguageView, \
        SenseDetailView

PK_RE = r'(?P<pk>\d+)'

urlpatterns = [
        url(r'^lists/',         include('wordlist.list.urls')),
        url(r'^language/',      include('wordlist.language.urls')),
]

urlpatterns += [
        url(r'^$',      WordlistView.as_view(),
                name='wordlist_index'),
        url(r'^'+PK_RE+r'/$', SenseDetailView.as_view(),
                name='wordlist_sense'),
]
