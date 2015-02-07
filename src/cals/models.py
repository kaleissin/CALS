
# -*- coding: UTF-8 -*-

import logging
_LOG = logging.getLogger(__name__)

from django.conf import settings
from django.db import models
from django.db.models.query import QuerySet
from django.utils.timezone import now as tznow

from cals import markup_as_restructuredtext

from cals.language.models import ExternalInfo

from cals.people.models import Profile

from cals.language.models import Language


def add_filter(queryset, **kwargs):
    return queryset.filter(**kwargs)

def add_exclude(queryset, **kwargs):
    return queryset.exclude(**kwargs)

def with_args(qs, keyword, *values):
    for v in values:
        qs = add_filter(qs, **{keyword: v})
    return qs

def without_args(qs, keyword, *values):
    for v in values:
        qs = add_exclude(qs, **{keyword: v})
    return qs

