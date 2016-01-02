from __future__ import absolute_import
from __future__ import unicode_literals

from django.conf.urls import *

urlpatterns = patterns('cals.statistics.views',
        url(r'^features/$',                 'show_feature_stats'),
        url(r'^conlangers/$',               'show_people_stats'),
        url(r'^vocabularies/$',             'show_vocab_stats'),
        url(r'^language_names/$',           'show_langname_stats'),
        url(r'^averageness/$',              'show_averageness_stats'),
        url(r'^milestones/$',               'show_milestone_stats'),
        url(r'^$',                          'show_stats'),
)
