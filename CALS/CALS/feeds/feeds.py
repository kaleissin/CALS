from datetime import datetime

from django.template.defaultfilters import slugify

import djatom as atom
from nano.blog.models import Entry
from cals.language.models import Language
from cals.people.models import Profile
from translations.models import TranslationExercise, Translation
from nano.comments.models import Comment
from django.template.loader import render_to_string

STANDARD_AUTHORS = ({'name': 'admin'},)

class AbstractFeed(atom.Feed):
    _domain = 'cals.conlang.org'
    category = ''
    feed_icon = "http://media.aldebaaran.uninett.no/CALS/img/favicon.ico"
    feed_authors = STANDARD_AUTHORS

    def _make_datetime(self, date):
        return date.strftime('%Y-%m-%dT%H:%M:%S')

    def _make_datetimeid(self, date):
        return date.strftime('%Y%m%d%H%M%S')

    def _make_date(self, date):
        return date.strftime('%Y-%m-%d')

    def feed_id(self):
        return 'http://%s/feeds/%s/' % (self._domain, self.category)

    def base_id(self, item):
        category = self.category
        if category:
            category = category + '/'
        return 'tag:%s,%s:%s' % (self._domain, 
                self._make_date(self.item_updated(item)), 
                category)


class AllFeed(AbstractFeed):
    feed_title = 'CALS news'
    category = 'all'
    
    def items(self):
        return Entry.objects.order_by('-pub_date')

    def item_id(self, item):
        return self.base_id(item) + str(item.id)

    def item_title(self, item):
        return item.headline

    def item_content(self, item):
        return {"type": "html",}, item.content

    def item_updated(self, item):
        return item.pub_date

class RecentCommentsFeed(AbstractFeed):
    feed_title = "CALS: recent comments"
    category = 'comments/recent'
    
    _item_template = 'feeds/comments_description.html'

    def items(self):
        return Comment.objects.order_by('-added')[:15]

    def item_id(self, item):
        return self.base_id(item) + '/%s-%s' % (slugify(item.content_object), item.user.id)

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
    category = 'languages/updated'
    
    _item_template = 'feeds/languages_description.html'

    def items(self):
        return Language.objects.conlangs().exclude(slug__startswith='testarossa').order_by('-last_modified')[:15]

    def item_id(self, item):
        return '%s%s-%s' % (self.base_id(item), 
                item.slug,
                self._make_datetimeid(self.item_updated(item)))

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
    category = 'languages/new'
    
    _item_template = 'feeds/languages_newest_description.html'

    def items(self):
        return Language.objects.conlangs().exclude(slug__startswith='testarossa').order_by('-created')[:15]

    def item_id(self, item):
        return '%s%s/%s' % (self.base_id(item), 
                        item.slug,
                        item.id)

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
    category = 'people/changed'
    
    _item_template = 'feeds/people_description_all.html'

    def items(self):
        return Profile.objects.filter(user__is_active=True).exclude(username__startswith='countach').order_by('display_name')

    def item_id(self, item):
        return '%s%s-%s' % (self.base_id(item),
                item.display_name,
                self._makedatetimeid(self.item_updated(item)))

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
    category = 'people/new'
    
    _item_template = 'feeds/people_description.html'

    def items(self):
        return Profile.objects.exclude(user__is_active=False, username__startswith='countach').order_by('-user__date_joined')[:15]

    def item_id(self, item):
        return '%s%s-%s' % (self.base_id(item),
                item.display_name,
                self._make_datetimeid(self.item_published(item)))

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
    category = 'translations/exercises'
    
    _item_template = 'feeds/transex_description.html'

    def items(self):
        return TranslationExercise.objects.order_by('-added')[:15]

    def item_id(self, item):
        return '%s%s' % (self.base_id(item),
                item.slug)

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
    category = 'translations/new'
    
    _item_template = 'feeds/trans_description.html'

    def items(self):
        return Translation.objects.order_by('-added')[:15]

    def item_id(self, item):
        return self.base_id(item) + '%s/%s/%s' % (item.exercise.slug, 
                slugify(item.language), 
                slugify(item.translator.username))

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

