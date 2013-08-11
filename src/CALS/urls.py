from django.conf.urls.defaults import *
from django.conf import settings
from django.views.generic import RedirectView

from CALS.feeds.feeds import *

from django.contrib import admin
admin.autodiscover()

thankyou_params = {
    'template_name': 'cals/thankyou.html', 
    'dictionary': {'me': 'thankyou'},
}

help_params = {
    'template_name': 'static/help.html',
    'dictionary': { 'me': 'help', },
}

help_rst_quickref_params = {
    'template_name': 'static/rst_quickref.html',
    'dictionary': { 'me': 'help', },
}

robots_txt_params = {
    'template_name': 'robots.txt',
    'content_type': 'text/plain',
}

login_params = {
    'template_name': 'loggedin.html', 
    'dictionary': { 'me': 'home', },
}

urlpatterns = patterns('django.contrib.syndication.views',
    (r'^feeds/translations/exercises/$',    NewTranslationExerciseFeed()),
    (r'^feeds/translations/new/$',          NewTranslationFeed()),
    (r'^feeds/languages/last_modified/$',   UpdatedLanguagesFeed()),
    (r'^feeds/languages/newest/$',          NewestLanguagesFeed()),
    (r'^feeds/people/recent/$',             RecentlyJoinedFeed()),
    (r'^feeds/people/all/$',                AllPeopleFeed()),
    (r'^feeds/comments/$',                  RecentCommentsFeed()),
    (r'^feeds/all/$',                       AllFeed()),
)

if settings.DEBUG:
    from django.contrib.staticfiles.urls import staticfiles_urlpatterns
    urlpatterns += staticfiles_urlpatterns()

urlpatterns += patterns('',
    # red tape
    (r'^favicon\.ico$',         RedirectView.as_view(
                                        **{'url': '/static/img/favicon.ico'})),
    (r'^robots\.txt$',          'django.shortcuts.render', robots_txt_params),
 
    (r'^thankyou$',             'django.shortcuts.render', thankyou_params),
    (r'^help/rst_quickref$',    'django.shortcuts.render', help_rst_quickref_params),
    (r'^help/',                 'django.shortcuts.render', help_params),
)

urlpatterns += patterns('',
    (r'^admin/doc/',            include('django.contrib.admindocs.urls')),
    (r'^admin/',                include(admin.site.urls)),

    (r'^logged_in$',            'django.shortcuts.render', login_params),
    (r'^logout$',               'django.contrib.auth.views.logout_then_login'),

    (r'^account/',              include('nano.user.urls')),
    # redirect the three links below into account/...
    (r'^signup/$',              'nano.user.views.signup'),
    (r'^password/reset/$',      'nano.user.views.password_reset', {'project_name': 'CALS'}),
    (r'^password/change/$',     'nano.user.views.password_change'),
    (r'^news/',                 include('nano.blog.urls')),

    (r'^translation/',          include('translations.urls')),
    (r'^badge/',                include('nano.badge.urls')),
    (r'^faq/',                  include('nano.faq.urls')),
    (r'^mark/',                 include('nano.mark.urls')),
    (r'^',                      include('cals.urls')),

)

