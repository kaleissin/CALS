from __future__ import absolute_import
from __future__ import unicode_literals

from django import template

register = template.Library()

@register.inclusion_tag('paginator.html', takes_context=True)
def paginator(context):
    return {
            'page_obj': context['page_obj'],
            'paginator': context['paginator'],
            'is_paginated': context['is_paginated'],
            'object_list': context['object_list'],
            }

