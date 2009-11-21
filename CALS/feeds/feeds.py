import djatom as atom
from nano.blog.models import Entry
from cals.models import Language, Profile
from translations.models import TranslationExercise
from django.template.loader import render_to_string

STANDARD_AUTHORS = ({'name': 'admin'},)

class AbstractFeed(atom.Feed):
    feed_icon = "http://media.aldebaaran.uninett.no/CALS/img/favicon.ico"
    feed_authors = STANDARD_AUTHORS

class AllFeed(AbstractFeed):
    feed_title = 'CALS news'
    feed_id = 'http://cals.conlang.org/feeds/all/'

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

class UpdatedLanguagesFeed(AbstractFeed):
    feed_title = "CALS: recently modified languages"
    feed_id = 'http://cals.conlang.org/feeds/languages/'

    #description = "Recently modified languages at CALS"

    _item_template = 'feeds/languages_description.html'

    def items(self):
        return Language.objects.exclude(slug__startswith='testarossa').order_by('-last_modified')[:15]

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
    feed_id = 'http://cals.conlang.org/feeds/languages/'

    _item_template = 'feeds/languages_newest_description.html'

    #description = "Recently added languages at CALS"

    def items(self):
        return Language.objects.exclude(slug__startswith='testarossa').order_by('-created')[:15]

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
    feed_id = "http://cals.conlang.org/feeds/people/"
    #title_template = 'feeds/people_title_all.html'

    #description = "The people of CALS"
    _item_template = 'feeds/people_description_all.html'

    def items(self):
        return Profile.objects.filter(user__is_active=True).exclude(username__startswith='countach').order_by('display_name')

    def item_id(self, item):
        return item.display_name

    def item_title(self, item):
        return item.display_name
        #return 'New conlanger: %s' % item.display_name

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
    feed_id = "http://cals.conlang.org/feeds/people/"
    #title_template = 'feeds/people_title_all.html'

#     description = "The people that most recently joined CALS"
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
    feed_id = "http://cals.conlang.org/feeds/translations/"
    #title_template = 'feeds/people_title_all.html'

#     description = "The people that most recently joined CALS"
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

