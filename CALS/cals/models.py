
# -*- coding: UTF-8 -*-

import unicodedata
import datetime as dt
from datetime import datetime

from cals import getLogger
LOG = getLogger('cals.models')

from textile import textile

from django.contrib.auth.models import User
from django.contrib.contenttypes.models import ContentType
from django.contrib.contenttypes import generic
#from django.contrib.markup.templatetags.markup import textile
from django.contrib.markup.templatetags.markup import restructuredtext, markdown
from django.db import models, connection
from django.template.defaultfilters import slugify
from django.utils.html import strip_tags
from django.utils.translation import ugettext_lazy as _

import tagging
from tagging.fields import TagField
from countries.models import Country

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

FREETEXT_TYPES = (
        ('textile', 'textile'),
        ('rest', 'RestructuredText'),
        ('plaintext', 'plaintext'),
        )

def asciify(string):
    return unicodedata.normalize('NFKD', string).encode('ascii', 'ignore')

def next_id(model):
    # postgres only
    table_name, pk_name = model._meta.db_table, model._meta.pk.column
    fetch_id = """SELECT nextval('\"%s_%s_seq\"')""" % (table_name, pk_name)
    cursor = connection.cursor()
    #cursor.execute(fetch_id, (table_name, pk_name))
    cursor.execute(fetch_id)
    return cursor.fetchone()[0]

class Freetext(models.Model):
    freetext = models.TextField(blank=True, null=True, default='')
    freetext_xhtml = models.TextField(null=True, editable=False)
    freetext_type = models.CharField(blank=True,max_length=20, choices=FREETEXT_TYPES, default='plaintext')
    freetext_link = models.URLField(blank=True, null=True)

    class Meta:
        abstract = True

    def __unicode__(self):
        return unicode(self.freetext_xhtml, 'UTF-8')

    def save(self, *args, **kwargs):
        self.freetext = strip_tags(self.freetext)
        if self.freetext_type == 'textile':
            self.freetext_xhtml = textile(self.freetext.decode('utf8'), head_offset=1, validate=0, sanitize=0)
#             self.freetext_xhtml = textile(self.freetext.encode('utf8'), head_offset=1,
#                     validate=0, sanitize=0, encoding='utf-8', output='utf-8').encode('UTF-8')
        elif self.freetext_type == 'rest':
            self.freetext_xhtml = restructuredtext(self.freetext)
        else:
            self.freetext_xhtml = u'<pre>'+self.freetext.strip()+u'</pre>'
        super(Freetext, self).save(*args, **kwargs)

class Description(Freetext):
    version = models.PositiveIntegerField(default=0)
    added = models.DateTimeField(default=datetime.now)
    added_by = models.ForeignKey(User,editable=False,blank=True,null=True, related_name='descriptions')

    content_type = models.ForeignKey(ContentType)
    object_id = models.PositiveIntegerField()
    content_object = generic.GenericForeignKey()

    class Meta:
        unique_together = ('version', 'content_type', 'object_id')
        db_table = 'cals_description'

    def save(self, user=None, *args, **kwargs):
        self.version += 1
        if self.id:
            self.id = next_id(Description)
        if user:
            self.added_by = user
        super(Description, self).save(*args, **kwargs)

class Category(models.Model):
    name = models.CharField(max_length=20, unique=True)

    class Meta:
        ordering = ['id']
        verbose_name_plural = 'categories'
        db_table = 'cals_category'

    def __unicode__(self):
        return self.name

class Feature(models.Model):
    MAX_WALS_FEATURE = 142
    name = models.CharField(max_length=96, unique=True) # Longest faeture-name... 93 chars!!
    category = models.ForeignKey(Category)
    tags = TagField()
    wals = models.BooleanField(default=False, editable=False)
    overrides = models.ForeignKey('self', blank=True, null=True)
    description = models.TextField(blank=True, null=True)
    description_xhtml = models.TextField(blank=True, null=True, editable=False)
    description_type = models.CharField(blank=True,max_length=20, choices=FREETEXT_TYPES)
    description_link = models.URLField(blank=True, null=True)

    descriptions = generic.GenericRelation(Description)

    class Meta:
        unique_together = ('id', 'name', 'category')
        ordering = ['id']
        #order_with_respect_to = 'category'
        db_table = 'cals_feature'

    def __unicode__(self):
        return self.name

#     def save(self):
#         if self.description:
#             if self.description_type in ('textile', ''):
#                 xhtml = textile(self.description,
#                         head_offset=1, validate=0, sanitize=0,
#                         output='utf-8')
#             if xhtml != self.description_xhtml:
#                 self.description_xhtml = xhtml
#         super(Feature, self).save()

class FeatureValueManager(models.Manager):
    def _value_counts(self):
        return self.extra(select={
            'value_count': 'SELECT count(*) FROM "cals_languagefeature" AS lf WHERE lf.value_id = id GROUP BY id'
            #'count': 'SELECT count(lf.value_id) FROM "cals_languagefeature" AS lf WHERE lf.value_id = id GROUP BY id'
            })

    def value_counts(self):
        return self._value_counts().order_by('count')

class FeatureValue(models.Model):
    feature = models.ForeignKey(Feature)
    name = models.CharField(max_length=64)
    position = models.IntegerField(null=True)#, editable=False)

    descriptions = generic.GenericRelation(Description)
    #objects = FeatureValueManager()

    class Meta:
        unique_together = ('feature', 'name')
        ordering = ['feature__id', 'position']
        #order_with_respect_to = 'feature'
        db_table = 'cals_featurevalue'

    def __unicode__(self):
        return self.name

class Profile(models.Model):
# TODO: change date-format on profile-page, needs new date-filter
#     CHOICE_DATE = datetime(2008, 5, 1, 14, 0, 0, 7, UTC())
#     DATE_FORMAT_CHOICES = (
#             ('Y-m-d H:i O', CHOICE_DATE.isoformat),
#             ('Y-m-d H:i O', CHOICE_DATE.),
#             ('r', ''),
#             )
    user = models.ForeignKey(User, unique=True)
    # Denormalization of django.contrib.auth.models.User - allows public
    # backup of database without exposing passwords and email-addresses
    username = models.CharField(max_length=30, unique=True, editable=False)
    display_name = models.CharField(max_length=32)
    show_username = models.NullBooleanField('Always show username',
            help_text="Show username everywhere, even if personal name "
            "or familyname have been set.")
    homepage = models.URLField(blank=True,null=True)
    homepage_title = models.CharField(max_length=64, blank=True)
#     help_text="""If you're on twitter and want your """
#             """latest tweet to be visible, fill this in """
#             """with your twitter-username"""
#     )
    country = models.ForeignKey(Country, null=True, blank=True)
    latitude = models.FloatField(blank=True,null=True)
    longitude = models.FloatField(blank=True,null=True)
    altitude = models.IntegerField(blank=True,null=True, default=0)
    date_format = models.CharField(max_length=16, default="Y-m-d H:i O")
    is_visible = models.BooleanField(default=True)

    class Meta:
        ordering = ('display_name',)
        db_table = 'cals_profile'

    def __unicode__(self):
        return self.display_name

    def save(self, *args, **kwargs):
        self.username = self.user.username
        if not self.show_username:
            full_name = '%s %s' % (self.user.first_name.strip(), self.user.last_name.strip())
            self.display_name = full_name.strip() or self.user.username
        super(Profile, self).save(*args, **kwargs)

    def get_absolute_url(self):
        return "/people/%s/" % self.id 

#     def twittername(self):
#         twitteraccounts = self.user.web20.filter(type='Twitter')
#         if twitteraccounts:
            

#     def get_absolute_url(self):
#         return ('profiles_profile_detail', (), { 'username': self.user.username })
#     get_absolute_url = models.permalink(get_absolute_url)

class EsperantoBackgroundManager(models.Manager):
    # For Rick Harrison
    def get_query_set(self):
        esperanto = Language.objects.get(slug='esperanto')
        return super(EsperantoBackgroundManager,
                self).get_query_set().filter(background_translated_from__translated_to=esperanto)

class Language(models.Model):
    name = models.CharField('External name', max_length=64, 
            help_text=u'Anglified name, safe for computing. ASCII!')
    internal_name = models.CharField('Internal name', max_length=64,
            blank=True,
            help_text=u'What the speakers call their language. All of unicode OK')
    slug = models.SlugField(max_length=64, editable=False, blank=True, null=True)
    author = models.CharField(max_length=128)
    homepage = models.URLField(null=True, blank=True)
    background = models.CharField(max_length=256, blank=True,
            help_text="""A short summary of the history/background of
            your language. 4 lines (256 letters) inc. formatting, no HTML.""")
    background_type = models.CharField(blank=True, max_length=20, choices=FREETEXT_TYPES)
    from_earth = models.NullBooleanField(null=True, blank=True,
            help_text="""Example: Klingon and Barsoomian (from Mars!) would set 'No' here, while
            Brithenig and Esperanto would set 'Yes'. As for Sindarin, it
            depends on whether you consider Arda to be the Earth""")
#     greeting3 = models.CharField(max_length=64, blank=True,
#             db_column='greeting3')
    greeting = models.ForeignKey('Translation', blank=True, null=True,
            editable=False, related_name='languagegreeting')
    vocabulary_size = models.PositiveIntegerField(null=True, blank=True,
            help_text="Estimated vocabulary size")
    # Denormalization, real-time average-score is expensive
    average_score = models.IntegerField(editable=False, default=0)
    # Denormalization, real-time num-of-features can't be sorted on
    num_features = models.IntegerField(editable=False, default=0)
    # Denormalization, real-time num-of-features can't be sorted on
    num_avg_features = models.IntegerField(editable=False, default=0)
    tags = TagField(help_text="Separate tags with commas or spaces")
    public = models.BooleanField('Editable by all', default=True,
            help_text="""If yes/on, all logged in may edit. If no/off, only the
            manager and editors may edit.""")
    added_by = models.ForeignKey(User,editable=False, blank=True, null=True, related_name='languages')
    manager = models.ForeignKey(Profile,
            blank=True,
            null=True,
            related_name='manages',
            help_text=u"""The person who gets to change the language. This
            makes it possible to hand a language over to another
            person.""")
    editors = models.ManyToManyField(Profile, blank=True, null=True, related_name='edits')
    created = models.DateTimeField(auto_now_add=True)
    last_modified = models.DateTimeField(blank=True, null=True,
            editable=False, default=datetime.now) #auto_now=True)

    # Managers
    objects = models.Manager()
    esperanto_background = EsperantoBackgroundManager()

    class Meta:
        ordering = ['name']
        db_table = 'cals_language'

    def __unicode__(self):
        return self.name

    def save(self, user=None, solo=True, *args, **kwargs):
        # New lang
        if not self.id and user:
            self.added_by = user
            self.manager = user
        if solo:
            self.last_modified = datetime.now()
        if not self.internal_name:
            self.internal_name = self.name
            self.name = asciify(self.name)
        self.slug = slugify(self.name)
        if not self.manager:
            self.manager = self.added_by.get_profile() or user.get_profile()
        # XXX Cannot set average score here as there would be an
        # import-loop
        super(Language, self).save(*args, **kwargs)
    
    #@permalink
    def get_absolute_url(self):
        return "/language/%s/" % self.slug 
    #    return ('cals.views.show_language', [str(self.id)]) 

    def set_average_score(self):
        if not self.num_features:
            self.average_score = 0
        else:
            self.average_score = int(self.num_avg_features / float(self.num_features) * 100)

    def set_num_features(self):
        self.num_features = LanguageFeature.objects.filter(language=self).count()

    def get_name(self):
        if self.internal_name:
            return self.internal_name
        return self.name

    def get_background_translation(self, lang):
        return self.background_translated_from.filter(translated_to=lang)

    def get_esperanto_background(self):
        esperanto = Language.objects.get(slug='esperanto')
        return self.get_background_translation(esperanto)

    def has_background_translation(self, lang):
        return self.get_background_translation(lang).count()

    def has_esperanto_background(self):
        esperanto = Language.objects.get(slug='esperanto')
        return self.has_background_translation(esperanto)

class LanguageFeature(models.Model):
    language = models.ForeignKey(Language, related_name='features')
    feature = models.ForeignKey(Feature, related_name='languages')
    value = models.ForeignKey(FeatureValue) #, related_name='languages')

    descriptions = generic.GenericRelation(Description)

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

class Web20Account(models.Model):
    WEB20_CHOICES = (
            ('AIM', 'AIM'),
            ('CONLANG-L', 'CONLANG-L'),
            ('Facebook', 'Facebook'),
            ('Flickr', 'Flickr'),
            ('FrathWiki', 'FrathWiki'),
            ('GTalk', 'GTalk'),
            ('ICQ', 'ICQ'),
            ('Jabber', 'Jabber'),
            ('LiveJournal', 'LiveJournal'),
            ('MSN', 'MSN'),
            ('MySpace', 'MySpace'),
            ('Twitter', 'Twitter'),
            ('WikiPedia', 'WikiPedia'),
            ('YIM', 'YIM'),
            ('ZBB', 'ZBB'),
            )

    user = models.ForeignKey(User, related_name='web20')
    username = models.CharField(max_length=64)
    place = models.CharField(max_length=20, choices=WEB20_CHOICES)

    class Meta:
        db_table = 'cals_web20account'

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

    def __unicode__(self):
        return self.name

    def save(self, user=None, *args, **kwargs):
        if not self.id:
            self.slug = slugify(self.name)
            if user:
                self.added_by = user
        self.added = datetime.now()
        super(TranslationExercise, self).save(*args, **kwargs)

# class EsperantoBackgroundManager(models.Manager):
#     # For Rick Harrison
#     def get_query_set(self):
#         esperanto = Language.objects.get(slug='esperanto')
#         return super(EsperantoBackgroundManager,
#                 self).get_query_set().filter(background_translated_from__translated_to=esperanto)

class Translation(models.Model):
    translation = models.TextField()
    exercise = models.ForeignKey(TranslationExercise, related_name='translations')
    language = models.ForeignKey(Language, related_name='translations')
    translator = models.ForeignKey(User, related_name='translations')
    added = models.DateTimeField(default=datetime.now, editable=False)
    last_modified = models.DateTimeField(default=datetime.now, editable=False)

    class Meta:
        db_table = 'cals_translation'

    def __unicode__(self):
        return self.translation

    def save(self, user=None, *args, **kwargs):
        if not self.id and user:
            self.translator = user
        self.last_modified = datetime.now()
        super(Translation, self).save(*args, **kwargs)

class BackgroundTranslation(models.Model):
    translation = models.CharField(max_length=512, blank=True,
            help_text="""A translation of the short summary of the history/background of
            a language. 8 lines (512 letters) inc. formatting, no HTML.
            (It is quite common that a translation is longer than
            the original.)""")
    translated_from = models.ForeignKey(Language,
            related_name='background_translated_from')
    translated_to = models.ForeignKey(Language,
            related_name='background_translated_to')
    translator = models.ForeignKey(User, related_name='background_translations')
    added = models.DateTimeField(default=datetime.now, editable=False)
    last_modified = models.DateTimeField(default=datetime.now, editable=False)

    class Meta:
        db_table = 'cals_backgroundtranslation'

    def __unicode__(self):
        return self.translation

    def save(self, user=None, *args, **kwargs):
        if not self.id and user:
            self.translator = user
        self.last_modified = datetime.now()
        super(Translation, self).save(*args, **kwargs)

