# -*- coding: utf-8 -*-
# vim: set fileencoding=utf-8 :

from __future__ import absolute_import
from __future__ import unicode_literals

from datetime import datetime, timedelta
from random import choice

from django import template
from django.conf import settings
from django.utils.timezone import now as tznow, utc

import logging
_LOG = logging.getLogger(__name__)

from translations.models import Translation

import os

STATIC_URL = ''
if settings.STATIC_URL:
    STATIC_URL = settings.STATIC_URL

register = template.Library()


@register.simple_tag
def seasons_greetings():
    translation = choice(tuple(Translation.objects.filter(exercise__slug='merry-christmas')))
    url = '<a href="/language/%s/">%s</a>' % (translation.language.slug, translation.translation)
    return url

@register.simple_tag
def happy_new_year():
    translation = choice(tuple(Translation.objects.filter(exercise__slug='happy-new-year')))
    url = '<a href="/language/%s/">%s</a>' % (translation.language.slug, translation.translation)
    return url

@register.filter
def special_date(special):
    now = tznow()

    christmas_start = datetime(now.year, 12, 24, 0,0,0, tzinfo=utc)
    christmas_end = christmas_start + timedelta(days=13)

    new_years_eve_start = datetime(now.year, 12, 31, 18,0,0, tzinfo=utc)
    new_years_eve_end = datetime(now.year, 12, 31, 23,59,59, tzinfo=utc)

    new_years_start = datetime(now.year, 1, 1, 0,0,0, tzinfo=utc)
    new_years_end = datetime(now.year, 1, 1, 23,59,59, tzinfo=utc)

    special_dates = {
        (christmas_start, christmas_end): 'christmas',
        (new_years_eve_start, new_years_eve_end): 'new_years_eve',
        (new_years_start, new_years_end): 'new_year',
    }
    outdates = []
    for begin, end in sorted(special_dates.keys()):
        if begin <= now <= end:
            outdates.append(special_dates[(begin, end)])
    if outdates and special in outdates:
        return True
    return False

@register.simple_tag
def between(comparee, cmp1, cmp2):
    return cmp1 <= comparee <= cmp2
between.is_safe = True

