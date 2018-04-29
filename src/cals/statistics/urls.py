from __future__ import absolute_import
from __future__ import unicode_literals

from django.conf.urls import *

from cals.statistics import views

urlpatterns = [
        url(r'^features/$',                 views.show_feature_stats),
        url(r'^conlangers/$',               views.show_people_stats),
        url(r'^vocabularies/$',             views.show_vocab_stats),
        url(r'^language_names/$',           views.show_langname_stats),
        url(r'^averageness/$',              views.show_averageness_stats),
        url(r'^milestones/$',               views.show_milestone_stats),
        url(r'^$',                          views.show_stats),
]
