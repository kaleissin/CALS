# Create your views here.
from pprint import pprint, pformat

from cals import getLogger
LOG = getLogger('cals.tools')

from django.contrib.contenttypes.models import ContentType
from django.http import HttpResponseNotFound, HttpResponseForbidden
from django.shortcuts import render_to_response, get_object_or_404

from cals.models import *
from cals.forms import *

def get_languagefeature_descriptions(lang=None, feature=None, lf=None):
    assert (lang and feature) or lf
    if not lf:
        lf = get_object_or_404(LanguageFeature, language=lang, feature=feature)
    lf_type = ContentType.objects.get_for_model(lf)
    return Description.objects.filter(content_type=lf_type, object_id=lf.id).order_by('-last_modified')

