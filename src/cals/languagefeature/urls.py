from django.conf.urls import *

LANG_RE = r'^(?P<language>[-\w]+)/'
LANG_FEAT_RE = LANG_RE + r'feature/(?P<feature>[0-9]+)/'
LANG_FEAT_HIST_RE = LANG_FEAT_RE + r'history/'

urlpatterns = patterns('cals.languagefeature.views',
        (LANG_FEAT_RE+r'$',                   'show_languagefeature'),
        (LANG_FEAT_RE+r'change$',             'describe_languagefeature'),
        (LANG_FEAT_RE+r'delete$',             'delete_languagefeature'),
        (LANG_FEAT_RE+r'use$',                'revert_languagefeature_description'),
        (LANG_FEAT_HIST_RE+r'delete$',        'remove_languagefeature_description_version'),
        (LANG_FEAT_HIST_RE+r'$',              'show_languagefeature_history'),
        (LANG_FEAT_HIST_RE+r'compare$',       'compare_languagefeature_history'),
)