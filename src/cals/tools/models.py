from __future__ import absolute_import
from __future__ import unicode_literals

from django.conf import settings
from django.contrib.contenttypes.models import ContentType
from django.contrib.contenttypes.fields import GenericForeignKey, GenericRelation
from django.db import models
from django.db.models import Q
from django.db.models.query import QuerySet
from django.utils.html import strip_tags
from django.utils.timezone import now as tznow
from django.utils.encoding import python_2_unicode_compatible

from interlinears import leipzig
from cals import markup_as_restructuredtext

from cals.tools import next_id, uslugify

FREETEXT_TYPES = (
        ('rst', 'RestructuredText'),
        ('plaintext', 'plaintext'),
        )


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
class Freetext(models.Model):
    freetext = models.TextField(blank=True, null=True, default='')
    freetext_xhtml = models.TextField(null=True, editable=False)
    freetext_type = models.CharField(blank=True,max_length=20, choices=FREETEXT_TYPES, default='plaintext')
    freetext_link = models.URLField(blank=True, null=True)

    class Meta:
        abstract = True

    def __str__(self):
        return self.freetext_xhtml

    def save(self, *args, **kwargs):
        self.freetext_xhtml = self.make_xhtml()
        super(Freetext, self).save(*args, **kwargs)

    def make_xhtml(self):
        plaintext_fmt = '<pre class="plaintext">%s</pre>'
        if self.freetext_type == 'rst':
            try:
                freetext_xhtml = markup_as_restructuredtext(self.freetext)
            except leipzig.InterlinearError as e:
                freetext_xhtml = '<div class="error">%s<br />%s</div>' % (e.args[0], plaintext_fmt % self.freetext.strip())
        else:
            freetext = strip_tags(self.freetext)
            freetext_xhtml = plaintext_fmt % self.freetext.strip()
        return freetext_xhtml


class DescriptionManager(models.Manager):
    def get_queryset(self):
        return super(DescriptionManager, self).get_queryset().filter(current=True)


class Description(Freetext):
    last_modified = models.DateTimeField(default=tznow, editable=False)
    last_modified_by = models.ForeignKey(settings.AUTH_USER_MODEL, editable=False, blank=True, null=True, related_name='descriptions')
    current = models.BooleanField(default=True)

    content_type = models.ForeignKey(ContentType)
    object_id = models.PositiveIntegerField()
    content_object = GenericForeignKey()

    #objects = DescriptionManager()
    objects = models.Manager()
    archive = models.Manager()

    class Meta:
        #unique_together = ('version', 'content_type', 'object_id')
        db_table = 'cals_description'
        get_latest_by = 'last_modified'
        app_label = 'cals'

    def save(self, user=None, batch=False, using=None, *args, **kwargs):
        if using:
            desc_obj = Description.objects.using(using)
        else:
            desc_obj = Description.objects
        if not batch:
            self.id = next_id(self.__class__)
            self.last_modified = tznow()
            if user:
                self.last_modified_by = user
            desc_obj.filter(object_id=self.object_id).update(current=False)
            super(Description, self).save(force_insert=True, using=using, *args, **kwargs)
        else:
            super(Description, self).save(using=using, *args, **kwargs)

    def delete(self, using=None, *args, **kwargs):
        if using:
            desc_obj = Description.objects.using(using)
        else:
            desc_obj = Description.objects
        desc_obj.filter(object_id=self.object_id).update(current=False)

    def next_version(self):
        try:
            return Description.archive.filter(object_id=self.object_id, content_type=self.content_type,
                id__gt=self.id).order_by('last_modified')[0]
        except IndexError:
            return None

    def prev_version(self):
        try:
            return Description.archive.filter(object_id=self.object_id, content_type=self.content_type,
                id__lt=self.id).order_by('-last_modified')[0]
        except IndexError:
            return None

    def reset_current_to_latest(self):
        descriptions = Description.archive.filter(object_id=self.object_id).order_by('-last_modified')
        d = descriptions[0]
        d.current = True
        d.save(batch=True)

    def reformat_xhtml(self):
        self.freetext_xhtml = self.make_xhtml()
        self.save(batch=True)


class DescriptionMixin(object):

    descriptions = GenericRelation(Description)

    @property
    def description(self):
        self_type = ContentType.objects.get_for_model(self)
        try:
            return Description.archive.get(object_id=self.id, current=True, content_type=self_type)
        except Description.DoesNotExist:
            return None


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
