from __future__ import unicode_literals

from datetime import datetime

from django.contrib.syndication.views import Feed
from django.utils.feedgenerator import Atom1Feed
from django.template.loader import render_to_string

from nano.blog.models import Entry
from nano.comments.models import Comment

from cals.tools import uslugify

from cals.language.models import Language
from cals.people.models import Profile

from translations.models import TranslationExercise, Translation

STANDARD_AUTHOR = u'admin'

class AbstractFeed(Feed):
    _domain = 'cals.conlang.org'
    categories = ('',)
    feed_type = Atom1Feed
    author_name = STANDARD_AUTHOR

    def _make_datetime(self, date):
        return date.strftime('%Y-%m-%dT%H:%M:%S')

    def _make_datetimeid(self, date):
        return date.strftime('%Y%m%d%H%M%S')

    def _make_date(self, date):
        return date.strftime('%Y-%m-%d')

    def link(self):
        return '/feeds/%s/' % self.categories[0]

    def feed_guid(self):
        return 'http://%s/feeds/%s/' % (self._domain, self.categories[0])

    def base_id(self, item):
        category = self.categories[0]
        if category:
            category = category + '/'
        return 'tag:%s,%s:%s' % (self._domain, 
                self._make_date(self.item_pubdate(item)), 
                category)

    def item_content(self, item):
        d = {'obj': item}
        return {"type": "html",}, render_to_string(self.description_template, d)


class AllFeed(AbstractFeed):
    title = 'CALS news'
    categories = ('all',)
    subtitle = 'The fifteen newest'
    
    def items(self):
        return Entry.objects.order_by('-pub_date')[:15]

    def item_guid(self, item):
        return self.base_id(item) + str(item.id)

    def item_title(self, item):
        return item.headline

    def item_content(self, item):
        return {"type": "html",}, item.content

    def item_pubdate(self, item):
        return item.pub_date

    def item_link(self, item):
        return '/news/latest/'

    def item_description(self, item):
        return item.content

class RecentCommentsFeed(AbstractFeed):
    title = "CALS: recent comments"
    categories = ('comments/recent',)
    
    description_template = 'feeds/comments_description.html'

    def items(self):
        return Comment.objects.order_by('-added')[:15]

    def item_guid(self, item):
        return self.base_id(item) + '/%s-%s' % (uslugify(unicode(item.content_object)), item.user.id)

    def item_title(self, item):
        return 'New comment by %s on %s' % (item.user.profile.display_name, item.content_object)

    def item_author_name(self, item):
        return unicode(item.user)

    def item_pubdate(self, item):
        return item.added

class UpdatedLanguagesFeed(AbstractFeed):
    title = "CALS: recently modified languages"
    categories = ('languages/updated',)
    
    description_template = 'feeds/languages_description.html'

    def items(self):
        return Language.objects.conlangs().exclude(slug__startswith='testarossa').order_by('-last_modified')[:15]

    def item_guid(self, item):
        return '%s%s-%s' % (self.base_id(item), 
                item.slug,
                self._make_datetimeid(self.item_pubdate(item)))

    def item_title(self, item):
        return 'Changed language: %s' % item.name

    def item_author_name(self, item):
        return unicode(item.added_by.profile.display_name)

    def item_pubdate(self, item):
        return item.created

class NewestLanguagesFeed(AbstractFeed):
    title = "CALS: recently added languages"
    categories = ('languages/new',)
    
    description_template = 'feeds/languages_newest_description.html'

    def items(self, obj):
        return Language.objects.conlangs().exclude(slug__startswith='testarossa').order_by('-created')[:15]

    def item_guid(self, item):
        return '%s%s/%s' % (self.base_id(item), 
                        item.slug,
                        item.id)

    def item_title(self, item):
        return 'New language: %s' % item.name

    def item_author_name(self, item):
        return unicode(item.added_by.profile.display_name)

    def item_pubdate(self, item):
        return item.created

class AllPeopleFeed(AbstractFeed):
    title = "CALS: all people"
    categories = ('people/changed',)
    
    description_template = 'feeds/people_description_all.html'

    def items(self):
        return Profile.objects.filter(user__is_active=True).exclude(username__startswith='countach').order_by('display_name')

    def item_guid(self, item):
        return '%s%s-%s' % (self.base_id(item),
                item.display_name,
                self._makedatetimeid(self.item_pubdate(item)))

    def item_title(self, item):
        return item.display_name

    def item_author_name(self, item):
        return unicode(item.display_name)

    def item_pubdate(self, item):
        return item.user.date_joined

class RecentlyJoinedFeed(AbstractFeed):
    title = "CALS: recently joined people"
    categories = ('people/new',)
    
    description_template = 'feeds/people_description.html'

    def items(self, obj):
        return Profile.objects.exclude(user__is_active=False, username__startswith='countach').order_by('-user__date_joined')[:15]

    def item_guid(self, item):
        return '%s%s-%s' % (self.base_id(item),
                item.display_name,
                self._make_datetimeid(self.item_pubdate(item)))

    def item_title(self, item):
        return '%s just joined!' % item.display_name

    def item_author_name(self, item):
        return unicode(item.display_name)

    def item_pubdate(self, item):
        return item.user.date_joined

class NewTranslationExerciseFeed(AbstractFeed):
    title = "CALS: new translation exercises"
    categories = ('translations/exercises',)
    
    description_template = 'feeds/transex_description.html'

    def items(self):
        return TranslationExercise.objects.order_by('-added')[:15]

    def item_guid(self, item):
        return '%s%s' % (self.base_id(item),
                item.slug)

    def item_title(self, item):
        return u'To translate: "%s"' % item.name

    def item_author_name(self, item):
        return unicode(item.added_by)

    def item_pubdate(self, item):
        return item.added

    def item_link(self, item):
        return '/translation/%s/' % item.slug

class NewTranslationFeed(AbstractFeed):
    title = "CALS: new translation"
    categories = ('translations/new',)
    
    description_template = 'feeds/trans_description.html'

    def items(self):
        return Translation.objects.order_by('-added')[:15]

    def item_guid(self, item):
        return self.base_id(item) + '%s/%s/%s' % (item.exercise.slug,
                uslugify(item.language.name),
                uslugify(item.translator.username))

    def item_title(self, item):
        return '%s translated "%s" into %s' % (item.translator, item.exercise.name, item.language)

    def item_author_name(self, item):
        return unicode(item.translator)

    def item_pubdate(self, item):
        return item.added

    def item_link(self, item):
        return '/translation/%s/language/%s/%s/' % (item.exercise.slug, item.language.slug, item.translator.profile.slug)
