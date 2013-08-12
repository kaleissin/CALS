from django.conf.urls.defaults import *

from wordlist.views import LanguageWordListView, WordlistView, \
        LanguageListView, LanguageSenseDetailView, AddWordForLanguageView, \
        SenseDetailView

PK_RE = r'(?P<pk>\d+)'

urlpatterns = patterns('',
        (r'^lists/',         include('wordlist.list.urls')),
        (r'^language/',      include('wordlist.language.urls')),
)

urlpatterns += patterns('',
        url(r'^$',      WordlistView.as_view(),
                name='wordlist_index'),
        url(r'^'+PK_RE+r'/$', SenseDetailView.as_view(),
                name='wordlist_sense'),
)
