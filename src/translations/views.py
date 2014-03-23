from django.contrib.auth.decorators import login_required
from django.http import HttpResponseRedirect, Http404
from django.core.exceptions import PermissionDenied
from django.shortcuts import get_object_or_404, render
from django.views.generic import ListView, DeleteView
from django.contrib.contenttypes.models import ContentType

import logging
_LOG = logging.getLogger(__name__)

from cals.views import langs_for_user
from cals.models import Language, User

from translations.models import Translation, TranslationExercise
from translations.forms import TranslationForm
from translations import get_model_for_kwarg

def get_translationexercise(**kwargs):
    return get_model_for_kwarg(TranslationExercise, 'exercise', 'slug', **kwargs)

def get_language(**kwargs):
    return get_model_for_kwarg(Language, 'language', 'slug', **kwargs)

def get_user(**kwargs):
    return get_model_for_kwarg(User, 'translator', 'username', **kwargs)


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

def show_translation_for_language(request, *args, **kwargs):
    """Show a specific translation by a specific user for a specific
    language."""

    # TODO: Allow several translations per person?
    me = 'translation'
    template = 'translations/show_translation.html'
    slug = kwargs['slug']
    # Bizarro error. This line *should* return the same as the next, but
    # it doesn't
    #trans = get_object_or_404(Translation, language=lang, exercise=exercise, translator=user)
    try:
        trans = Translation.objects.get(slug=slug)
    except Translation.DoesNotExist:
        raise Http404
    data = {'lang': trans.language,
            'translation': trans,
            'me': me,}
    return render(request, template, data)

@login_required
def add_languagetranslations(request, *args, **kwargs):
    """Add a specific translation by a specific user for a specific
    language."""

    me = 'translation'
    template = 'translations/languagetranslation_form.html'
    help_message = ''
    lang = get_language(**kwargs)
    exercise = get_translationexercise(**kwargs)
    user = request.user
    try:
        Translation.objects.get(exercise=exercise, language=lang, translator=user)
    except Translation.DoesNotExist:
        pass
    else:
        return HttpResponseRedirect('/translation/%s/language/%s/change' % (exercise.slug, lang.slug))
    form = TranslationForm()
    if request.method == 'POST':
        form = TranslationForm(request.POST)
        if form.is_valid():
            trans = form.save(commit=False)
            trans.translator = user
            trans.language = lang
            trans.exercise = exercise
            trans.save(user=request.user)
            return HttpResponseRedirect('/translation/%s/language/%s/' %
                    (trans.exercise.slug, lang.slug))
        else:
            error = 'Form not valid'
    trans = lang.translations.exclude(translation__isnull=True).exclude(translation='')
    data = {'form': form,
            'exercise': exercise, 
            'help_message': help_message,
            'me': me}
    return render(request, template, data)

@login_required
def change_languagetranslations(request, *args, **kwargs):
    """Change a specific translation by a specific user for a specific
    language."""

    me = 'translation'
    template = 'translations/languagetranslation_form.html'
    help_message = ''
    lang = get_language(**kwargs)
    exercise = get_translationexercise(**kwargs)
    #trans = Translation.objects.get(language=lang, translator=request.user, exercise=exercise)
    try:
        trans = lang.translations.get(translator=request.user, exercise=exercise)
    except Translation.DoesNotExist:
        raise Http404
    form = TranslationForm(instance=trans)
    if request.method == 'POST':
        form = TranslationForm(data=request.POST, instance=trans)
        if form.is_valid():
            trans = form.save()
            return HttpResponseRedirect('./%s/' % request.user)
    data = {'form': form,
            'exercise': exercise, 'help_message': help_message,
            'me': me}
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
        queryset = self.exercise.translations.exclude(translation__isnull=True).exclude(translation='').order_by('language')
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


class DeleteTranslationForLanguageView(DeleteView):
    """Delete a specific translation for a specific language."""

    template_name = 'translations/delete_translation.html'
    context_object_name = 'translation'

    def get_context_data(self, **kwargs):
        context = super(DeleteTranslationForLanguageView, self).get_context_data(**kwargs)
        context['me'] = 'translation'
        return context

    def get_success_url(self):
        success_url = "/translation/language/%s/" % self.lang.slug 
        return success_url

    def get_object(self, queryset=None):
        # XXX: While deciding on how to replace login_required()
        if not self.request.user.is_authenticated():
            raise PermissionDenied
        self.lang = get_language(**self.kwargs)
        exercise = get_translationexercise(**self.kwargs)
        try:
            trans = Translation.objects.get(language=self.lang, translator=self.request.user, exercise=exercise)
        except Translation.DoesNotExist:
            raise Http404("No %(verbose_name)s found matching the query" %
                            {'verbose_name':
                            Translation._meta.verbose_name})
        return trans
delete_languagetranslations = DeleteTranslationForLanguageView.as_view()
