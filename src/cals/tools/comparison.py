from __future__ import absolute_import
from __future__ import unicode_literals
import logging
_LOG = logging.getLogger(__name__)

from django.http import HttpResponseRedirect

from cals.forms import CompareTwoForm, CompareTwoFeaturesForm


def _generate_comparison_type(comparison_type):
    same = None
    different = None
    if comparison_type == 'different':
        same = False
        different = True
    elif comparison_type == 'same':
        same = True
        different = False
    return same, different


def _generate_comparison_url(langs, comparison_type=''):
    redirect_to = '/language/%s/' % '+'.join(langs)
    if comparison_type in ('same', 'different'):
        redirect_to += comparison_type
    return redirect_to


def _compare(request, langs, comparison_type=None):
    # langs should be a non-string iterator/generator over strings
    if not len(langs):
        raise ValueError('No languages given to compare')
    langs = tuple(langs)

    # Get existing comparison-type
    comparison_type = comparison_type or request.GET.get('compare', None)
    same, different = _generate_comparison_type(comparison_type)

    cform = CompareTwoForm(data=request.POST)
    if cform.is_valid():
        lang2 = cform.cleaned_data['lang2']
        redirect_to = _generate_comparison_url(langs + (lang2.slug,), comparison_type)
    else:
        redirect_to = _generate_comparison_url(langs, comparison_type)
    return HttpResponseRedirect(redirect_to)
