# -*- coding: UTF-8 -*-

from __future__ import absolute_import
from __future__ import unicode_literals

import logging
_LOG = logging.getLogger(__name__)

import django.dispatch
from django.conf import settings
from django.db import models
from django.db.models.query import QuerySet
from django.utils.encoding import smart_text
from django.utils.encoding import python_2_unicode_compatible
from django.utils.timezone import now as tznow

from taggit.managers import TaggableManager

from cals import markup_as_restructuredtext
from cals.tools import uslugify, asciify

from cals.tools.models import FREETEXT_TYPES, DescriptionMixin

language_hidden = django.dispatch.Signal(providing_args=["languages"])


class LangtypeQuerySet(QuerySet):
    def conlangs(self):
        return self.exclude(natlang=True)

    def natlangs(self):
        return self.filter(natlang=True)


class DefaultLanguageManager(models.Manager):
    use_for_related_fields = True
    def get_queryset(self):
        return LangtypeQuerySet(self.model).filter(visible=True)

    def conlangs(self):
        return self.get_queryset().conlangs()

    def natlangs(self):
        return self.get_queryset().natlangs()

    def get_by_natural_key(self, slug):
        return self.get(slug=slug)


class NaturalLanguageManager(models.Manager):
    def get_queryset(self):
        return super(NaturalLanguageManager, self).get_queryset().filter(natlang=True)


class UnorderedTreeMixin(models.Model):
    part_of = models.ForeignKey('self', blank=True, null=True, default=None)
    path = models.CharField(max_length=255, blank=True, default='')

    _sep = '/'

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
        return str(self.path).count(self._sep)

    def roots(self):
        return self._default_manager.filter(part_of__isnull=True)

    def get_path(self):
        return [self._default_manager.get(id=p) for p in str(self.path).split(self._sep) if p]

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


@python_2_unicode_compatible
class LanguageFamily(UnorderedTreeMixin):
    name = models.CharField(max_length=64)
    slug = models.SlugField(editable=False, blank=True, null=True)

    objects = models.Manager()

    class Meta:
        db_table = 'cals_languagefamily'
        verbose_name_plural = 'language families'
        ordering = ('name',)
        app_label = 'cals'

    def __str__(self):
        return self.name

    def save(self, *args, **kwargs):
        self.slug = uslugify(self.name)

        super(LanguageFamily, self).save(*args, **kwargs)


@python_2_unicode_compatible
class Language(models.Model):
    name = models.CharField('External name', max_length=64, 
            help_text='Anglified name, safe for computing. ASCII!')
    internal_name = models.CharField('Internal name', max_length=64,
            blank=True,
            help_text='What the speakers call their language. All of unicode OK')
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
    tags = TaggableManager(blank=True)
    public = models.BooleanField('Editable by all', default=True,
            help_text="""If yes/on, all logged in may edit. If no/off, only the
            manager and editors may edit.""")
    added_by = models.ForeignKey(settings.AUTH_USER_MODEL,
            editable=False,
            blank=True,
            null=True,
            related_name='languages')
    manager = models.ForeignKey(settings.AUTH_USER_MODEL,
            blank=True,
            null=True,
            related_name='manages',
            help_text="""The person who controls who gets to
            change the description of this language. This makes 
            it possible to hand a language over to another person.""")
    editors = models.ManyToManyField(settings.AUTH_USER_MODEL, blank=True,
            related_name='edits',
            help_text="""People who get to change the description of this language.""")
    created = models.DateTimeField(default=tznow)
    last_modified = models.DateTimeField(blank=True, null=True, editable=False, default=tznow)
    last_modified_by = models.ForeignKey(settings.AUTH_USER_MODEL,
            editable=False,
            blank=True,
            null=True,
            related_name='languages_modified')

    try:
        from nano.blog.models import Entry
        blogentries = models.ManyToManyField(Entry,
                blank=True, related_name='languages')
    except ImportError:
        # nano.blog not in use
        pass

    # Managers
    objects = DefaultLanguageManager()
    natlangs = NaturalLanguageManager()
    all_langs = models.Manager()

    class Meta:
        ordering = ['name']
        db_table = 'cals_language'
        get_latest_by = 'last_modified'
        app_label = 'cals'

    def __str__(self):
        return self.name

    def save(self, user=None, solo=True, *args, **kwargs):
        now = tznow()
        # New lang
        if not self.id and user:
            self.added_by = user
            self.manager = user
        if solo:
            self.last_modified = now
            if user:
                self.last_modified_by = user
            else:
                self.last_modified_by = self.manager
        if not self.internal_name:
            self.internal_name = self.name
            self.name = asciify(self.name)
        self.slug = self.get_slug()

        if not self.manager:
            self.manager = self.added_by or user
        # XXX Cannot set average score here as there would be an
        # import-loop
        super(Language, self).save(*args, **kwargs)

        self.save_langnames(now=now)

    def natural_key(self):
        return self.slug

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
            now = tznow()
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
        from cals.people.models import Profile
        if not isinstance(profile, Profile):
            profile = profile.profile
        if self.manager == profile.user:
            return True
        if len(self.editors.filter(id=profile.user.id)):
            return True
        return False

    def get_slug(self):
        return uslugify(self.name)

    def get_name(self):
        if self.internal_name:
            return self.internal_name
        return self.name

    def get_infodensity(self):
        from cals.feature.models import Feature
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
        q = uslugify(q)
        return self.get_queryset().filter(slug__istartswith=q)

    def find_anywhere(self, q):
        q = uslugify(q)
        return self.get_queryset().filter(slug__icontains=q)

    def find(self, q, anywhere=False):
        if anywhere:
            return self.find_anywhere(q)
        else:
            return self.find_prefix(q)


@python_2_unicode_compatible
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
        app_label = 'cals'

    def save(self, *args, **kwargs):
        self.slug = uslugify(smart_text(self.name))
        if not self.added:
            self.added = tznow()
        super(LanguageName, self).save(*args, **kwargs)

    def __str__(self):
        return self.name

    def is_current(self):
        return (self.name == self.language.name) or (self.name == self.language.internal_name)


@python_2_unicode_compatible
class WALSCode(models.Model):
    URI_FORMAT = 'http://wals.info/languoid/lect/wals_code_{}'
    language = models.OneToOneField(Language, primary_key=True, related_name="walscode")
    walscode = models.CharField(max_length=3, unique=True)

    class Meta:
        db_table = 'cals_walscodes'
        app_label = 'cals'

    def __str__(self):
        return self.walscode

    def natural_key(self):
        return self.walscode

    def uri(self):
        return self.URI_FORMAT.format(str(self))


@python_2_unicode_compatible
class ISO639_3(models.Model):
    URI_FORMAT = 'https://www.ethnologue.com/language/{}'
    language = models.OneToOneField(Language, primary_key=True, related_name="iso639_3")
    iso639_3 = models.CharField(max_length=3, unique=True)

    class Meta:
        db_table = 'cals_iso639_3'
        app_label = 'cals'
        verbose_name = 'ISO 639-3'
        verbose_name_plural = 'ISO 639-3'

    def __str__(self):
        return self.iso639_3

    def natural_key(self):
        return self.iso639_3

    def uri(self):
        return self.URI_FORMAT.format(str(self))


@python_2_unicode_compatible
class Glottocode(models.Model):
    URI_FORMAT = 'http://glottolog.org/resource/languoid/id/{}'
    language = models.OneToOneField(Language, primary_key=True, related_name="glottocode")
    glottocode = models.CharField(max_length=8, unique=True)

    class Meta:
        db_table = 'cals_glottocode'
        app_label = 'cals'

    def __str__(self):
        return self.glottocode

    def natural_key(self):
        return self.glottocode

    def uri(self):
        return self.URI_FORMAT.format(str(self))


@python_2_unicode_compatible
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

    class Meta:
        app_label = 'cals'

    def __str__(self):
        return "%s %s: on request: %s, link: %s" % (self.language,
                self.category, self.on_request, self.link or 'No')
