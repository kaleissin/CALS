# -*- coding: UTF-8 -*-

from datetime import datetime

from cals import getLogger
LOG = getLogger('cals.models')

from django.contrib.auth.models import User
from django.db import models
from django.template.defaultfilters import slugify
from django.utils.html import escape

from cals.models import Language

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

    def save(self, *args, **kwargs):
        new_il = self.get_interlinear()
        if new_il:
            self.il_xhtml = new_il
        super(Interlinear, self).save(*args, **kwargs)

    def get_interlinear(self):
        if not self.interlinear.strip():
            return u''
        interlinear = escape(self.interlinear)
        format = self.il_format
        if format == u'leipzig':
            try:     
                from leipzig import InterlinearText
            except ImportError, e:
                assert False, e
                format = u'monospace'
            else:
                il = InterlinearText()
                il.add_text(interlinear)
                return il.to_html()
        return u'<pre>%s</pre>' % interlinear

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
    added = models.DateTimeField(default=datetime.now, editable=False)
    last_modified = models.DateTimeField(default=datetime.now, editable=False)

    class Meta:
        db_table = 'cals_translation'
        ordering = ('exercise', 'language', 'translator')

    def __unicode__(self):
        return self.translation

    def save(self, user=None, *args, **kwargs):
        if not self.id and user:
            self.translator = user
        self.last_modified = datetime.now()
        super(Translation, self).save(*args, **kwargs)

