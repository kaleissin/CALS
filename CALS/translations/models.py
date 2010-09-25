# -*- coding: UTF-8 -*-

from datetime import datetime

import logging
_LOG = logging.getLogger(__name__)

from django.contrib.auth.models import User
from django.db import models
from django.template.defaultfilters import slugify
from django.utils.html import escape

from cals.language.models import Language

def get_interlinear(model):
    if not model.interlinear.strip():
        return u''
    interlinear = model.interlinear
    format = model.il_format
    if format == u'leipzig':
        try:     
            from interlinears.leipzig import InterlinearText
        except ImportError, e:
            assert False, e
            format = u'monospace'
        else:
            il = InterlinearText()
            return il.do_text(interlinear)
    return u'<pre>%s</pre>' % escape(interlinear)

class Interlinear(models.Model):
    INTERLINEAR_FORMATS = (
            ('monospace', 'WYSIWYG monospace'),
            ('leipzig', 'Leipzig Glossing Rules'),
    )

    interlinear = models.TextField('Interlinear', blank=True, default='', db_column='il_text')
    il_xhtml = models.TextField('Interlinear, formatted', blank=True, default='', db_column='il_xhtml')
    il_format = models.CharField('Interlinear format', max_length=20, choices=INTERLINEAR_FORMATS, blank=True, default='monospace')

    class Meta:
        abstract = True

    def get_interlinear(self):
        return get_interlinear(self)

    def save(self, *args, **kwargs):
        new_il = self.get_interlinear()
        if new_il:
            self.il_xhtml = new_il
        super(Interlinear, self).save(*args, **kwargs)

class TranslationExerciseCategory(models.Model):
    name = models.CharField(max_length=64, unique=True)

    class Meta:
        verbose_name_plural = 'translation-exercise categories'
        db_table = 'cals_translationcategory'

    def __unicode__(self):
        return self.name

class TranslationExercise(models.Model):
    name = models.CharField(max_length=64, unique=True,
            help_text="A short name to refer to the translation excrcise")
    slug = models.SlugField(max_length=64, unique=True, editable=False)
    exercise = models.TextField(unique=True)
    comment = models.TextField(blank=True, null=True)
    category = models.ForeignKey(TranslationExerciseCategory,
            related_name='exercises')
    added_by = models.ForeignKey(User, related_name='translation_exercises')
    added = models.DateTimeField(default=datetime.now, editable=False)

    class Meta:
        db_table = 'cals_translationexercise'
        ordering = ('category', 'slug',)
        get_latest_by = 'added'

    def __unicode__(self):
        return self.name

    def save(self, user=None, *args, **kwargs):
        if not self.id:
            self.slug = slugify(self.name)
            if user:
                self.added_by = user
        self.added = datetime.now()
        super(TranslationExercise, self).save(*args, **kwargs)

class Translation(Interlinear):
    translation = models.TextField()
    exercise = models.ForeignKey(TranslationExercise, related_name='translations')
    language = models.ForeignKey(Language, related_name='translations')
    translator = models.ForeignKey(User, related_name='translations')
    slug = models.SlugField(max_length=255, editable=False, blank=True)
    added = models.DateTimeField(default=datetime.now, editable=False)
    last_modified = models.DateTimeField(default=datetime.now, editable=False)

    RE = r'[-_\w]+/language/[-\w]+/[-\w]+/'

    def _set_slug(self):
        pattern = '%(exercise)s/language/%(language)s/%(translator)s/'
        self.slug = pattern % {
                'exercise': self.exercise.slug, 
                'language': self.language.slug,
                'translator': self.translator.username }

    class Meta:
        db_table = 'cals_translation'
        ordering = ('exercise', 'language', 'translator')
        unique_together = (('language', 'translator', 'exercise'),)
        get_latest_by = 'last_modified'

    def __unicode__(self):
        return self.translation

    def save(self, user=None, batch=False, *args, **kwargs):
        if not self.id and user:
            self.translator = user
        if not batch:
            self.last_modified = datetime.now()
        self._set_slug()
        super(Translation, self).save(*args, **kwargs)

# -- signals
from signalhandlers import new_translation
from django.db.models.signals import post_save

post_save.connect(new_translation, sender=Translation)
