
from datetime import timedelta, datetime

from nano.blog import add_entry_to_blog
from nano.blog.models import Entry

def new_user(sender, **kwargs):
    "Signal handler for nano.user.new_user_created"
    new_user = kwargs[u'user']
    blog_template = 'blog/new_user.html'
    add_entry_to_blog(new_user, '%s just joined' % new_user.username, blog_template, date_field='date_joined')

def new_or_changed_language(sender, **kwargs):
    "Signal handler for cals.Language.post_save"
    new = kwargs[u'created']
    lang = kwargs[u'instance']
    if u'testarossa' in lang.slug:
        return
    new_title = 'New language: %s' % lang.name
    changed_title = 'Changed language: %s' % lang.name
    if new:
        add_entry_to_blog(lang, new_title, 'feeds/languages_newest_description.html', date_field='created')
    else:
        latest = Entry.objects.latest()
        one_minute = timedelta(0, 60, 0)
        if latest.headline != changed_title:
            if not (latest.headline == new_title and (lang.last_modified - latest.pub_date < one_minute)):
                add_entry_to_blog(lang, changed_title, 'feeds/languages_description.html', date_field='last_modified')
        else:
            latest.pub_date = datetime.now()
            latest.save()
