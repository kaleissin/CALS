import logging
_LOG = logging.getLogger(__name__)

from django.views.generic import ListView, DetailView
from django.http import HttpResponseRedirect
from django.shortcuts import get_object_or_404, render
from django.forms.models import modelformset_factory

from taggit.models import Tag

from cals.tools.auth import may_edit_lang
from cals.tools.comparison import _compare
from cals.forms import CompareTwoForm

from cals.language.models import LanguageName, Language, LanguageFamily
from cals.languagefeature.models import LanguageFeature
from cals.feature.models import Category


def _get_lang(all=False, *args, **kwargs):
    if all:
        return get_object_or_404(Language.all_langs, slug=kwargs.get('lang', None))
    return get_object_or_404(Language, slug=kwargs.get('lang', None))

def change_languagenames(request, *args, **kwargs):
    lang = _get_lang(all=False, *args, **kwargs)
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
    return render(request, 'cals/language/name_form.html', data)


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

def show_language(request, *args, **kwargs):
    me = 'language'
    lang = _get_lang(all=True, *args, **kwargs)
    may_edit, (is_admin, is_manager) = may_edit_lang(request.user, lang)

    # Nav for comparisons
    cform = CompareTwoForm()
    if request.method == 'POST':
        cform = CompareTwoForm(data=request.POST)
        if cform.is_valid():
            return _compare(request, (lang.slug,))

    data = {'object': lang,
            'me': me,
            'cform': cform,
            'may_edit': may_edit,
    }
    return render(request, 'cals/language/overview.html', data)

def show_features_for_language(request, *args, **kwargs):
    me = 'language'
    lang = _get_lang(all=True, *args, **kwargs)
    may_edit, (is_admin, is_manager) = may_edit_lang(request.user, lang)
    categories = Category.objects.all().select_related().order_by('id')
    cats = []
    for category in categories:
        try:
            lf = LanguageFeature.objects.filter(language=lang, feature__category=category).order_by('feature__id')
        except LanguageFeature.DoesNotExist:
            continue
        if lf:
            cats.append({'name': category.name, 'features': lf})

    # Nav for comparisons
    cform = CompareTwoForm()
    if request.method == 'POST':
        cform = CompareTwoForm(data=request.POST)
        if cform.is_valid():
            return _compare(request, (lang.slug,))

    data = {'object': lang,
            'categories': cats,
            'me': me,
            'cform': cform,
            'may_edit': may_edit,
    }
    return render(request, 'cals/language/features_overview.html', data)
