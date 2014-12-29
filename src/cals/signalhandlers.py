import logging
_LOG = logging.getLogger(__name__)

from datetime import timedelta, datetime

from django.conf import settings

from nano.blog.tools import add_entry_to_blog
from nano.blog.models import Entry

from nano.badge import add_badge, batchbadge
from nano.badge.models import Badge

from cals.people.models import Profile

def is_real_user(user):
    test_users = getattr(settings, 'NANO_USER_TEST_USERS', ())
    for test_user in test_users:
        if user.username.startswith(test_user):
            return False
    else:
        return True

def blog_new_user(new_user):
    test_users = getattr(settings, 'NANO_USER_TEST_USERS', ())
    # Add blog-entry
    for test_user in test_users:
        if new_user.username.startswith(test_user):
            break
    else:
        blog_template = 'blog/new_user.html'
        add_entry_to_blog(new_user, '%s just joined' % new_user.username, blog_template, date_field='date_joined')

def blog_unlurked_user(unlurked_user):
    if is_real_user(unlurked_user):
        blog_template = 'blog/unlurked_user.html'
        add_entry_to_blog(unlurked_user, '%s just unlurked' %
                unlurked_user.username, blog_template, date_field='date_joined')

# signals

def user_now_active(sender, **kwargs):
    _LOG.info('blogging unlurking')
    user = kwargs.get(u'user')
    blog_unlurked_user(user)

def new_user_anywhere(sender, **kwargs):
    new = kwargs.get(u'created', False)
    if new:
        new_user = kwargs[u'instance']
        test_users = getattr(settings, 'NANO_USER_TEST_USERS', ())

        # Add blog-entry
        for test_user in test_users:
            if new_user.username.startswith(test_user):
                break
        else:
            blog_template = 'blog/new_user.html'
            add_entry_to_blog(new_user, '%s just joined' % new_user.username, blog_template, date_field='date_joined')

        # Make sure there is a profile
        try:
            profile = new_user.profile
        except Profile.DoesNotExist:
            profile = Profile(user=new_user, display_name=new_user.username)
            profile.save()

def new_or_changed_language(sender, **kwargs):
    "Signal handler for cals.Language.post_save"
    new = kwargs[u'created']
    lang = kwargs[u'instance']
    if u'testarossa' in lang.slug:
        return
    new_title = 'New language: %s' % lang.name
    changed_title = 'Changed language: %s' % lang.name

    # Add relevant badge to conlanger
    badge = Badge.objects.get(name='Conlanger')
    add_badge(badge, lang.manager)
    batchbadge(badge, lang.editors.all())

    # Report on new language
    if new:
        # New language
        entry = add_entry_to_blog(lang, new_title, 'feeds/languages_newest_description.html', date_field='created')
        entry.tags = 'new_language'
        entry.save()
        lang.blogentries.add(entry)
    else:
        if lang.natlang: return
        # Changed language, has code to prevent duplicates
        latest = Entry.objects.latest()
        one_minute = timedelta(0, 60, 0)
        if latest.headline != changed_title:
            if not (latest.headline == new_title and (lang.last_modified - latest.pub_date < one_minute)):
                entry = add_entry_to_blog(lang, changed_title, 'feeds/languages_description.html', date_field='last_modified')
                entry.tags = 'changed_language'
                entry.save()
        else:
            latest.pub_date = datetime.now()
            latest.save()

def hidden_language(sender, **kwargs):
    languages = kwargs.get('languages', [])
    if languages:
        count = languages.count()
        if count == 1:
            lang = languages[0]
            title = u'Dropped language: %s' % lang.name
            add_entry_to_blog(lang, title,
                    'feeds/languages_single_dropped_description.html', date_field='last_modified')
        elif count > 1:
            title = u'Several languages dropped'
            add_entry_to_blog(languages, title,
                    'feeds/languages_multi_dropped_description.html', date_field='last_modified')

