from nano.blog import add_entry_to_blog

def new_translation(sender, **kwargs):
    "Signal handler for Translation.post_save"
    new = kwargs[u'created']
    trans = kwargs[u'instance']
    if new and trans.exercise.id != 1:
        title = u'New translation of "%s" into %s by %s' % (trans.exercise.name, trans.language, trans.translator.get_profile().display_name)
        add_entry_to_blog(trans, title, 'translation/new_trans_blogentry.html', date_field='added')

