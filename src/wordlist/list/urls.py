from django.conf.urls.defaults import *
from django.views.generic import TemplateView

from wordlist.list.views import ListAllWordlistView, Swadesh100View, \
        HolmanListView, YakhontovListView, Swadesh207View, \
        SwadeshNotBuckView, HolmanAndYakhontovView, \
        Swadesh207Not100View, NotOnAnyListView
from wordlist.list.views import BuckView, CommonBuckView, \
        Buck1949View, BuckIDSView, BuckWOLDView
from wordlist.list.views import OnlyBuck1949View, OnlyBuckIDSView, \
        OnlyBuckWOLDView, OnlyBuckIDSWOLDView

urlpatterns = patterns('',
        url(r'^swadesh100/$',      
                Swadesh100View.as_view(), 
                name='swadesh100_list'),
        url(r'^swadesh207/$',      
                Swadesh207View.as_view(),
                name='swadesh207_list'),
        url(r'^holman/$',      
                HolmanListView.as_view(),
                name='holman_list'),
        url(r'^yakhontov/$',      
                YakhontovListView.as_view(),
                name='yakhontov_list'),

        url(r'^buck-common/$',      
                CommonBuckView.as_view(),
                name='buck_common_list'),
        url(r'^buck-1949/$',      
                Buck1949View.as_view(),
                name='buck_1949_list'),
        url(r'^buck-ids/$',      
                BuckIDSView.as_view(),
                name='buck_ids_list'),
        url(r'^buck-wold/$',      
                BuckWOLDView.as_view(),
                name='buck_wold_list'),
        url(r'^buck-only-1949/$',      
                OnlyBuck1949View.as_view(),
                name='buck_only_1949_list'),
        url(r'^buck-only-ids/$',      
                OnlyBuckIDSView.as_view(),
                name='buck_only_ids_list'),
        url(r'^buck-only-wold/$',      
                OnlyBuckWOLDView.as_view(),
                name='buck_only_wold_list'),
        url(r'^buck-ids-wold/$',      
                OnlyBuckIDSWOLDView.as_view(),
                name='buck_ids_wold_list'),
        url(r'^buck/$',      
                BuckView.as_view(),
                name='buck_list'),

        url(r'^swadesh-buck/$',      
                SwadeshNotBuckView.as_view(),
                name='swadesh_minus_buck_list'),
        url(r'^holman-yakhontov/$',      
                HolmanAndYakhontovView.as_view(),
                name='common-holman-yakhontov-list'),
        url(r'^swadesh207-swadesh100/$',      
                Swadesh207Not100View.as_view(), 
                name='swadesh207-swadesh100-list'),
        url(r'^unlisted/$',      
                NotOnAnyListView.as_view(), 
                name='unlisted-list'),

        url(r'^$',      
                ListAllWordlistView.as_view(), 
                name='wordlist_overview'),
)
