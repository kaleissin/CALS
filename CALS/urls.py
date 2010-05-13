from django.conf.urls.defaults import *
from django.views.generic.simple import direct_to_template

from CALS.feeds.feeds import *

from django.contrib import admin
admin.autodiscover()

translation_feeds = { 'exercises': NewTranslationExerciseFeed,
        }

language_feeds = {
        'last_modified': UpdatedLanguagesFeed,
        'newest': NewestLanguagesFeed,
}

people_feeds = {
        'recent': RecentlyJoinedFeed,
        'all': AllPeopleFeed,
}

all_feeds = {
        'all': AllFeed,
}

comment_feeds = {
        'comments': RecentCommentsFeed,
}

thankyou_params = {
        'template': 'cals/thankyou.html', 
        'extra_context': { 
                'me': 'thankyou',
        },
}

index_params = {
        'template': 'cals/index.html', 
        'extra_context': { 
                'me': 'home',
        },
}

login_params = {
        'template': 'loggedin.html', 
        'extra_context': { 
                'me': 'home',
        },
}

privacy_params = {
        'template': 'cals/privacy.html', 
        'extra_context': { 
                'me': 'privacy',
        },
}

copyright_params = {
        'template': 'cals/copyright.html', 
        'extra_context': { 
                'me': 'copyright',
        },
}

todo_params = {
        'template': 'cals/TODO.html', 
        'extra_context': { 
                'me': 'todo',
        },
}

urlpatterns = patterns('',
    (r'^admin/doc/',            include('django.contrib.admindocs.urls')),
    (r'^admin/',                include(admin.site.urls)),

    # red tape
    (r'^favicon\.ico$', 'django.views.generic.simple.redirect_to', {'url': '/media/img/favicon.ico'}),

    (r'^thankyou$',             direct_to_template, thankyou_params),
    (r'^help/rst_quickref$',    direct_to_template, {
                                'template': 'static/rst_quickref.html', 
                                'extra_context': 
                                        { 'me': 'help'}
                                }),
    (r'^help/',                 direct_to_template, {
                                'template': 'static/help.html',
                                'extra_context': 
                                        { 'me': 'help'}
                                }),

    (r'^logged_in$',            direct_to_template, login_params),
    (r'^logout$',               'django.contrib.auth.views.logout_then_login'),

    (r'^feeds/translations/(.*)/$', 'django.contrib.syndication.views.feed', {'feed_dict': translation_feeds}),
    (r'^feeds/languages/(.*)/$', 'django.contrib.syndication.views.feed', {'feed_dict': language_feeds}),
    (r'^feeds/people/(.*)/$', 'django.contrib.syndication.views.feed', {'feed_dict': people_feeds}),
    (r'^feeds/(\w*)/$', 'django.contrib.syndication.views.feed', {'feed_dict': comment_feeds}),
    (r'^feeds/(.*)/$', 'django.contrib.syndication.views.feed', {'feed_dict': all_feeds}),
#    (r'^feeds/all/$', 'django.contrib.syndication.views.feed', {'feed_dict': {'all': AllFeed,},}),

    (r'^account/',              include('nano.user.urls')),
    # redirect the three links below into account/...
    (r'^signup/$',              'nano.user.views.signup'),
    (r'^password/reset/$',      'nano.user.views.password_reset', {'project_name': 'CALS'}),
    (r'^password/change/$',     'nano.user.views.password_change'),
    (r'^news/',                 include('nano.blog.urls')),

    (r'^translation/',          include('translations.urls')),
    (r'^badge/',                include('nano.badge.urls')),
    (r'^faq/',                  include('nano.faq.urls')),
    (r'^mark/',                  include('nano.mark.urls')),
    (r'^',                      include('cals.urls')),

)

