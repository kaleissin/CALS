from __future__ import absolute_import
from __future__ import unicode_literals

import logging

from django.db import models
from django.conf import settings
from django.utils.encoding import python_2_unicode_compatible

from cals.tools import uslugify

LOG = logging.getLogger(__name__)


@python_2_unicode_compatible
class BuckCategory(models.Model):
    id = models.IntegerField(primary_key=True)
    name = models.TextField()
    notes = models.TextField(blank=True, null=True)

    class Meta:
        ordering = ('id',)
        verbose_name = 'Buck category'
        verbose_name_plural = 'Buck categories'

    def __str__(self):
        return '%i. %s' % (self.id, self.name)


class SenseManager(models.Manager):
    def yakholman(self):
        return super(SenseManager,
                self).get_queryset().filter(yakhontov=True,
                holman_list=True)
    def all_buck(self):
        return super(SenseManager,
               self).get_queryset().filter(buck_category__isnull=False)

    def most_common_buck(self):
        return super(SenseManager,
                self).get_queryset().filter(buck=True, ids=True,
                wold=True)


@python_2_unicode_compatible
class Sense(models.Model):
    entry = models.CharField(max_length=40)
    slug = models.SlugField()
    pos = models.CharField(max_length=16, blank=True, null=True)
    notes = models.TextField(blank=True, null=True)
    swadesh_100 = models.BooleanField(default=False)
    swadesh_207 = models.IntegerField(blank=True, null=True)
    yakhontov = models.BooleanField(default=False)
    holman_rank = models.IntegerField(blank=True, null=True)
    holman_list = models.BooleanField(default=False)
    buck_category = models.ForeignKey(BuckCategory, blank=True, null=True)
    buck = models.BooleanField(default=False)
    buck_number = models.CharField(max_length=12, blank=True, null=True)
    wold = models.BooleanField(default=False)
    wold_number = models.CharField(max_length=12, blank=True, null=True)
    ids = models.BooleanField(default=False)
    ids_number = models.CharField(max_length=12, blank=True, null=True)
    uld2 = models.CharField(max_length=3, blank=True, null=True)
    see_also = models.ManyToManyField('self', blank=True)
    added = models.DateTimeField(auto_now_add=True)
    suggested_by = models.ForeignKey(settings.AUTH_USER_MODEL, default=1)

    objects = SenseManager()

    class Meta:
        ordering = ('id',)

    def __str__(self):
        return '\u201c%s\u201d' % self.entry

    def save(self, *args, **kwargs):
        self.slug = uslugify(self.entry)
        super(Sense, self).save(*args, **kwargs)

    def show_notes(self):
        if self.pos and self.notes:
            return '%s, %s' % (self.pos, self.notes)
        if self.pos:
            return self.pos
        if self.notes:
            return self.notes
        return None

    def show_buck_numbers(self):
        b = ''
        if self.buck_number:
            b = self.buck_number.rstrip('0')
        i = ''
        if self.ids_number:
            i = self.ids_number.rstrip('0')
        w = ''
        if self.wold_number:
            w = self.wold_number.rstrip('0')
        if b+i+w:
            if b==i==w:
                return 'b'+self.buck_number
            front = 'b%s' % self.buck_number if b else ''
            mid = 'i%s' % self.ids_number if i else ''
            back = 'w%s' % self.wold_number if w else ''
            if i != w:
                mid = mid + ' ' + back
            if b != i+w:
                front = front + ' ' + mid
            return front.strip()
        else:
            # None set
            return None


@python_2_unicode_compatible
class Word(models.Model):
    word = models.CharField(max_length=40, blank=True, null=True)
    senses = models.ManyToManyField(Sense, related_name='words', blank=True)
    notes = models.TextField(blank=True, null=True)
    language = models.ForeignKey('cals.language', related_name='words')
    not_applicable = models.NullBooleanField(default=False)
    see_also = models.ManyToManyField('self', blank=True)
    added = models.DateTimeField(auto_now_add=True)
    added_by = models.ForeignKey(settings.AUTH_USER_MODEL, related_name='words_added')
    last_modified = models.DateTimeField(auto_now=True)
    last_modified_by = models.ForeignKey(settings.AUTH_USER_MODEL,
            related_name='words_modified')

    def __str__(self):
        return self.word or ''

    def save(self, *args, **kwargs):
        self.not_applicable = False
        if not self.word:
            self.not_applicable = True
        super(Word, self).save(*args, **kwargs)


@python_2_unicode_compatible
class SkippedWord(models.Model):
    sense = models.ForeignKey(Sense, related_name='skipped_words')
    language = models.ForeignKey('cals.language', related_name='skipped_words')
    added = models.DateTimeField(auto_now_add=True)
    added_by = models.ForeignKey(settings.AUTH_USER_MODEL,
            related_name='skipped_words')

    def __str__(self):
        return self.sense
