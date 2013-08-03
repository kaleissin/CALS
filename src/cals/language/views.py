import logging
_LOG = logging.getLogger(__name__)

from django.http import HttpResponseRedirect, HttpResponseNotFound, HttpResponseForbidden
from django.shortcuts import get_object_or_404
from django.forms.models import modelformset_factory

from nano.tools import render_page

from cals.models import LanguageName, Language

def _get_lang(*args, **kwargs):
    return get_object_or_404(Language, slug=kwargs.get('lang', None))

def change_languagenames(request, *args, **kwargs):
    lang = _get_lang(*args, **kwargs)
    queryset = LanguageName.objects.filter(
            language=lang).exclude(
            name=lang.name).exclude(
            name=lang.internal_name, internal=True).order_by('added')
    LanguageNameFormset = modelformset_factory(LanguageName, can_delete=True, exclude=('language',), extra=3)
    if request.method == "POST":
        formset = LanguageNameFormset(request.POST, request.FILES, queryset=queryset)
        if formset.is_valid():
            instances = formset.save(commit=False)
            for instance in instances:
                instance.language = lang
                instance.save()
            return HttpResponseRedirect(lang.get_absolute_url())
    else:
        formset = LanguageNameFormset(queryset=queryset)
        #assert False, dir(formset)
    data = {'me': 'language',
        'formset': formset }
    return render_page(request, 'cals/language/name_form.html', data)
