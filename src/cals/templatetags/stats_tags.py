# -*- coding: utf-8 -*-
# vim: set fileencoding=utf-8 :

from __future__ import absolute_import
from __future__ import unicode_literals

from django import template

register = template.Library()

@register.inclusion_tag('statistics/milestone_user.html')
def milestone_user(user, count):
    return {'user': user, 'count': count}

@register.inclusion_tag('statistics/milestone_language.html')
def milestone_language(language, count):
    return {'language': language, 'count': count}
