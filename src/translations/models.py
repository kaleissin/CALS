# -*- coding: UTF-8 -*-

import logging
_LOG = logging.getLogger(__name__)

from django.conf import settings
from django.db import models
from django.utils.html import escape
from django.utils.timezone import now as tznow

from cals.tools import uslugify

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
    added_by = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        related_name='translation_exercises'
    )
    added = models.DateTimeField(default=tznow, editable=False)

    class Meta:
        db_table = 'cals_translationexercise'
        ordering = ('category', 'slug',)
        get_latest_by = 'added'

    def __unicode__(self):
        return self.name

    def save(self, user=None, *args, **kwargs):
        if not self.id:
            self.slug = uslugify(self.name)
            if user:
                self.added_by = user
            self.added = tznow()
        super(TranslationExercise, self).save(*args, **kwargs)

class Translation(Interlinear):
    translation = models.TextField()
    exercise = models.ForeignKey(TranslationExercise, related_name='translations')
    language = models.ForeignKey(Language, related_name='translations')
    translator = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        related_name='translations'
    )
    slug = models.SlugField(max_length=255, editable=False, blank=True)
    added = models.DateTimeField(default=tznow, editable=False)
    last_modified = models.DateTimeField(default=tznow, editable=False)

    RE = r'[-_\w]+/language/[-\w]+/[-\w]+/'

    def _generate_slug(self):
        pattern = '%(exercise)s/language/%(language)s/%(translator)s/'
        return pattern % {
                'exercise': self.exercise.slug,
                'language': self.language.id,
                'translator': self.translator.id }

    def _set_slug(self):
        pattern = '%(exercise)s/language/%(language)s/%(translator)s/'
        self.slug = self._generate_slug()

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
            self.last_modified = tznow()
        self._set_slug()
        super(Translation, self).save(*args, **kwargs)

