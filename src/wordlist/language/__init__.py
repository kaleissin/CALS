import logging

from django.db.models import Q
from django.db import transaction
from django.shortcuts import get_object_or_404

LOG = logging.getLogger(__name__)

_me = 'word'

class WordlistMixin(object):

    def get_context_data(self, **kwargs):
        context = kwargs
        context['me'] = _me
        context['params'] = kwargs
        return context

def get_object_or_slug_from_kwargs(model, field='pk', **kwargs):
    pk = kwargs.get(field, None)
    if not pk:
        if 'params' in kwargs:
            pk = kwargs['params'].get(field, None) 
    if pk: 
        pk = int(pk)
    slug = kwargs.get(u'slug', None)
    return get_object_or_404(model, Q(pk=pk)|Q(slug=slug))
    try:
        object = get_object_or_404(model, Q(pk=pk)|Q(slug=slug))
    except:
        assert False, model.objects.filter(Q(pk=pk)|Q(slug=slug))
        raise
    return object

def get_object_from_kwargs(model, field='pk', **kwargs):
    pk = kwargs.get(field, None)
    if not pk:
        if 'params' in kwargs:
            pk = kwargs['params'].get(field, None) 
    if pk: 
        pk = int(pk)
    return get_object_or_404(model, pk=pk)

def get_field_from_kwargs(field='pk', **kwargs):
    pk = kwargs.get(field, None)
    if not pk:
        if 'params' in kwargs:
            pk = kwargs['params'].get(field, None) 
    if pk: 
        pk = int(pk)
    return pk

def get_language_from_kwargs(**kwargs):
    from cals.language.models import Language
    language = kwargs.get('language', None)
    if not language:
        try:
            return get_object_or_404(Language, slug=kwargs.get(u'langslug', None))
        except:
            assert False, kwargs 
    return language

def language_has_word(language, word):
    if language.words.filter(word=word):
        return True
    return False

def language_has_sense(language, sense):
    if language.words.filter(senses=sense):
        return True
    return False

def may_edit(language, user):
    if user.is_authenticated():
        if language.public:
            LOG.info("$s is public, %s may edit")
            return True
        if user == language.manager:
            LOG.info("$s is managed by %s who may edit")
            return True
        if user in language.editors.all():
            LOG.info("$s is edited by %s who may edit")
            return True
    LOG.info("%s may not edit %s", user, language)
    return False

def save_word(self, word):
    with transaction.atomic():
        word = form.save(commit=False)
        word.language = self.language
        word.not_applicable = False
        word.added_by = self.user
        word.last_modified_by = self.user
        word.save()
        word.senses.add(self.sense)
        return word
    return None
