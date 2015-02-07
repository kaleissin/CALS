from django.conf import settings
from django.contrib.auth.decorators import login_required
from django.http import HttpResponseRedirect, Http404
from django.core.exceptions import PermissionDenied
from django.shortcuts import get_object_or_404, render
from django.views.generic import ListView, DetailView
from django.views.generic import DeleteView, UpdateView, CreateView
from django.contrib.contenttypes.models import ContentType
from django.contrib.auth import get_user_model

import logging
_LOG = logging.getLogger(__name__)

from cals.views import langs_for_user
from cals.models import Language

from translations.models import Translation, TranslationExercise
from translations.forms import TranslationForm
from translations.tools import get_model_for_kwarg

def get_translationexercise(**kwargs):
    return get_model_for_kwarg(TranslationExercise, 'exercise', 'slug', **kwargs)

def get_language(**kwargs):
    return get_model_for_kwarg(Language, 'language', 'slug', **kwargs)

def get_user(**kwargs):
    return get_model_for_kwarg(settings.AUTH_USER_MODEL, 'translator', 'username', **kwargs)


class ListLanguageTranslationView(ListView):
    """List all translations for a specific language.

    Specific translations is reached by show_translation_for_language().
    """
    template_name = 'translations/languagetranslation_list.html'

    def get_queryset(self):
        lang = get_language(**self.kwargs)
        trans = lang.translations.exclude(translation__isnull=True).exclude(translation='')
        exercises = TranslationExercise.objects.exclude(translations__language=lang)
        if self.request.user.is_authenticated():
            exercises = exercises.exclude(translations__translator=self.request.user)
        self.exercises = exercises
        self.lang = lang
        return trans

    def get_context_data(self, **kwargs):
        context = super(ListLanguageTranslationView, self).get_context_data(**kwargs)
        context['me'] = 'translation'
        context['lang'] = self.lang
        context['exercises'] = self.exercises
        return context
show_languagetranslations = ListLanguageTranslationView.as_view()


def list_translation_for_language(request, *args, **kwargs):
    """List all translations of a specific exercise for a specific language.

    Specific translations is reached by show_translation_for_language().
    """

    me = 'translation'
    template = 'translations/list_translation_for_language.html'
    lang = get_language(**kwargs)
    exercise = get_translationexercise(**kwargs)
    trans = Translation.objects.filter(language=lang, exercise=exercise)
    data = {'exercise': exercise,
            'lang': lang,
            'object_list': trans,
            'doop': 'derp',
            'me': me,}
    return render(request, template, data)


class ListAllTranslationView(ListView):
    """List all translations."""
    queryset = TranslationExercise.objects.all()
    template_name = 'translations/translation_list.html'

    def get_context_data(self, **kwargs):
        context = super(ListAllTranslationView, self).get_context_data(**kwargs)
        context['me'] = 'translation'
        context['exercises'] = self.queryset
        return context
list_all_translations = ListAllTranslationView.as_view()


class ListTranslationsForExercise(ListView):
    """List all translations for a specific exercise, and provide links
    to add more translations.
    """

    template_name = 'translations/translationexercise_list.html'

    def get_queryset(self):
        self.exercise = get_translationexercise(**self.kwargs)
        queryset = (self.exercise.translations
            .filter(language__visible=True)
            .exclude(translation__isnull=True)
            .exclude(translation='')
            .order_by('language')
        )
        return queryset

    def get_context_data(self, **kwargs):
        context = super(ListTranslationsForExercise, self).get_context_data(**kwargs)
        context['me'] = 'translation'
        natlangs, other_conlangs, own_conlangs, favelangs = None, None, None, None
        user = self.request.user
        if user.is_authenticated():
            ctl = ContentType.objects.get_for_model(Language)
            favelangs = [m.content_object
                    for m in user.marks.filter(marktype__slug='fave', content_type=ctl)]
            natlangs = Language.objects.natlangs()
            conlangs = Language.objects.conlangs()
            own_conlangs = langs_for_user(user)
            other_conlangs = conlangs.exclude(id__in=[l.id for l in list(own_conlangs)+favelangs])
        context['natlangs'] = natlangs
        context['other_conlangs'] = other_conlangs
        context['own_conlangs'] = own_conlangs
        context['favorite_langs'] = favelangs
        context['exercise'] = self.exercise
        return context
show_translationexercise = ListTranslationsForExercise.as_view()


class CreateTranslationView(CreateView):
    """Add a specific translation by a specific user for a specific
    language."""
    model = Translation
    template_name = 'translations/languagetranslation_form.html'
    form_class = TranslationForm

    def get_success_url(self):
        return self.object.get_absolute_url()

    def get_context_data(self, **context):
        context = super(CreateTranslationView, self).get_context_data(**context)
        new_context = {
            'me': 'translation',
            'exercise': get_translationexercise(**self.kwargs),
            'language': get_language(**self.kwargs),
        }
        context.update(new_context)
        return context

    def form_valid(self, form):
        trans = form.save(commit=False)
        trans.translator = self.request.user
        exercise = self.kwargs['exercise']
        trans.exercise = TranslationExercise.objects.get(slug=exercise)
        language = self.kwargs['language']
        trans.language = Language.objects.get(slug=language)
        trans.save(user=self.request.user)
        return HttpResponseRedirect(trans.get_absolute_url())
add_languagetranslations = login_required(CreateTranslationView.as_view())


class TranslationMixin(object):
    model = Translation
    slug_url_kwarg = 'exercise'
    form_class = TranslationForm

    def get_language(self):
        language_id = self.kwargs['language']
        return Language.objects.get(id=language_id)

    def get_exercise(self):
        exercise = self.kwargs['exercise']
        return TranslationExercise.objects.get(slug=exercise)

    def get_translator(self):
        translator_id = self.kwargs['translator']
        return get_user_model().objects.get(id=translator_id)

    def get_queryset(self):
        exercise = self.kwargs['exercise']
        language_id = self.kwargs['language']
        translator_id = self.kwargs['translator']
        qs = self.model.objects.filter(
            language__id=language_id,
            exercise__slug=exercise,
            translator__id=translator_id,
        )
        return qs

    def get_object(self, queryset=None):
        if queryset is None:
            queryset = self.get_queryset()
        if not queryset:
            kwargs = {'verbose_name': queryset.model._meta.verbose_name}
            raise Http404("No %(verbose_name)s found matching the query" % kwargs)
        return queryset.get()

    def get_context_data(self, **context):
        context = super(TranslationMixin, self).get_context_data(**context)
        new_context = {
            'me': 'translation',
            'exercise': self.get_exercise(),
            'language': self.get_language(),
            'translator': self.get_translator(),
        }
        context.update(new_context)
        return context


class DetailTranslationView(TranslationMixin, DetailView):
    """Show a specific translation by a specific user for a specific
    language."""
    template_name = 'translations/show_translation.html'
show_translation_for_language = DetailTranslationView.as_view()


class ChangeTranslationMixin(TranslationMixin):

    def get_queryset(self):
        translator = self.get_translator()
        if translator != self.request.user:
            raise PermissionDenied
        queryset = super(ChangeTranslationMixin, self).get_queryset()
        return queryset.filter(translator=self.get_translator())


class UpdateTranslationView(ChangeTranslationMixin, UpdateView):
    """Change a specific translation by a specific user for a specific
    language."""
    template_name = 'translations/languagetranslation_form.html'

    def get_success_url(self):
        return self.object.get_absolute_url()
change_languagetranslations = login_required(UpdateTranslationView.as_view())


class DeleteTranslationForLanguageView(ChangeTranslationMixin, DeleteView):
    """Delete a specific translation for a specific language."""

    template_name = 'translations/delete_translation.html'
    context_object_name = 'translation'

    def get_success_url(self):
        success_url = "/translation/language/%s/" % self.get_language().slug
        return success_url
delete_languagetranslations = DeleteTranslationForLanguageView.as_view()
