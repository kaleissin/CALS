from __future__ import absolute_import
from __future__ import unicode_literals

from django.shortcuts import get_object_or_404 as _get_object_or_404


def get_model_for_kwarg(model, kwarg_field='object_id', model_field='pk', **kwargs):
    return _get_object_or_404(model._default_manager, 
            **{model_field: kwargs.get(kwarg_field, None)})
