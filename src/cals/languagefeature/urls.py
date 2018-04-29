from __future__ import absolute_import
from __future__ import unicode_literals

from django.conf.urls import *

from cals.languagefeature import views

LANG_RE = r'^(?P<language>[-\w]+)/'
LANG_FEAT_RE = LANG_RE + r'feature/(?P<feature>[0-9]+)/'
LANG_FEAT_HIST_RE = LANG_FEAT_RE + r'history/'

urlpatterns = [
        url(LANG_FEAT_RE+r'$',                   views.show_languagefeature),
        url(LANG_FEAT_RE+r'change$',             views.describe_languagefeature),
        url(LANG_FEAT_RE+r'delete$',             views.delete_languagefeature),
        url(LANG_FEAT_RE+r'use$',                views.revert_languagefeature_description),
        url(LANG_FEAT_HIST_RE+r'delete$',        views.remove_languagefeature_description_version),
        url(LANG_FEAT_HIST_RE+r'$',              views.show_languagefeature_history),
        url(LANG_FEAT_HIST_RE+r'compare$',       views.compare_languagefeature_history),
]
