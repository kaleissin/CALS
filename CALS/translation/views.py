from django.contrib.auth.decorators import login_required
from django.http import HttpResponseRedirect, Http404
from django.shortcuts import get_object_or_404
from django.views.generic.list_detail import object_list
from django.views.generic.create_update import delete_object

from nano.tools import getLogger, pop_error, render_page, get_user_model
LOG = getLogger('translation.views')

from cals.views import _get_lang, _get_user

from translation.models import Translation, TranslationExercise
from translation.forms import TranslationForm

User = get_user_model()

def get_translationexercise(*args, **kwargs):
    #assert False, kwargs.get('exercise', None)
    return get_object_or_404(TranslationExercise, slug=kwargs.get('exercise', None))

def show_languagetranslations(request, *args, **kwargs):
    me = 'translation'
    error = pop_error(request)
    template = 'translation/languagetranslation_list.html'
    lang = _get_lang(*args, **kwargs)
    trans = lang.translations.exclude(translation__isnull=True).exclude(translation='')
    if request.user.is_authenticated():
        exercises = TranslationExercise.objects.exclude(
                translations__language=lang,
                translations__translator=request.user)
    else:
        exercises = TranslationExercise.objects.exclude(translations__language=lang)
    extra_context = {'lang': lang,
            'exercises': exercises, 
            'me': me,
            'error': error,}
    return object_list(request, queryset=trans, template_name=template,
            extra_context=extra_context)


def list_translation_for_language(request, *args, **kwargs):
    me = 'translation'
    error = pop_error(request)
    template = 'translation/list_translation_for_language.html'
    lang = _get_lang(*args, **kwargs)
    exercise = get_translationexercise(*args, **kwargs)
    trans = Translation.objects.filter(language=lang, exercise=exercise)
    data = {'exercise': exercise,
            'lang': lang,
            'object_list': trans,
            'me': me, 
            'error': error,}
    return render_page(request, template, data)

def show_translation_for_language(request, *args, **kwargs):
    me = 'translation'
    error = pop_error(request)
    template = 'translation/show_translation.html'
    lang = _get_lang(*args, **kwargs)
    exercise = get_translationexercise(*args, **kwargs)
    user = _get_user(*args, **kwargs)
    # Bizarro error. This line *should* return the same as the next, but
    # it doesn't
    #trans = get_object_or_404(Translation, language=lang, exercise=exercise, translator=user)
    try:
        trans = lang.translations.get(translator=user, exercise=exercise)
    except Translation.DoesNotExist:
        raise Http404
    data = {'lang': lang,
            'translation': trans,
            'me': me, 
            'error': error,}
    return render_page(request, template, data)

@login_required
def add_languagetranslations(request, *args, **kwargs):
    me = 'translation'
    error = pop_error(request)
    template = 'translation/languagetranslation_form.html'
    help_message = ''
    lang = _get_lang(*args, **kwargs)
    exercise = get_translationexercise(*args, **kwargs)
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
            trans = Translation()
            trans.translation = form.cleaned_data['translation']
            trans.translator = user
            trans.language = lang
            trans.exercise = exercise
            trans.interlinear = form.cleaned_data['interlinear']
            trans.save()
            request.session['error'] = None
            return HttpResponseRedirect('..')
        else:
            error = 'Form not valid'
            request.session['error'] = error
    trans = lang.translations.exclude(translation__isnull=True).exclude(translation='')
    data = {'form': form,
            'exercise': exercise, 
            'help_message': help_message,
            'error': error, 
            'me': me}
    return render_page(request, template, data)

@login_required
def change_languagetranslations(request, *args, **kwargs):
    me = 'translation'
    error = pop_error(request)
    template = 'translation/languagetranslation_form.html'
    help_message = ''
    lang = _get_lang(*args, **kwargs)
    exercise = get_translationexercise(*args, **kwargs)
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
            request.session['error'] = None
            return HttpResponseRedirect('./%s/' % request.user)
    data = {'form': form,
            'exercise': exercise, 'help_message': help_message,
            'error':error, 'me': me}
    return render_page(request, template, data)

def list_all_translations(request, *args, **kwargs):
    me = 'translation'
    error = pop_error(request)
    template = 'translation/translation_list.html'
    exercises = TranslationExercise.objects.all()
    extra_context = {'me': me, 'error': error,}
    return object_list(request, queryset=exercises, template_name=template,
            extra_context=extra_context)

def show_translationexercise(request, *args, **kwargs):
    me = 'translation'
    error = pop_error(request)
    template = 'translation/translationexercise_list.html'
    exercise = get_translationexercise(*args, **kwargs)
    trans = exercise.translations.exclude(translation__isnull=True).exclude(translation='').order_by('language')
    extra_context = {'me': me, 'error': error, 'exercise': exercise}
    return object_list(request, queryset=trans, template_name=template,
            extra_context=extra_context)

@login_required
def delete_languagetranslations(request, *args, **kwargs):
    me = 'translation'
    template = 'delete.html'
    error = pop_error(request)
    lang = _get_lang(*args, **kwargs)
    exercise = get_translationexercise(*args, **kwargs)
    trans = Translation.objects.get(language=lang, translator=request.user, exercise=exercise)
    extra_context = {'me': me, 'error': error,}
    return delete_object(request, model=Translation, object_id=trans.id,
            post_delete_redirect="..", extra_context=extra_context)

