from django.contrib.syndication.feeds import Feed
from django.utils import feedgenerator
from cals.models import Language, Profile
from django.contrib.auth.models import User

class RSSUpdatedLanguages(Feed):
    #feed_type = feedgenerator.Atom1Feed
    title = "CALS: recently modified languages"
    title_template = 'feeds/languages_title.html'

    description = "Recently modified languages at CALS"
    description_template = 'feeds/languages_description.html'
    #subtitle = description

    link = "http://cals.conlang.org/feeds/languages/"

    def items(self):
        return Language.objects.exclude(slug__startswith='testarossa').order_by('-last_modified')[:15]

    def item_author_name(self, item):
        return item.added_by

class RSSNewestLanguages(Feed):
    #feed_type = feedgenerator.Atom1Feed
    title = "CALS: recently added languages"
    title_template = 'feeds/languages_newest_title.html'

    description = "Recently added languages at CALS"
    description_template = 'feeds/languages_newest_description.html'
    #subtitle = description

    link = "http://cals.conlang.org/feeds/languages/"

    def items(self):
        return Language.objects.exclude(slug__startswith='testarossa').order_by('-created')[:15]

    def item_author_name(self, item):
        return item.added_by

class RSSAllPeople(Feed):
    #feed_type = feedgenerator.Atom1Feed
    title = "CALS: all people"
    title_template = 'feeds/people_title_all.html'

    description = "The people of CALS"
    description_template = 'feeds/people_description_all.html'
    #subtitle = description

    link = "http://cals.conlang.org/feeds/people/"

    def items(self):
        return Profile.objects.filter(user__is_active=True).exclude(username='countach').order_by('display_name')

    def item_author_name(self, item):
        return item.display_name

class RSSRecentlyJoined(Feed):
    #feed_type = feedgenerator.Atom1Feed
    title = "CALS: recently joined people"
    title_template = 'feeds/people_title.html'

    description = "The people that most recently joined CALS"
    description_template = 'feeds/people_description.html'
    #subtitle = description

    link = "http://cals.conlang.org/feeds/people/"

    def items(self):
        return User.objects.exclude(username='countach').order_by('-date_joined')[:15]

    def item_author_name(self, item):
        return item.username
