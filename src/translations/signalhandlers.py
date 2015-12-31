from __future__ import absolute_import
from __future__ import unicode_literals

from nano.blog.tools import add_entry_to_blog
from nano.badge import add_badge
#from nano.badge.models import Badge

def new_translation(sender, **kwargs):
    "Signal handler for Translation.post_save"
    new = kwargs['created']
    trans = kwargs['instance']

    if new:
#         # Add relevant badge to conlanger
#         badge = Badge.objects.get(name='Translator')
#         add_badge(badge, trans.translator)

        # Blog
        if trans.exercise.id != 1:
            title = 'New translation of "%s" into %s by %s' % (trans.exercise.name, trans.language, trans.translator.profile.display_name)
            add_entry_to_blog(trans, title, 'translations/new_trans_blogentry.html', date_field='added')

