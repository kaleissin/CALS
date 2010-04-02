from datetime import datetime

from django.template.defaultfilters import slugify

import djatom as atom
from nano.blog.models import Entry
from cals.models import Language, Profile
from translations.models import TranslationExercise, Translation
from nano.comments.models import Comment
from django.template.loader import render_to_string

STANDARD_AUTHORS = ({'name': 'admin'},)

class AbstractFeed(atom.Feed):
    _domain = 'cals.conlang.org'
    feed_icon = "http://media.aldebaaran.uninett.no/CALS/img/favicon.ico"
    feed_authors = STANDARD_AUTHORS

    def _make_date(self, date):
        return date.strftime('%Y-%m-%dT%H:%M:%S')

class AllFeed(AbstractFeed):
    feed_title = 'CALS news'
    
    def feed_id(self):
            return 'http://%s/feeds/all/' % self._domain

    def items(self):
        return Entry.objects.order_by('-pub_date')

    def item_id(self, item):
        return str(item.id)

    def item_title(self, item):
        return item.headline

    def item_content(self, item):
        return {"type": "html",}, item.content

    def item_updated(self, item):
        return item.pub_date

class RecentCommentsFeed(AbstractFeed):
    feed_title = "CALS: recent comments"
    
    def feed_id(self):
            return 'http://%s/feeds/comments/' % self._domain

    _item_template = 'feeds/comments_description.html'

    def items(self):
        return Comment.objects.order_by('-added')[:15]

    def item_id(self, item):
        return 'tag:%s,%s/recent/%s-%s' % (self._domain, self._make_date(item.added), slugify(item.content_object), item.user.id)

    def item_title(self, item):
        return 'New comment by %s on %s' % (item.user.get_profile().display_name, item.content_object)

    def item_content(self, item):
        d = {'obj': item}
        return {"type": "html",}, render_to_string(self._item_template, d)

    def item_authors(self, item):
        return ({'name': unicode(item.user)},)

    def item_updated(self, item):
        return item.added

    def item_published(self, item):
        return item.added

class UpdatedLanguagesFeed(AbstractFeed):
    feed_title = "CALS: recently modified languages"
    
    def feed_id(self):
            return 'http://%s/feeds/languages/updated/' % self._domain

    _item_template = 'feeds/languages_description.html'

    def items(self):
        return Language.objects.conlangs().exclude(slug__startswith='testarossa').order_by('-last_modified')[:15]

    def item_id(self, item):
        return '%s-%s' % (item.slug, item.last_modified)

    def item_title(self, item):
        return 'Changed language: %s' % item.name

    def item_content(self, item):
        d = {'obj': item}
        return {"type": "html",}, render_to_string(self._item_template, d)

    def item_authors(self, item):
        return ({'name': unicode(item.added_by)},)

    def item_updated(self, item):
        return item.last_modified

    def item_published(self, item):
        return item.created

class NewestLanguagesFeed(AbstractFeed):
    feed_title = "CALS: recently added languages"
    
    def feed_id(self):
            return 'http://%s/feeds/languages/new/' % self._domain

    _item_template = 'feeds/languages_newest_description.html'

    def items(self):
        return Language.objects.conlangs().exclude(slug__startswith='testarossa').order_by('-created')[:15]

    def item_id(self, item):
        return '%s-created-%s' % (item.slug, item.created)

    def item_title(self, item):
        return 'New language: %s' % item.name

    def item_content(self, item):
        d = {'obj': item}
        return {"type": "html",}, render_to_string(self._item_template, d)

    def item_authors(self, item):
        return ({'name': unicode(item.added_by.get_profile().display_name)},)

    def item_updated(self, item):
        return item.created

    def item_published(self, item):
        return item.created

class AllPeopleFeed(AbstractFeed):
    feed_title = "CALS: all people"
    
    def feed_id(self):
            return 'http://%s/feeds/people/changed/' % self._domain

    _item_template = 'feeds/people_description_all.html'

    def items(self):
        return Profile.objects.filter(user__is_active=True).exclude(username__startswith='countach').order_by('display_name')

    def item_id(self, item):
        return item.display_name

    def item_title(self, item):
        return item.display_name

    def item_content(self, item):
        d = {'obj': item.user}
        return {"type": "html",}, render_to_string(self._item_template, d)

    def item_authors(self, item):
        return ({'name': unicode(item.display_name)},)

    def item_updated(self, item):
        return item.user.last_login

    def item_published(self, item):
        return item.user.date_joined

class RecentlyJoinedFeed(AbstractFeed):
    feed_title = "CALS: recently joined people"
    
    def feed_id(self):
            return 'http://%s/feeds/people/new/' % self._domain

    _item_template = 'feeds/people_description.html'

    def items(self):
        return Profile.objects.exclude(user__is_active=False, username__startswith='countach').order_by('-user__date_joined')[:15]

    def item_id(self, item):
        return item.display_name

    def item_title(self, item):
        return '%s just joined!' % item.display_name

    def item_content(self, item):
        d = {'obj': item}
        return {"type": "html",}, render_to_string(self._item_template, d)

    def item_authors(self, item):
        return ({'name': unicode(item.display_name)},)

    def item_updated(self, item):
        return item.user.date_joined

    def item_published(self, item):
        return item.user.date_joined

class NewTranslationExerciseFeed(AbstractFeed):
    feed_title = "CALS: new translation exercises"
    
    def feed_id(self):
            return 'http://%s/feeds/translations/exercises' % self._domain

    _item_template = 'feeds/transex_description.html'

    def items(self):
        return TranslationExercise.objects.order_by('-added')[:15]

    def item_id(self, item):
        return item.slug

    def item_title(self, item):
        return 'To translate: "%s"' % item.name

    def item_content(self, item):
        d = {'obj': item}
        return {"type": "html",}, render_to_string(self._item_template, d)

    def item_authors(self, item):
        return ({'name': unicode(item.added_by)},)

    def item_updated(self, item):
        return item.added

    def item_published(self, item):
        return item.added

class NewTranslationFeed(AbstractFeed):
    feed_title = "CALS: new translation"
    
    def feed_id(self):
            return 'http://%s/feeds/translations/new' % self._domain

    _item_template = 'feeds/trans_description.html'

    def items(self):
        return Translation.objects.order_by('-added')[:15]

    def item_id(self, item):
        return '%s/%s/%s' % (item.exercise.slug, item.language, item.translator)

    def item_title(self, item):
        return '%s translated "%s" into %s' % (item.translator, item.exercise.name, item.language)

    def item_content(self, item):
        d = {'obj': item}
        return {"type": "html",}, render_to_string(self._item_template, d)

    def item_authors(self, item):
        return ({'name': unicode(item.translator)},)

    def item_updated(self, item):
        return item.added

    def item_published(self, item):
        return item.added

