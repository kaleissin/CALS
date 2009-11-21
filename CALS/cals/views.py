# Create your views here.
from pprint import pprint, pformat
from random import choice, sample
import time
import unicodedata
import string
import sys
from datetime import datetime
sys.stderr = sys.stdout

import logging
_LOG = logging.getLogger(__name__)

from django.contrib import auth #.authenticate, auth.login
from django.contrib.auth.decorators import login_required
from django.contrib.auth.models import User
from django.core.mail import send_mail
from django.http import HttpResponseRedirect, HttpResponseNotFound, HttpResponseForbidden
from django.shortcuts import get_object_or_404
from django.template import loader, Context
from django.template.loader import render_to_string
from django.views.generic.list_detail import object_list
from django.views.generic.create_update import delete_object
from django.utils.encoding import smart_unicode
from django.db.models import Q

from snippets.namepaginator import NamePaginator, InvalidPage

from tagging.models import Tag

from pygooglechart import StackedVerticalBarChart, Axis

from cals.models import *
from cals.forms import *
from cals.statistics import *
from cals.tools import *

from translations.models import TranslationExercise, Translation

from nano.tools import *
from nano.blog.models import Entry
from nano.privmsg.models import PM

_error_forbidden_msg = "You don't have the necessary permissions to edit here."
error_forbidden = render_to_string('error.html', 
        {'error_message': _error_forbidden_msg })

class CALSError(Exception):
    pass

class CALSUserExistsError(CALSError):
    pass

def _get_lang(*args, **kwargs):
    return get_object_or_404(Language, slug=kwargs.get('lang', None))

def _get_feature(*args, **kwargs):
    return get_object_or_404(Feature, id=kwargs.get('object_id', None))

def _get_exercise(*args, **kwargs):
    #assert False, kwargs.get('exercise', None)
    return get_object_or_404(TranslationExercise, slug=kwargs.get('exercise', None))

def _get_profile(*args, **kwargs):
    return get_object_or_404(User, id=kwargs.get('object_id', None))

def _get_user(*args, **kwargs):
    return get_object_or_404(User, username=kwargs.get('user', None))

def _get_url_pieces(name='slug', **kwargs):
    _LOG.debug('Url-pieces: %s' % kwargs)
    if name in kwargs:
        # split on +, remove empty pieces
        pieces = filter(None, kwargs[name].split('+'))
        if pieces:
            return pieces
    # '%s not in kwargs: %s' % (name, pformat(kwargs))
    return None

def langs_for_user(user):
    if isinstance(user, Profile):
        profile = user
        user = user.user
    else: 
        user = user
        profile = user.get_profile()
    return Language.objects.filter(Q(public=True) | Q(manager=user) | Q(editors=user))

def may_edit_lang(user, language):
    # Tuple-in-tuple so that the inner tuple can be discarded easier:
    # may_edit, _ = may_edit_lang(user, lang)
    standardreturn = True, (False, False)

    # Must have a profile
    try:
        profile = user.get_profile()
    except AttributeError:
        return False, (False, False)
    
    if user.is_superuser:
        return True, (True, True)
    if user == language.manager:
        return True, (False, True)
    if user in language.editors.all():
        return standardreturn
    if language.public:
        return standardreturn
    return False, (False, False)

def set_language_feature_value(lang, feature_id, value_id):
    feature = Feature.objects.active().get(id=feature_id)
    try:
        lf = LanguageFeature.objects.get(language=lang, feature=feature)
    except LanguageFeature.DoesNotExist:
        lf = None
    try:
        fv = FeatureValue.objects.get(id=int(value_id or 0))
    except FeatureValue.DoesNotExist:
        fv = None
    if fv:
        if lf:
            if lf.value != fv: # change
                lf.value = fv
                lf.save()
        else: # new
            lf_new = LanguageFeature.objects.create(language=lang, feature=feature, value=fv) 
    else:
        if lf: # delete
            lf.delete()

def make_feature_list_for_lang(lang=None):
    categories = Category.objects.all().select_related().order_by('id')
    cats = []
    for category in categories:
        try:
            fvs = FeatureValue.objects.filter(feature__category=category)
        except FeatureValue.DoesNotExist:
            continue
        features = Feature.objects.active().filter(category=category)
        f = []
        for feature in features:
            form = FeatureValueForm(feature=feature)
            lf = None
            if lang:
                try:
                    lf = LanguageFeature.objects.get(language=lang, feature=feature)
                    form = FeatureValueForm(feature=feature,
                            initial={'value': '%s_%s' % (feature.id, lf.value.id)})
                            #instance=lf.value, initial={'name': lf.value.id})
                except LanguageFeature.DoesNotExist:
                    pass
            f.append({'feature': feature, 'form':form, 'value': lf})
        if f:
            cats.append({'name': category.name, 'features': f})
        else:
            cats.append({'name': category.name})
    return cats

def revert(user, descriptions, revert_to):
    if revert_to:
        try:
            description = descriptions.get(id=int(revert_to))
        except Description.DoesNotExist:
            error = 'Invalid version. This revert-attempt by %s has been logged.' % user.get_profile()
            return error
        else:
            description.current = True
            description_last_modified_by = user
            description.save()

# Feature
def compare_feature(request, *args, **kwargs):
    me = 'feature'
    features = _get_url_pieces(name='objects', **kwargs)
    if not features:
        # 'No feature'
        return HttpResponseNotFound()
    if len(features) == 1:
        # 'One feature'
        kwargs['object_id'] = features[0]
        return show_feature(request, *args, **kwargs)
    elif len(features) > 2:
        # 'Too many features'
        return HttpResponseNotFound()
    fvs, fs = [], []
    for feature in features:
        try:
            f = Feature.objects.active().get(id=feature)
        except Feature.DoesNotExist:
            # 
            return HttpResponseNotFound()
        fv = FeatureValue.objects.filter(feature__id=int(feature))
        if not fv:
            # 
            return HttpResponseNotFound()
        fvs.append(fv)
        fs.append(f)
    matrix = compare_features(fs, fvs)

    # rewrite matrix into something the template-system can deal with
    comparison = []
    for v2 in fvs[1]:
        vs = []
        for v1 in fvs[0]:
            vs.append(int(matrix[v1.id][v2.id]))
        comparison.append({'fv': v2, 'counts': tuple(vs)})
    #return comparison

    data = { 
            'comparison': comparison,
            'me': me,
            'features': fs,
            'fvs': fvs,
            }
    return render_page(request, 'feature_compare.html', data)

@login_required()
def change_or_add_feature(request, *args, **kwargs):
    categoryform = CategoryForm()
    featureform = FeatureForm()
    valueformset = NewFeatureValueFormSet()

    data = {u'me': u'feature',
        'featureform': featureform,
        'fvformset': valueformset,
    }

    return render_page(request, 'cals/suggested_feature_form.html', data)

def list_feature(request, *args, **kwargs):
    extra_context = {'me': 'feature'}
    queryset = Category.objects.all().order_by('id')
    template = 'cals/feature_list.html'
    return object_list(queryset=queryset, template_name=template,
            extra_context=extra_context)

def show_feature(request, *args, **kwargs):
    me = 'feature'
    try:
         feature = Feature.objects.active().get(id=kwargs['object_id'])
    except Feature.DoesNotExist:
        return HttpResponseNotFound()
    cform = CompareTwoFeaturesForm()
    if request.method == 'POST':
        cform = CompareTwoFeaturesForm(data=request.POST)
        if cform.is_valid():
            feature2 = cform.cleaned_data['feature2']
            return HttpResponseRedirect('/feature/%s+%s/' % (feature.id, feature2.id))
    data = {'object': feature, 
            'me': me, 
            'cform': cform}
    return render_page(request, 'feature_detail.html', data)

@login_required()
def change_feature_description(request, *args, **kwargs):
    me = 'feature'
    feature = get_object_or_404(Feature, id=kwargs.get('object_id', None))
    preview = u''
    link = '/feature/%i/' % feature.id
    if not request.user.is_staff:
        error = "You do not have permission to change this feature's description"
        request.notifications.add(error, 'error')
        return HttpResponseRedirect(link)
    if request.method == 'POST':
        if feature.description:
            form = DescriptionForm(data=request.POST, instance=feature.description)
        else:
            form = DescriptionForm(data=request.POST)
        if form.is_valid():
            featured = form.save(commit=False)
            
            if request.POST.get('preview'):
                preview = featured.make_xhtml()
                msg = "You are previewing the description of this feature"
                request.notifications.add(msg)
            elif request.POST.get('submit'):
                featured.content_type = ContentType.objects.get_for_model(feature)
                featured.object_id = feature.id
                featured.freetext_type = 'rst'
                featured.save()
                return HttpResponseRedirect(link)
    else:
        if feature.description:
            form = DescriptionForm(instance=feature.description)
        else:
            form = DescriptionForm()
    data = {'me': me,
            'form': form,
            'preview': preview,
            'feature': feature,}
    return render_page(request, 'feature_description_form.html', data)

def show_feature_history(request, *args, **kwargs):
    me = 'feature'
    feature = get_object_or_404(Feature, id=kwargs.get('object_id', None))
    feature_type = ContentType.objects.get(app_label="cals", model="feature")
    descriptions = Description.archive.filter(object_id=feature.id, content_type=feature_type).order_by('-last_modified')
    link = '/feature/%i/' % feature.id
    data = {'me': me,
            'descriptions': descriptions,
            'feature': feature,
            }
    return render_page(request, 'feature_description_history_list.html', data)

def compare_feature_history(request, *args, **kwargs):
    me = 'feature'
    feature = get_object_or_404(Feature, id=kwargs.get('object_id', None))
    feature_type = ContentType.objects.get(app_label="cals", model="feature")
    descriptions = Description.archive.filter(object_id=feature.id, content_type=feature_type).order_by('-last_modified')

    newest = descriptions[0]
    oldest = tuple(descriptions)[-1]
    oldid = request.GET.get('oldid', oldest.id)
    newid = request.GET.get('newid', newest.id)
    if oldid:
        oldest = descriptions.get(id=int(oldid))
    if newid:
        newest = descriptions.get(id=int(newid))
    link_format = '/feature/%i/history/compare?' % feature.id
    patch = u''
    if request.method == 'GET':
        patch = description_diff(oldest, newest, link_format)
    data = {'me': me,
            'oldest': oldest,
            'newest': newest,
            'patch': patch,
            'feature': feature,}
    return render_page(request, 'feature_description_history_compare.html', data)

@login_required
def revert_feature_description(request, *args, **kwargs):
    me = 'language'
    feature = get_object_or_404(Feature, id=kwargs.get('object_id', None))
    feature_type = ContentType.objects.get(app_label="cals", model="feature")
    may_edit, (is_admin, is_manager) = may_edit_lang(request.user, lang)
    if not may_edit:
        return HttpResponseForbidden(error_forbidden)

    descriptions = Description.archive.filter(object_id=feature.id, content_type=feature_type).order_by('-last_modified')
    link_format = '/feature/%i/history/compare?' % feature.id

    revert_to = request.GET.get('id', 0)
    error = revert(request.user, descriptions, revert_to)
    if error:
        request.notification.add(error, 'error')
    return HttpResponseRedirect(link_format)

# language

def compare_language(request, *args, **kwargs):
    me = 'language'
    langslugs = _get_url_pieces(name='slugs', **kwargs)
    comparison_type = kwargs.get('opt', None)
    _LOG.info('%s will compare %s' % (request.user, langslugs))
    if not langslugs:
        return HttpResponseForbidden(error_forbidden)
    if len(langslugs) == 1:
        kwargs['slug'] = langslugs[0]
        return show_language(request, *args, **kwargs)
    langs = []
    for langslug in langslugs:
        try:
            lang = Language.objects.get(slug=langslug)
        except Language.DoesNotExist:
            continue
        langs.append(lang)
    same = None
    different = None
    if comparison_type == 'different':
        same = False
        different = True
    elif comparison_type == 'same':
        same = True
        different = False
    _LOG.debug('0: %s' % comparison_type)
    _LOG.debug('1: same %s, different %s' % (same, different))
    comparison = compare_languages(langs, same=same, different=different)
    _LOG.debug('Last: Features compared: %s (%s)' % (len(comparison), comparison_type))
    data = {
            'comparison': comparison, 
            'me': me,
            'langs': langs,
            'comparison_type': comparison_type,
            }
    return render_page(request, 'language_compare.html', data)

def show_language(request, *args, **kwargs):
    me = 'language'
    lang = _get_lang(*args, **kwargs)
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
    cform = CompareTwoForm()
    if request.method == 'POST':
        cform = CompareTwoForm(data=request.POST)
        if cform.is_valid():
            lang2 = cform.cleaned_data['lang2']
            same = None
            different = None
            comparison_type = request.REQUEST.get('compare', None)
            if comparison_type == 'different':
                same = False
                different = True
            elif comparison_type == 'same':
                same = True
                different = False
            redirect_to = '/language/%s+%s/' % (lang.slug, lang2.slug)
            if comparison_type in ('same', 'different'):
                redirect_to = redirect_to + comparison_type
            return HttpResponseRedirect(redirect_to)
    data = {'object': lang, 
            'categories': cats, 
            'me': me, 
            'cform': cform,
            'may_edit': may_edit,
    }
    return render_page(request, 'language_detail.html', data)

@login_required()
def create_language(request, *args, **kwargs):
    me = 'language'
    state = 'new'
    langform = LanguageForm()
    user = request.user

    editorform = EditorForm()

    # sort values into categories
    cats = make_feature_list_for_lang()

    if request.method == 'POST':
        langform = LanguageForm(data=request.POST, initial=request.POST)
        if langform.is_valid():
            lang = langform.save(commit=False)
            lang.added_by = user
            lang.last_modified_by = user
            if not lang.manager:
                lang.manager = user
            lang.save(user=user, solo=False)
            editorform = EditorForm(data=request.POST, instance=lang)
            if editorform.is_valid():
                editorform.save()
            # greeting
            if lang.greeting:
                # use signal instead?
                greetingexercise = TranslationExercise.objects.get(id=1)
                trans = Translation(translation=lang.greeting,language=lang,
                        translator=user,exercise=greetingexercise)
                trans.save()
            # values
            for value in request.POST.getlist(u'value'):
                feature_id, value_id = value.split('_')
                if not value_id:
                    continue
                set_language_feature_value(lang, feature_id, value_id)
            freq = get_averageness_for_lang(lang, scale=100)
            _LOG.info('Freq now: %s' % repr(freq))
            lang.num_features = LanguageFeature.objects.filter(language=lang).count()
            lang.num_avg_features = freq
            lang.set_average_score()
            lang.save(user=user)
            return HttpResponseRedirect('.')
        else:
            error = "Couldn't store language-description: " + str(form.errors) 
            request.notifications.add(error, 'error')
    data = {'form': langform, 
            'categories': cats, 
            'me': me, 
            'editorform': editorform,
            'state': state,}
    return render_page(request, 'language_form.html', data)

@login_required()
def change_language(request, *args, **kwargs):
    me = 'language'
    state = 'change'
    lang = _get_lang(*args, **kwargs)
    user = request.user

    _LOG.info('%s about to change %s' % (user, lang))

    may_edit, (is_admin, is_manager) = may_edit_lang(user, lang)
    if not may_edit:
        return HttpResponseForbidden(error_forbidden)

    langform = LanguageForm(instance=lang)
    #moreinfoformset = ExternalInfoFormSet(queryset=lang.externalinfo.all())
    #profile = user.get_profile()
    if is_manager:
        editorform = EditorForm(instance=lang)
    else:
        editorform = None
    _LOG.info('User is manager: %s' % user == lang.manager)
    # sort values into categories
    cats = make_feature_list_for_lang(lang)

    if request.method == 'POST':
        langform = LanguageForm(data=request.POST, instance=lang, initial=request.POST)
        if langform.is_valid():

            # editors and managers
            old_manager = lang.manager
            lang = langform.save(commit=False)
            if is_manager:
                editorform = EditorForm(data=request.POST, instance=lang)
                editors = lang.editors
                if editorform.is_valid():
                    editors = editorform.save()
                    _LOG.debug('editors after save: %s' % editors)
                if not 'manager' in langform.cleaned_data:
                    lang.manager = old_manager
            else:
                # Just in case: must be manager also in view in order to
                # change who can be manager
                lang.manager = old_manager

            lang.last_modified_by = user

            # greeting
            greetingexercise = TranslationExercise.objects.get(id=1)
            new_greeting = lang.greeting
            try:
                greetingtrans = Translation.objects.get(language=lang, exercise=greetingexercise,
                        translator=user)
            except Translation.DoesNotExist:
                greetingtrans = None
            if new_greeting:
                if greetingtrans:
                    if new_greeting != greetingtrans.translation:
                        greetingtrans.translation = new_greeting
                else:
                    Translation.objects.create(language=lang,
                            exercise=greetingexercise, translator=user,
                            translation=new_greeting)
            else:
                if greetingtrans:
                    greetingtrans.delete()
#             # more info
#             moreinfoformset = ExternalInfoFormSet(request.POST)
#             if moreinfoformset.is_valid():
#                 moreinfo = moreinfoformset.save()
#                 assert False, moreinfo
# 
            # values
            for value in request.POST.getlist(u'value'):
                feature_id, value_id = value.split('_')
                set_language_feature_value(lang, feature_id, value_id)
            freq = get_averageness_for_lang(lang, scale=100)
            lang.num_features = LanguageFeature.objects.filter(language=lang).count()
            lang.num_avg_features = freq
            lang.set_average_score()
            lang.save(user=user)
            return HttpResponseRedirect('.')
        else:
            error = "Couldn't change language-description: " + str(langform.errors)
            request.notifications.add(error, 'error')
    data = {'form': langform, 
            'categories': cats, 
            'editorform': editorform, 
            #'moreinfoformset': moreinfoformset,
            'me': me, 
            'state': state,}
    return render_page(request, 'language_form.html', data)

def list_languages(request, *args, **kwargs):
    """Select and dispatch to a view of the list of languages"""
    if in_kwargs_or_get(request, kwargs, 'action', 'cloud'):
        return language_cloud(request, *args, **kwargs)
    for value in ('jrk', 'jrklist'):
        if in_kwargs_or_get(request, kwargs, 'action', value):
            return language_jrklist(request, *args, **kwargs)
    if not kwargs or kwargs.get('action', None) is None:
        return language_list(request, *args, **kwargs)

def language_cloud(request, *args, **kwargs):
    me = 'language'
    queryset = Language.objects.all().order_by('name')
    langs = []
    for lang in queryset:
        langs.append({'slug': lang.slug,
                'size': int(round(lang.get_infodensity() * 6)) + 1,
                'name': lang.name,
        })
    data = {'me': me, 'langs': langs}
    return render_page(request, 'cals/language_cloud.html',
            data)

def language_jrklist(request, *args, **kwargs):
    queryset = Language.objects.exclude(background='').order_by('name')
    return object_list(request, queryset, 
            template_name='jrklist.html',
            extra_context={'me': 'language'})

def language_list(request, *args, **kwargs):
    queryset = Language.objects.all().order_by('name')
    paginator = NamePaginator(queryset, on="name")
    page = page_in_kwargs_or_get(request, kwargs) or 1

    try:
        page = paginator.page(page)
    except (InvalidPage):
        page = paginator.page(paginator.num_pages)

    data = {u'me': u'language',
            u'object_list': page.object_list,
            u'page_obj': page,
            u'paginator': paginator,
            u'is_paginated': True}

    return render_page(request, 'cals/language_list.html', data)

# BEGIN LF

def show_languagefeature(request, *args, **kwargs):
    me = 'language'
    lang = _get_lang(*args, **kwargs)
    feature = get_object_or_404(Feature, id=kwargs.get('object_id', None))
    lf = get_object_or_404(LanguageFeature, language=lang, feature=feature)
    try:
        description = lf.description
    except Description.DoesNotExist:
        description = None
    link = '/language/%s/feature/%i/' % (lang.slug, feature.id)
    data = {'me': me,
            'description': description,
            'lang': lang, 'feature': lf,}
    return render_page(request, 'language_description_detail.html', data)

def show_languagefeature_history(request, *args, **kwargs):
    me = 'language'
    lang = _get_lang(*args, **kwargs)
    feature = get_object_or_404(Feature, id=kwargs.get('object_id', None))
    lf = get_object_or_404(LanguageFeature, language=lang, feature=feature)
    lf_type = ContentType.objects.get(app_label="cals", model="languagefeature")
    descriptions = Description.archive.filter(object_id=lf.id, content_type=lf_type).order_by('-last_modified')
    link = '/language/%s/feature/%i/' % (lang.slug, feature.id)
    data = {'me': me,
            'descriptions': descriptions,
            'lang': lang, 'feature': lf,}
    return render_page(request, 'language_description_history_list.html', data)

def compare_languagefeature_history(request, *args, **kwargs):
    me = 'language'
    lang = _get_lang(*args, **kwargs)
    feature = get_object_or_404(Feature, id=kwargs.get('object_id', None))
    lf_type = ContentType.objects.get(app_label="cals", model="languagefeature")
    lf = get_object_or_404(LanguageFeature, language=lang, feature=feature)
    descriptions = Description.archive.filter(object_id=lf.id, content_type=lf_type).order_by('-last_modified')
    may_edit, (is_admin, is_manager) = may_edit_lang(request.user, lang)

    newest = descriptions[0]
    oldest = tuple(descriptions)[-1]
    oldid = request.GET.get('oldid', oldest.id)
    newid = request.GET.get('newid', newest.id)
    if oldid:
        oldest = descriptions.get(id=int(oldid))
    if newid:
        newest = descriptions.get(id=int(newid))
    link_format = '/language/%s/feature/%i/history/compare?' % (lang.slug, feature.id)
    patch = u''
    if request.method == 'GET':
        patch = description_diff(oldest, newest, link_format, may_edit, is_admin)
    data = {'me': me,
            'oldest': oldest,
            'newest': newest,
            'patch': patch,
            'lang': lang, 
            'feature': lf,}
    return render_page(request, 'language_description_history_compare.html', data)

@login_required
def revert_languagefeature_description(request, *args, **kwargs):
    me = 'language'
    lang = _get_lang(*args, **kwargs)
    feature = get_object_or_404(Feature, id=kwargs.get('object_id', None))
    lf_type = ContentType.objects.get(app_label="cals", model="languagefeature")
    lf = get_object_or_404(LanguageFeature, language=lang, feature=feature)
    may_edit, (is_admin, is_manager) = may_edit_lang(request.user, lang)
    if not may_edit:
        return HttpResponseForbidden(error_forbidden)

    descriptions = Description.archive.filter(object_id=lf.id, content_type=lf_type).order_by('-last_modified')
    link_format = '/language/%s/feature/%i/' % (lang.slug, feature.id)

    revert_to = request.GET.get('id', 0)
    error = revert(request.user, descriptions, revert_to)
    if error:
        request.notification.add(error, 'error')
    return HttpResponseRedirect(link_format)

@login_required
def remove_languagefeature_description_version(request, *args, **kwargs):
    me = 'language'
    lang = _get_lang(*args, **kwargs)
    feature = get_object_or_404(Feature, id=kwargs.get('object_id', None))
    lf_type = ContentType.objects.get(app_label="cals", model="languagefeature")
    lf = get_object_or_404(LanguageFeature, language=lang, feature=feature)
    may_edit, (is_admin, is_manager) = may_edit_lang(request.user, lang)
    if not is_admin:
        return HttpResponseForbidden(error_forbidden)

    descriptions = Description.archive.filter(object_id=lf.id, content_type=lf_type).order_by('-last_modified')
    link_format = '/language/%s/feature/%i/' % (lang.slug, feature.id)

    remove = request.GET.get('id', 0)
    try:
        description = descriptions.get(id=remove)
    except Description.DoesNotExist:
        return HttpResponseRedirect(link_format+'history/')
    deleted_is_current = description.current
    description.delete()
    if deleted_is_current:
        new_current_description = descriptions.latest()
        new_current_description.current = True
        new_current_description.save(batch=True)
    request.notification.add('Version as of %s is deleted')
    return HttpResponseRedirect(link_format)

@login_required()
def describe_languagefeature(request, *args, **kwargs):
    me = 'language'
    lang = _get_lang(*args, **kwargs)
    may_edit, (is_admin, is_manager) = may_edit_lang(request.user, lang)
    if not may_edit:
        return HttpResponseForbidden(error_forbidden)

    error = pop_error(request)
    feature = get_object_or_404(Feature, id=kwargs.get('object_id', None))
    lf = get_object_or_404(LanguageFeature, language=lang, feature=feature)
    value_str = '%s_%s' % (feature.id, lf.value.id)
    preview = u''
    preview_value = u''
    link = '/language/%s/feature/%i/' % (lang.slug, feature.id)

    if request.method == 'POST':
        if lf.description:
            descriptionform = DescriptionForm(data=request.POST, instance=lf.description)
        else:
            descriptionform = DescriptionForm(data=request.POST)
        valueform = FeatureValueForm(feature=feature, data=request.POST)

        if descriptionform.is_valid() and valueform.is_valid():
            new_f, new_v = map(int, valueform.cleaned_data.get('value', value_str).split('_'))
            new_fv = FeatureValue.objects.get(feature=feature, id=new_v)
            preview_value = new_fv

            # Need to prevent extraenous saving here because of versioning
            lfd = descriptionform.save(commit=False)
            
            new_xhtml = lfd.make_xhtml()

            if request.POST.get('preview'):
                preview = new_xhtml
                msg = "You are previewing the description of '%s: %s' for %s" % (feature, new_fv, lang)
                request.notifications.add(msg)
            elif request.POST.get('submit'):
                # value
                value_change = ''
                if new_v and new_f == feature.id and new_v != lf.value.id:
                    lf.value = new_fv
                    lf.save()
                    value_change = u'Value now "%s." ' % lf.value
            
                # description
                desc_change = ''
                if not lf.description or lfd.freetext != lf.description.freetext \
                        or new_xhtml != lf.description.freetext_xhtml \
                        or lfd.freetext_type != lf.description.freetext_type:
                    lfd.content_type = ContentType.objects.get_for_model(lf)
                    lfd.object_id = lf.id
                    lfd.save(user=request.user)
                    desc_change = 'Description changed.'
                request.notifications.add('%s%s' % (value_change, desc_change))
                return HttpResponseRedirect(link)
    else:
        valueform = FeatureValueForm(feature=feature, initial={'value': value_str})

        if lf.description:
            descriptionform = DescriptionForm(instance=lf.description)
        else:
            descriptionform = DescriptionForm()

    data = {'me': me,
            'form': descriptionform, 
            'lang': lang, 
            'feature': lf,
            'valueform': valueform,
            'preview': preview,
            'preview_value': preview_value,
            }
    return render_page(request, 'language_description_form.html', data)

# END LF

def show_profile(request, *args, **kwargs):
    me = 'people'
    user = _get_profile(*args, **kwargs)
    profile = None
    whereami = request.META.get('PATH_INFO', None)
    try:
        profile = user.get_profile()
    except Profile.DoesNotExist:
        return HttpResponseNotFound()
    pms, pms_archived, pms_sent = (), (), ()
    if request.user == user:
        pms = PM.objects.received(user)
        pms_archived = PM.objects.archived(user)
        pms_sent = PM.objects.sent(user)
    data = {'object': user, 
            'profile': profile, 
            'me': me, 
            'pms': pms,
            'pms_archived': pms_archived,
            'pms_sent': pms_sent,
            'whereami': whereami,
            }
    return render_page(request, 'profile_detail.html', data)

@login_required()
def change_profile(request, *args, **kwargs):
    me = 'people'
    user = _get_profile(*args, **kwargs)
    if user != request.user:
        return HttpResponseNotFound()
    profile = None
    try:
        profile = user.get_profile()
    except Profile.DoesNotExist:
        return HttpResponseNotFound()
    #web20acc = user.web20.all()

    _LOG.info('User: %s', user)
    _LOG.info('Profile: %s', profile)
    uform = UserForm(instance=user)
    pform = ProfileForm(instance=profile)
    #w20forms = [Web20Form(instance=w20) for w20 in web20acc]
    #new_w20 = Web20Form(prefix="new_w20")
    if request.method == 'POST':
        _LOG.debug('POST %s', request.POST)
        uform = UserForm(data=request.POST, instance=user)
        pform = ProfileForm(data=request.POST, instance=profile)
        if uform.is_valid() and pform.is_valid():
            _LOG.debug('Saving form')
            user = uform.save()
            profile = pform.save()
            _LOG.debug('Form saved')
            _LOG.debug('Country:', profile.country)
            return HttpResponseRedirect('/people/%i' % user.id)
    data = {#'w20forms': w20forms, 
            #'new_w20': new_w20, 
            'uform': uform,
            'pform': pform, 
            'me': me}
    return render_page(request, 'profile_form.html', data)

def show_stats(request, *args, **kwargs):
    me = 'statistics'
    data = {'me': me}

    data.update(generate_global_stats())
    return render_page(request, 'statistics.html', data)

def auth_login(request, *args, **kwargs):
    _LOG.info('Starting auth_login')
    messages = None
    greeting = None
    next = ''
    langs = Language.objects.exclude(slug__startswith='testarossa')
    langs_newest = langs.order_by('-created')[:5]
    langs_modified = langs.order_by('-last_modified')[:5]
    people = User.objects.exclude(username='countach')
    people_recent = people.order_by('-date_joined')[:5]
    trans_ex_recent = TranslationExercise.objects.order_by('-added')[:5]
    if u'next' in request.REQUEST:
        next = request.REQUEST[u'next']
    if request.method == 'POST':
        _LOG.debug('request: %s', request.POST)

        # Login
        if not request.user.is_authenticated():
            username = asciify(smart_unicode(request.POST[u'username'], errors='ignore').strip())
            password = request.POST['password'].strip()
            if username and password:
                try:
                    _LOG.debug('Form valid')
                    try:
                        user = User.objects.get(username=username)
                    except User.DoesNotExist:
                        try:
                            userslug = slugify(username)
                            profile = Profile.objects.get(slug=userslug)
                            user = profile.user
                        except Profile.DoesNotExist:
                            error = "User '%s' does not exist! Typo?" % username
                            request.notifications.add(error, 'error')
                            _LOG.warn("User '%s' does not exist" % username)
                            if u'next' in request.REQUEST:
                                _LOG.warn("Redirecting back to '%s' after failed login" % request.POST[u'next'] or '[redierct missing]')
                                return HttpResponseRedirect(request.POST[u'next'])
                    user = auth.authenticate(username=user.username, password=password)
                    _LOG.info("User: %s", pformat(user))
                    if user is not None:
                        auth.login(request, user)
                    else:
                        _LOG.warn("Invalid user for some reason")
                        error = "Couldn't log you in: Your username and/or password does not match with what is stored here."
                        request.notifications.add(error, 'error')
                except CALSUserExistsError, e:
                    error = "Couldn't sign you up: " + e
                    request.notifications.add(error, 'error')
            if u'next' in request.REQUEST:
                _LOG.info('Redirecting back to %s', request.POST[u'next'])
                return HttpResponseRedirect(request.POST[u'next'])
    l_cloud = Tag.objects.cloud_for_model(Language, steps=7, min_count=2)
    #l_cloud = Tag.objects.cloud_for_model(Language, steps=7)

    data = {'me': 'home', 
            'next': next,
            'news': Entry.objects.order_by('-pub_date')[:2],
            'devel_news': Entry.tagged.with_any(('devel',)).order_by('-pub_date')[:1],
            'language_cloud': l_cloud,
            'langs_newest': langs_newest,
            'langs_modified': langs_modified,
            'trans_exs_newest': trans_ex_recent,
            'people': people_recent,}
    return render_page(request, 'index.html', data)

def page_in_kwargs_or_get(request, kwargs):
    """If an url has the key-value-pair page=<page> in kwargs or
    GET, return the value, else return False."""
    page = kwargs.get(u'page', 0) or request.GET.get(u'page', 0)
    try:
        page = int(page)
    except ValueError:
        if page != u'last':
            page = False
    return page

def in_kwargs_or_get(request, kwargs, key, value):
    """If an url has the key-value-pair key=<value> in kwargs or
    the key <value> in GET, return the value, else return False."""
    assert value, '"value" cannot be empty/false'
    if kwargs.get(key, '') == value or value in request.GET:
        return True
    return False

def show_people_map(request, *args, **kwargs):
    people = User.objects.filter(is_active=True)

def all_people_map(request, *args, **kwargs):
    people = User.objects.filter(is_active=True)

def test(request, *args, **kwargs):
    template = 'test.html'
    data = { 
            'testarossa': Language.objects.get(id=80),
            'langs': Language.objects.all(), 
            'features': Feature.objects.all(),
            'news': Entry.objects.latest('pub_date')
            }
    return render_page(request, template, data)

