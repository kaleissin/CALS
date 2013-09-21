import logging
_LOG = logging.getLogger(__name__)

from django.views.generic import ListView, DetailView
from django.http import HttpResponseRedirect
from django.shortcuts import get_object_or_404
from django.forms.models import modelformset_factory

from taggit.models import Tag

from nano.tools import render_page

from cals.language.models import LanguageName, Language, LanguageFamily

def _get_lang(*args, **kwargs):
    return get_object_or_404(Language, slug=kwargs.get('lang', None))

def change_languagenames(request, *args, **kwargs):
    lang = _get_lang(*args, **kwargs)
    queryset = LanguageName.objects.filter(
            language=lang).exclude(
            name=lang.name).exclude(
            name=lang.internal_name, internal=True).order_by('added')
    languagenameformset = modelformset_factory(LanguageName, can_delete=True, exclude=('language',), extra=3)
    if request.method == "POST":
        formset = languagenameformset(request.POST, request.FILES, queryset=queryset)
        if formset.is_valid():
            instances = formset.save(commit=False)
            for instance in instances:
                instance.language = lang
                instance.save()
            return HttpResponseRedirect(lang.get_absolute_url())
    else:
        formset = languagenameformset(queryset=queryset)
        #assert False, dir(formset)
    data = {'me': 'language',
            'formset': formset }
    return render_page(request, 'cals/language/name_form.html', data)


class LanguageMixin(object):
    def get_context_data(self, **kwargs):
        context = super(LanguageMixin, self).get_context_data(**kwargs)
        context['me'] = 'language'
        return context


class LanguageFamilyMixin(LanguageMixin):
    queryset = LanguageFamily.objects.all()


class ListLanguageFamilyView(LanguageFamilyMixin, ListView):
    pass
list_languagefamilies = ListLanguageFamilyView.as_view()


class ShowLanguageFamilyView(LanguageFamilyMixin, DetailView):
    pass
show_languagefamilies = ShowLanguageFamilyView.as_view()


class ListTagsView(LanguageMixin, ListView):
    queryset = Tag.objects.all()
    template_name = 'tagging/tag_list.html'
list_languagetags = ListTagsView.as_view()
