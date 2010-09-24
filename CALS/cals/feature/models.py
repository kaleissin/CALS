
from django.contrib.auth.models import User
from django.db import models
from django.db.models.query import QuerySet

from tagging.fields import TagField

from cals.tools.models import DescriptionMixin

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

class CategoryManager(ActivePassiveManager):

    def get_by_natural_key(self, name):
        return self.get(name=name)

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
        app_label = 'cals'

    def __unicode__(self):
        return self.name

    def natural_key(self):
        return self.name

class FeatureManager(ActivePassiveManager):

    def get_by_natural_key(self, category, name):
        return self.get(category__name=category, name=name)

class Feature(models.Model, DescriptionMixin):
    MAX_WALS_FEATURE = 142
    name = models.CharField(max_length=96, unique=True) # Longest faeture-name... 93 chars!!
    category = models.ForeignKey(Category)
    tags = TagField()
    wals = models.BooleanField(default=False, editable=False)
    overrides = models.ForeignKey('self', blank=True, null=True)
    active = models.BooleanField(default=False, editable=False)
    added_by = models.ForeignKey(User, editable=False, null=True)

    objects = FeatureManager()
    active_objects = ActiveManager()
    passive_objects = PassiveManager()

    class Meta:
        unique_together = ('id', 'name', 'category')
        ordering = ['id']
        #order_with_respect_to = 'category'
        db_table = 'cals_feature'
        app_label = 'cals'

    def __unicode__(self):
        return self.name

    def natural_key(self):
        return (self.category.name, self.name)

class FeatureValueManager(models.Manager):
    def get_by_natural_key(self, feature, name):
        return self.get(feature__name=feature, name=name)

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
        app_label = 'cals'

    def __unicode__(self):
        return self.name

    def natural_key(self):
        return (self.feature.name, self.name)

# END Features
