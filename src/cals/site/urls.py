from __future__ import absolute_import
from __future__ import unicode_literals

from django.conf.urls import *
from django.conf import settings
from django.views.generic import RedirectView
from django.shortcuts import render
from django.contrib.auth.views import logout_then_login
from django.contrib import admin

from nano.user import views as nanouserviews
from nano.badge.models import Badge

from cals.site.feeds import feeds
from cals.people.views import auth_login as cals_auth_login

thankyou_params = {
    'template_name': 'cals/thankyou.html',
    'dictionary': {
        'me': 'thankyou',
        'bughunters': Badge.objects.get(name='Bughunter').receivers.all(),
    },
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

urlpatterns = [
    url(r'^feeds/translations/exercises/$',  feeds.NewTranslationExerciseFeed()),
    url(r'^feeds/translations/new/$',        feeds.NewTranslationFeed()),
    url(r'^feeds/languages/last_modified/$', feeds.UpdatedLanguagesFeed()),
    url(r'^feeds/languages/newest/$',        feeds.NewestLanguagesFeed()),
    url(r'^feeds/people/recent/$',           feeds.RecentlyJoinedFeed()),
    url(r'^feeds/people/all/$',              feeds.AllPeopleFeed()),
    url(r'^feeds/comments/$',                feeds.RecentCommentsFeed(), name='feed-comments'),
    url(r'^feeds/all/$',                     feeds.AllFeed()),
]

if settings.DEBUG:
    from django.contrib.staticfiles.urls import staticfiles_urlpatterns
    urlpatterns += staticfiles_urlpatterns()

urlpatterns += [
    # red tape
    url(r'^favicon\.ico$',      RedirectView.as_view(url='/static/img/favicon.ico', permanent=True)),
    url(r'^robots\.txt$',       render, robots_txt_params),

    url(r'^thankyou$',          render, thankyou_params),
    url(r'^help/rst_quickref$', render, help_rst_quickref_params),
    url(r'^help/',              render, help_params),
]

urlpatterns += [
    url(r'^admin/doc/',         include('django.contrib.admindocs.urls')),
    url(r'^admin/',             include(admin.site.urls)),

    url(r'^logged_in$',         render, login_params),
    url(r'^logout$',            logout_then_login),

    url(r'account/social/',     include('social_django.urls', namespace='social')),
    url(r'account/login/$',     cals_auth_login),
    url(r'^account/',           include('nano.user.urls')),

    # redirect the three links below into account/...
    url(r'^signup/$',           nanouserviews.signup),
    url(r'^password/reset/$',   nanouserviews.password_reset, {'project_name': 'CALS'}),
    url(r'^password/change/$',  nanouserviews.password_change),

    url(r'^news/',              include('nano.blog.urls')),

    url(r'^word/list/',         include('wordlist.list.urls')),
    url(r'^word/$',             RedirectView.as_view(url='/word/list/', permanent=True)),
    url(r'^translation/',       include('translations.urls')),
    url(r'^badge/',             include('nano.badge.urls')),
    url(r'^faq/',               include('nano.faq.urls')),
    url(r'^mark/',              include('nano.mark.urls')),

    url(r'meetups/',            include('meetups.urls')),

    url(r'^',                   include('cals.urls')),
]
