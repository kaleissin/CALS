from django.conf.urls import *

urlpatterns = patterns('cals.statistics.views',
        (r'^features/$',                 'show_feature_stats'),
        (r'^conlangers/$',               'show_people_stats'),
        (r'^vocabularies/$',             'show_vocab_stats'),
        (r'^language_names/$',           'show_langname_stats'),
        (r'^averageness/$',              'show_averageness_stats'),
        (r'^milestones/$',               'show_milestone_stats'),
        (r'^$',                          'show_stats'),
)
