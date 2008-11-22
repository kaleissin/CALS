from django.conf.urls.defaults import *
from django.views.generic.simple import direct_to_template

from CALS.feeds.feeds import *

from django.contrib import admin
admin.autodiscover()

language_feeds = {
        'last_modified': UpdatedLanguagesFeed,
        'newest': NewestLanguagesFeed,
}

people_feeds = {
        'recent': RecentlyJoinedFeed,
        'all': AllPeopleFeed,
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
#    (r'^admin/webalizer/',      include('webalizer.urls')),
    (r'^admin/(.*)',            admin.site.root),


    (r'^thankyou$',             direct_to_template, thankyou_params),

    (r'^logged_in$',            direct_to_template, login_params),
    (r'^logout$',               'django.contrib.auth.views.logout_then_login'),
    (r'^signup/$',              'nano.user.views.signup'),
    (r'^password/reset/$',      'nano.user.views.password_reset', {'project_name': 'CALS'}),
    (r'^password/change/$',     'nano.user.views.password_change'),


    (r'^feeds/languages/(.*)/$', 'django.contrib.syndication.views.feed', {'feed_dict': language_feeds}),
    (r'^feeds/people/(.*)/$', 'django.contrib.syndication.views.feed', {'feed_dict': people_feeds}),
    (r'^feeds/(.*)/$', 'django.contrib.syndication.views.feed', {'feed_dict': {'all': AllFeed,},}),

    (r'^news/',                include('nano.blog.urls')),
    (r'^comments/',             include('django.contrib.comments.urls')),

    (r'^translation/',          include('translation.urls')),
    (r'^',                      include('cals.urls')),


#     (r'^openid/login/$', 'openid_auth.views.login'),
#     (r'^openid/ok/$', 'openid_auth.views.complete_openid_login'),
#     (r'^openid/logout/$', 'openid_auth.views.logout', {'next_page' : '/'}),

)

