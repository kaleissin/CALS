
# -*- coding: UTF-8 -*-

import unicodedata
import datetime as dt
from datetime import datetime

import logging
_LOG = logging.getLogger(__name__)

from django.contrib.auth.models import User
from django.contrib.contenttypes.models import ContentType
from django.contrib.contenttypes import generic
from django.db import models, connection
from django.db.models import Q
from django.db.models.query import QuerySet
from django.template.defaultfilters import slugify
from django.utils.html import strip_tags
from django.utils.encoding import smart_unicode
from django.utils.translation import ugettext_lazy as _

import tagging
from tagging.fields import TagField
from countries.models import Country
#from nano.link.models import Link

from interlinears import leipzig

from cals import markup_as_restructuredtext
from cals.tools import uni_slugify, asciify, next_id
from cals.tools.models import Description, DescriptionMixin, FREETEXT_TYPES

from cals.people.models import Profile

# Create your models here.
FEATURE_GROUPS_CHOICES = (
        ('Phonology','Phonology'),
        ('Morphology','Morphology'),
        ('Nominal Categories','Nominal Categories'),
        ('Nominal Syntax','Nominal Syntax'),
        ('Verbal Categories','Verbal Categories'),
        ('Word Order','Word Order'),
        ('Simple Clauses','Simple Clauses'),
        ('Complex Sentences','Complex Sentences'),
        ('Lexicon','Lexicon'),
        ('Sign Languages','Sign Languages'),
        ('Other','Other'),
        )

# BEGIN Features

class ActiveQuerySet(QuerySet):
    def active(self):
        return self.filter(active=True)

    def passive(self):
        return self.filter(active=False)

class ActivePassiveManager(models.Manager):
    "Needed to use the custom queryset"
    def get_query_set(self):
        return ActiveQuerySet(self.model)

    def active(self):
        return self.get_query_set().active()

    def passive(self):
        return self.get_query_set().passive()

class ActiveManager(models.Manager):
    "Needed to use the custom queryset"
    def get_query_set(self):
        return ActiveQuerySet(self.model)

    def active(self):
        return self.get_query_set().active()

class PassiveManager(models.Manager):
    "Needed to use the custom queryset"
    def get_query_set(self):
        return ActiveQuerySet(self.model)

    def passive(self):
        return self.get_query_set().passive()

class Category(models.Model):
    name = models.CharField(max_length=20, unique=True)
    active = models.BooleanField(default=False, editable=False)

    objects = ActivePassiveManager()
    active_objects = ActiveManager()
    passive_objects = PassiveManager()

    class Meta:
        ordering = ['id']
        verbose_name_plural = 'categories'
        db_table = 'cals_category'

    def __unicode__(self):
        return self.name

class Feature(models.Model, DescriptionMixin):
    MAX_WALS_FEATURE = 142
    name = models.CharField(max_length=96, unique=True) # Longest faeture-name... 93 chars!!
    category = models.ForeignKey(Category)
    tags = TagField()
    wals = models.BooleanField(default=False, editable=False)
    overrides = models.ForeignKey('self', blank=True, null=True)
    active = models.BooleanField(default=False, editable=False)
    added_by = models.ForeignKey(User, editable=False, null=True)

    objects = ActivePassiveManager()
    active_objects = ActiveManager()
    passive_objects = PassiveManager()

    class Meta:
        unique_together = ('id', 'name', 'category')
        ordering = ['id']
        #order_with_respect_to = 'category'
        db_table = 'cals_feature'

    def __unicode__(self):
        return self.name

class FeatureValueManager(models.Manager):
    def _value_counts(self):
        return self.extra(select={
            'value_count': 'SELECT count(*) FROM "cals_languagefeature" AS lf WHERE lf.value_id = id GROUP BY id'
            #'count': 'SELECT count(lf.value_id) FROM "cals_languagefeature" AS lf WHERE lf.value_id = id GROUP BY id'
            })

    def value_counts(self):
        return self._value_counts().order_by('count')

class FeatureValue(models.Model, DescriptionMixin):
    feature = models.ForeignKey(Feature, related_name='values')
    name = models.CharField(max_length=64)
    position = models.IntegerField(null=True)#, editable=False)

    class Meta:
        unique_together = ('feature', 'name')
        ordering = ['feature__id', 'position']
        #order_with_respect_to = 'feature'
        db_table = 'cals_featurevalue'

    def __unicode__(self):
        return self.name

# END Features

class LangtypeQuerySet(QuerySet):
    def conlangs(self):
        return self.exclude(natlang=True)

    def natlangs(self):
        return self.filter(natlang=True)

class DefaultLanguageManager(models.Manager):
    def get_query_set(self):
        return LangtypeQuerySet(self.model).filter(visible=True)

    def conlangs(self):
        return self.get_query_set().conlangs()

    def natlangs(self):
        return self.get_query_set().natlangs()

class NaturalLanguageManager(models.Manager):
    def get_query_set(self):
        return super(NaturalLanguageManager, self).get_query_set().filter(natlang=True)

class UnorderedTreeMixin(models.Model):
    part_of = models.ForeignKey('self', blank=True, null=True, default=None)
    path = models.CharField(max_length=255, blank=True, default='')

    _sep = u'/'

    class Meta:
        abstract = True

    def save(self, *args, **kwargs):
        if not self.id:
            super(UnorderedTreeMixin, self).save(*args, **kwargs)

        self._set_path()
        super(UnorderedTreeMixin, self).save(*args, **kwargs)


    def _set_path(self):

        if self.part_of:
            self.path = "%s%i/" % (self.part_of.path, self.id)
        else:
            self.path = "%i/" % self.id

    @property
    def level(self):
        return unicode(self.path).count(self._sep)

    def roots(self):
        return self._default_manager.filter(part_of__isnull=True)

    def get_path(self):
        return [self._default_manager.get(id=p) for p in unicode(self.path).split(self._sep) if p]

    def descendants(self):
        return self._default_manager.filter(path__startswith=self.path).exclude(id=self.id)

    def parent(self):
        return self.part_of

    def siblings(self):
        return [p for p in self.part_of.descendants() if p.level == self.level]

    def children(self):
        return [p for p in self.descendants() if p.level == self.level + 1]

    def is_sibling_of(self, node):
        return self.part_of == node.part_of

    def is_child_of(self, node):
        return self.part_of == node

    def is_root(self):
        """Roots have no parents"""

        return bool(self.part_of)

    def is_leaf(self):
        """Leaves have no descendants"""

        return self.descendants().count() == 0

class LanguageFamily(UnorderedTreeMixin):
    name = models.CharField(max_length=64)
    slug = models.SlugField(editable=False, blank=True, null=True)

    objects = models.Manager()

    class Meta:
        db_table = 'cals_languagefamily'
        verbose_name_plural = 'language families'
        ordering = ('name',)

    def __unicode__(self):
        return self.name

    def save(self, *args, **kwargs):
        self.slug = slugify(self.name)

        super(LanguageFamily, self).save(*args, **kwargs)

class Language(models.Model):
    name = models.CharField('External name', max_length=64, 
            help_text=u'Anglified name, safe for computing. ASCII!')
    internal_name = models.CharField('Internal name', max_length=64,
            blank=True,
            help_text=u'What the speakers call their language. All of unicode OK')
    slug = models.SlugField(max_length=64, editable=False, blank=True, null=True)
    author = models.CharField('Author(s)', max_length=128)
    homepage = models.URLField(null=True, blank=True)
    background = models.CharField(max_length=256, blank=True,
            help_text="""A short summary of the history/background of
            your language. 4 lines (256 letters) inc. formatting, no HTML.""")
    background_type = models.CharField(blank=True, max_length=20, choices=FREETEXT_TYPES)
    from_earth = models.NullBooleanField(null=True, blank=True,
            help_text="""Example: Klingon and Barsoomian (from Mars!) would set 'No' here, while
            Brithenig and Esperanto would set 'Yes'. As for Sindarin, it
            depends on whether you consider Arda to be the Earth""")
    greeting = models.CharField(max_length=64, blank=True,
            db_column='greeting')
    vocabulary_size = models.PositiveIntegerField(null=True, blank=True,
            help_text="Estimated vocabulary size")
    family = models.ForeignKey(LanguageFamily, blank=True, null=True,
            related_name='languages')
    natlang = models.BooleanField(default=False, editable=False)

    # statistics
    # Denormalization, real-time average-score is expensive
    average_score = models.IntegerField(editable=False, default=0)
    # Denormalization, real-time num-of-features can't be sorted on
    num_features = models.IntegerField(editable=False, default=0)
    # Denormalization, real-time num-of-features can't be sorted on
    num_avg_features = models.IntegerField(editable=False, default=0)

    # Permissions and metadata
    visible = models.BooleanField(default=True)
    tags = TagField(help_text="Separate tags with commas or spaces")
    public = models.BooleanField('Editable by all', default=True,
            help_text="""If yes/on, all logged in may edit. If no/off, only the
            manager and editors may edit.""")
    added_by = models.ForeignKey(User,editable=False, blank=True, null=True, related_name='languages')
    manager = models.ForeignKey(User,
            blank=True,
            null=True,
            related_name='manages',
            help_text=u"""The person who controls who gets to
            change the description of this language. This makes 
            it possible to hand a language over to another person.""")
    editors = models.ManyToManyField(User, blank=True, null=True, 
            related_name='edits',
            help_text=u"""People who get to change the description of this language.""")
    created = models.DateTimeField(default=datetime.now)
    last_modified = models.DateTimeField(blank=True, null=True, editable=False, default=datetime.now)
    last_modified_by = models.ForeignKey(User, editable=False, blank=True, null=True, related_name='languages_modified')

    # Managers
    objects = DefaultLanguageManager()
    natlangs = NaturalLanguageManager()
    all_langs = models.Manager()

    class Meta:
        ordering = ['name']
        db_table = 'cals_language'
        get_latest_by = 'last_modified'

    def __unicode__(self):
        return self.name

    def save(self, user=None, solo=True, *args, **kwargs):
        now = datetime.utcnow()
        # New lang
        if not self.id and user:
            self.added_by = user
            self.manager = user
        if solo:
            self.last_modified = now
        if not self.internal_name:
            self.internal_name = self.name
            self.name = asciify(self.name)
        self.slug = slugify(self.name)

        if not self.manager:
            self.manager = self.added_by or user
        # XXX Cannot set average score here as there would be an
        # import-loop
        super(Language, self).save(*args, **kwargs)

        self.save_langnames(now=now)
    
    #@permalink
    def get_absolute_url(self):
        return "/language/%s/" % self.slug 
    #    return ('cals.views.show_language', [str(self.id)]) 

    def save_langnames(self, now=None):
        """Save name-changes in separate table, if Language has an
        id. For some reason, get_or_create leads to duplicates.
        """
        assert self.id, 'Language not saved'
        if not now:
            now = datetime.utcnow()
        names = LanguageName.objects.filter(language=self)
        if not names.filter(name=self.name):
            l = LanguageName(language=self, name=self.name, added=now)
            l.save()
        # Save internal name only if different from external
        if not names.filter(name=self.internal_name) and self.name != self.internal_name:
            l = LanguageName(language=self, name=self.internal_name, added=now, internal=True)
            l.save()
        # If Language renamed, preserve old names
        prev_names = names.exclude(name=self.internal_name).exclude(name=self.name).exclude(alternate=True).exclude(previous=True)
        if prev_names:
            prev_names.update(previous=True)
                
    def set_average_score(self):
        if not self.num_features:
            self.average_score = 0
        else:
            self.average_score = int(self.num_avg_features / float(self.num_features) * 100)

    def set_num_features(self):
        self.num_features = LanguageFeature.objects.filter(language=self).count()

    def can_change(self, profile):
        if isinstance(profile, User):
            profile = profile.get_profile()
        if self.manager == profile.user:
            return True
        if len(self.editors.filter(id=profile.user.id)):
            return True
        return False

    def get_name(self):
        if self.internal_name:
            return self.internal_name
        return self.name

    def get_infodensity(self):
        feature_weight = 0.95
        density = 0
        num_features = Feature.objects.active().count()
        singles = 7.0
        if self.greeting:
            density += 1
        if self.background:
            density += 1
        if self.vocabulary_size:
            density += 1
        if self.internal_name:
            density += 1
        if self.tags:
            density += 1
        if self.homepage:
            density += 1
        # TODO: trans should be weighed higher
        if self.translations.count() > 1:
            density += 1
        weighted_num_features = self.num_features * feature_weight
        density = (weighted_num_features + density) / (num_features + singles)
        return density

    def alternates(self):
        return self.alternate_names.exclude(name=self.name)

    def previous_names(self):
        return self.alternates().exclude(name=self.internal_name)

class SearchManager(models.Manager):

    def find_prefix(self, q):
        q = uni_slugify(q)
        return self.get_query_set().filter(slug__istartswith=q)

    def find_anywhere(self, q):
        q = uni_slugify(q)
        return self.get_query_set().filter(slug__icontains=q)

    def find(self, q, anywhere=False):
        if anywhere:
            return self.find_anywhere(q)
        else:
            return self.find_prefix(q)

class LanguageName(models.Model):
    language = models.ForeignKey(Language, related_name="alternate_names")
    added = models.DateTimeField(blank=True, null=True)
    name = models.CharField(max_length=64)
    slug = models.SlugField(max_length=64, editable=False, blank=True)
    internal = models.BooleanField('Internal name?', default=False)
    alternate = models.BooleanField('Additional?', default=False)
    previous = models.BooleanField('No longer in use?', default=False)

    objects = SearchManager()

    class Meta:
        db_table = 'cals_languagenames'
        unique_together = ('language', 'name')
        verbose_name_plural = 'language names'

    def save(self, *args, **kwargs):
        self.slug = uni_slugify(smart_unicode(self.name))
        if not self.added:
            self.added = datetime.utcnow()
        super(LanguageName, self).save(*args, **kwargs)

    def __unicode__(self):
        return self.name

    def is_current(self):
        return (self.name == self.language.name) or (self.name == self.language.internal_name)

class WALSCode(models.Model):
    language = models.OneToOneField(Language, primary_key=True, related_name="wals_code")
    walscode = models.CharField(max_length=3, unique=True)

    class Meta:
        db_table = 'cals_walscodes'

    def __unicode__(self):
        return "%i: %s" % (self.language.id, self.walscode)

class LanguageFeature(models.Model, DescriptionMixin):
    language = models.ForeignKey(Language, related_name='features')
    feature = models.ForeignKey(Feature, related_name='languages')
    value = models.ForeignKey(FeatureValue) #, related_name='languages')

    objects = models.Manager()

    class Meta:
        unique_together = ('language', 'feature')
        db_table = 'cals_languagefeature'

    def __unicode__(self):
        return u"%s / %s / %s" % (self.language, self.feature, self.value)


class UTC(dt.tzinfo):
    ZERO = dt.timedelta(0)
    """UTC"""
    def tzname(self, dt):
        return "UTC"
    def utcoffset(self, dt):
        return self.ZERO
    def dst(self, dt):
        return self.ZERO

class ExternalInfo(models.Model):
    EXTERNALINFO_TYPES = (
            ('homepage', 'Homepage'),
            ('dictionary', 'Dictionary'),
    )

    language = models.ForeignKey(Language, related_name='externalinfo')
    category = models.CharField(max_length=20,
            choices=EXTERNALINFO_TYPES)
    on_request = models.BooleanField(default=False)
    link = models.URLField(blank=True, null=True)

    def __unicode__(self):
        return u"%s %s: on request: %s, link: %s" % (self.language,
                self.category, self.on_request, self.link or 'No')

# --- Signals
from django.db.models.signals import post_save
from nano.user import new_user_created

from signalhandlers import new_or_changed_language, new_user_anywhere

post_save.connect(new_user_anywhere, sender=User)
#post_save.connect(new_or_changed_language, sender=Language)
