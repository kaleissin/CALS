from django.contrib.auth.decorators import login_required
from django.http import HttpResponseRedirect, Http404
from django.shortcuts import get_object_or_404
from django.views.generic.list_detail import object_list
from django.views.generic.create_update import delete_object

from nano.tools import render_page, get_user_model

import logging
_LOG = logging.getLogger(__name__)

from cals.views import langs_for_user
from cals.models import Language, User

from translations.models import Translation, TranslationExercise
from translations.forms import TranslationForm
from translations import get_model_for_kwarg

User = get_user_model()

def get_translationexercise(**kwargs):
    return get_model_for_kwarg(TranslationExercise, 'exercise', 'slug', **kwargs)

def get_language(**kwargs):
    return get_model_for_kwarg(Language, 'language', 'slug', **kwargs)

def get_user(**kwargs):
    return get_model_for_kwarg(User, 'translator', 'username', **kwargs)

def show_languagetranslations(request, *args, **kwargs):
    """List all translations for a specific language.
    
    Specific translations is reached by show_translation_for_language().
    """

    me = 'translation'
    template = 'translations/languagetranslation_list.html'
    lang = get_language(**kwargs)
    trans = lang.translations.exclude(translation__isnull=True).exclude(translation='')
    if request.user.is_authenticated():
        exercises = TranslationExercise.objects.exclude(
                translations__language=lang,
                translations__translator=request.user)
    else:
        exercises = TranslationExercise.objects.exclude(translations__language=lang)
    extra_context = {'lang': lang,
            'exercises': exercises, 
            'me': me,}
    return object_list(request, queryset=trans, template_name=template,
            extra_context=extra_context)


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
            'me': me,}
    return render_page(request, template, data)

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
    return render_page(request, template, data)

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
    return render_page(request, template, data)

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
    return render_page(request, template, data)

def list_all_translations(request, template_name='translations/translation_list.html', *args, **kwargs):
    """List all translations."""

    me = 'translation'
    exercises = TranslationExercise.objects.all()
    extra_context = {'me': me,}
    return object_list(request, queryset=exercises, template_name=template_name,
            extra_context=extra_context)

def show_translationexercise(request, template_name='translations/translationexercise_list.html', *args, **kwargs):
    """List all translations for a specific exercise, and provide links
    to add more translations.
    """

    me = 'translation'
    exercise = get_translationexercise(**kwargs)
    trans = exercise.translations.exclude(translation__isnull=True).exclude(translation='').order_by('language')
    natlangs, other_conlangs, own_conlangs = None, None, None
    if request.user.is_authenticated():
        natlangs = Language.objects.natlangs()
        conlangs = Language.objects.conlangs()
        own_conlangs = langs_for_user(request.user)
        other_conlangs = conlangs.exclude(id__in=[l.id for l in own_conlangs])
    extra_context = {
            'me': me, 
            'exercise': exercise,
            'natlangs': natlangs,
            'own_conlangs': own_conlangs,
            'other_conlangs': other_conlangs,
            }
    return object_list(request, queryset=trans, template_name=template_name,
            extra_context=extra_context)

@login_required
def delete_languagetranslations(request, template_name='delete.html', *args, **kwargs):
    """Delete a specific translation for a specific language."""

    me = 'translation'
    lang = get_language(**kwargs)
    exercise = get_translationexercise(**kwargs)
    trans = Translation.objects.get(language=lang, translator=request.user, exercise=exercise)
    extra_context = {'me': me,}
    return delete_object(request, model=Translation, object_id=trans.id,
            template_name=template_name,
            post_delete_redirect="/translation/language/%s/" % lang.slug, 
            extra_context=extra_context)

