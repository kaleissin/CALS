# Create your views here.
from pprint import pprint, pformat
from random import choice, sample
import time
import unicodedata
import string
import sys
from datetime import datetime
sys.stderr = sys.stdout

from cals import getLogger
LOG = getLogger('cals.views')

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

from translation.models import TranslationExercise, Translation

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

def _get_exercise(*args, **kwargs):
    #assert False, kwargs.get('exercise', None)
    return get_object_or_404(TranslationExercise, slug=kwargs.get('exercise', None))

def _get_profile(*args, **kwargs):
    return get_object_or_404(User, id=kwargs.get('object_id', None))

def _get_user(*args, **kwargs):
    return get_object_or_404(User, username=kwargs.get('user', None))

def _get_url_pieces(name='slug', **kwargs):
    LOG.debug('Url-pieces: %s' % kwargs)
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
    return Language.objects.filter(Q(public=True) | Q(manager=profile) | Q(editors=user))

def compare_feature(request, *args, **kwargs):
    me = 'feature'
    error = pop_error(request)
    features = _get_url_pieces(name='objects', **kwargs)
    if not features:
        # 'No feature'
        return HttpResponseNotFound()
    if len(features) == 1:
        # 'One feature'
        kwargs['object'] = features[0]
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
            'error': error,
            'features': fs,
            'fvs': fvs,
            }
    return render_page(request, 'feature_compare.html', data)

def compare_language(request, *args, **kwargs):
    me = 'language'
    error = pop_error(request)
    langslugs = _get_url_pieces(name='slugs', **kwargs)
    comparison_type = kwargs.get('opt', None)
    LOG.error('Will compare %s' % langslugs)
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
    LOG.error('0: %s' % comparison_type)
    LOG.error('1: same %s, different %s' % (same, different))
    comparison = compare_languages(langs, same=same, different=different)
    LOG.error('Last: Features compared: %s (%s)' % (len(comparison), comparison_type))
    data = {
            'comparison': comparison, 
            'me': me,
            'langs': langs,
            'error': error,
            'comparison_type': comparison_type,
            }
    return render_page(request, 'language_compare.html', data)

def show_people_map(request, *args, **kwargs):
    people = User.objects.filter(is_active=True)

def all_people_map(request, *args, **kwargs):
    people = User.objects.filter(is_active=True)

def show_language(request, *args, **kwargs):
    me = 'language'
    error = pop_error(request)
    lang = _get_lang(*args, **kwargs)
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
            'error': error,
    }
    return render_page(request, 'language_detail.html', data)

def list_feature(request, *args, **kwargs):
    error = pop_error(request)
    extra_context = {'me': 'feature', 'error': error}
    queryset = Category.objects.all().order_by('id')
    template = 'cals/feature_list.html'
    return object_list(queryset=queryset, template_name=template,
            extra_context=extra_context)

def show_feature(request, *args, **kwargs):
    me = 'feature'
    error = pop_error(request)
    try:
         feature = Feature.objects.active().get(id=kwargs['object'])
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
            'error': error,
            'cform': cform}
    return render_page(request, 'feature_detail.html', data)

def add_entry_to_blog(object, headline, template, date_field=None):
    data = {'obj': object}
    template = loader.render_to_string(template, dictionary=data)
    pub_date = object.__dict__.get(date_field or 'last_modified', datetime.now())
    blog_entry = Entry.objects.create(content=template,headline=headline,pub_date=pub_date)

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
            if lang:
                try:
                    lf = LanguageFeature.objects.get(language=lang, feature=feature)
                    form = FeatureValueForm(feature=feature,
                            initial={'value': '%s_%s' % (feature.id, lf.value.id)})
                            #instance=lf.value, initial={'name': lf.value.id})
                except LanguageFeature.DoesNotExist:
                    pass
            f.append({'feature': feature, 'form':form})
        if f:
            cats.append({'name': category.name, 'features': f})
        else:
            cats.append({'name': category.name})
    return cats

@login_required()
def create_language(request, *args, **kwargs):
    me = 'language'
    state = 'new'
    error = pop_error(request)
    langform = LanguageForm()

    editorform = EditorForm()

    # sort values into categories
    cats = make_feature_list_for_lang()

    if request.method == 'POST':
        langform = LanguageForm(data=request.POST, initial=request.POST)
        if langform.is_valid():
            lang = langform.save(commit=False)
            lang.added_by = request.user
            lang.last_modified_by = request.user
            lang.save(solo=False)
            editorform = EditorForm(data=request.POST, instance=lang)
            if editorform.is_valid():
                editorform.save()
            # greeting
            if lang.greeting:
                # use signal instead?
                greetingexercise = TranslationExercise.objects.get(id=1)
                trans = Translation(translation=lang.greeting,language=lang,
                        translator=request.user,exercise=greetingexercise)
                trans.save()
            # values
            for value in request.POST.getlist(u'value'):
                feature_id, value_id = value.split('_')
                if not value_id:
                    continue
                set_language_feature_value(lang, feature_id, value_id)
            freq = get_averageness_for_lang(lang, scale=100)
            LOG.error('Freq now: %s' % repr(freq))
            lang.num_features = LanguageFeature.objects.filter(language=lang).count()
            lang.num_avg_features = freq
            lang.set_average_score()
            lang.save()
            request.session['error'] = None
            if not u'testarossa' in lang.slug:
                add_entry_to_blog(lang, 'New language: %s' % lang.name, 'feeds/languages_newest_description.html', date_field='created')
            return HttpResponseRedirect('.')
        else:
            error = "Couldn't store language-description: " + str(form.errors) 
            request.session['error'] = error
    data = {'form': langform, 
            'categories': cats, 
            'me': me, 
            'editorform': editorform,
            'state': state,
            'error': error}
    return render_page(request, 'language_form.html', data)

def may_edit_lang(user, language):
    standardreturn = (True, (False, False))
    profile = user.get_profile()
    if profile == language.manager:
        return True, (False, True)
    if user in language.editors.all():
        return standardreturn
    if language.public:
        return standardreturn
    if user.is_superuser:
        return True, (True, True)
    return False, (False, False)

@login_required()
def change_language(request, *args, **kwargs):
    me = 'language'
    state = 'change'
    error = pop_error(request)
    lang = _get_lang(*args, **kwargs)
    user = request.user

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
    LOG.error('User is manager: %s' % request.user == lang.manager.user)
    # sort values into categories
    cats = make_feature_list_for_lang(lang)

    if request.method == 'POST':
        langform = LanguageForm(data=request.POST, instance=lang, initial=request.POST)
        if langform.is_valid():
            # editors and managers
            if is_manager:
                editorform = EditorForm(data=request.POST, instance=lang)
                old_manager = lang.manager
                editors = lang.editors
                if not 'manager' in langform.cleaned_data:
                    lang.manager = old_manager
                if editorform.is_valid():
                    editors = editorform.save()
                    LOG.error('editors: %s' % editors)
            lang.last_modified_by = request.user
            lang = langform.save()
            # greeting
            greetingexercise = TranslationExercise.objects.get(id=1)
            new_greeting = lang.greeting
            try:
                greetingtrans = Translation.objects.get(language=lang, exercise=greetingexercise,
                        translator=request.user)
            except Translation.DoesNotExist:
                greetingtrans = None
            if new_greeting:
                if greetingtrans:
                    if new_greeting != greetingtrans.translation:
                        greetingtrans.translation = new_greeting
                else:
                    Translation.objects.create(language=lang,
                            exercise=greetingexercise, translator=request.user,
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
            lang.save()
            if not u'testarossa' in lang.slug:
                add_entry_to_blog(lang, 'Changed language: %s' % lang.name,
                        'feeds/languages_description.html',
                        date_field='last_modified')
            request.session['error'] = None
            return HttpResponseRedirect('.')
        else:
            error = "Couldn't change language-description: " + str(langform.errors)
            request.session['error'] = error
    data = {'form': langform, 
            'categories': cats, 
            'editorform': editorform, 
            #'moreinfoformset': moreinfoformset,
            'me': me, 
            'state': state,
            'error': error}
    return render_page(request, 'language_form.html', data)

@login_required()
def change_description(request, *args, **kwargs):
    me = 'feature'
    error = pop_error(request)
    feature = get_object_or_404(Feature, id=kwargs.get('object_id', None))
    link = '/feature/%i/description/' % feature.id
    if not request.user.is_staff:
        return HttpResponseRedirect(link)
    if request.method == 'POST':
        form = FeatureDescriptionForm(data=request.POST, instance=feature)
        if form.is_valid():
            feature = form.save()
            request.session['error'] = None
            return HttpResponseRedirect(link)
    else:
        form = FeatureDescriptionForm(instance=feature)
    data = {'me': me,
            'form': form,
            'feature': feature,
            'error': error}
    return render_page(request, 'feature_description_form.html', data)

def show_languagefeature(request, *args, **kwargs):
    me = 'language'
    error = pop_error(request)
    lang = _get_lang(*args, **kwargs)
    feature = get_object_or_404(Feature, id=kwargs.get('object_id', None))
    lf = get_object_or_404(LanguageFeature, language=lang, feature=feature)
    descriptions = get_languagefeature_descriptions(lf=lf)
    description = None
    if descriptions:
        description = descriptions[0]
    link = '/language/%s/feature/%i/' % (lang.slug, feature.id)
    data = {'me': me,
            'description': description,
            'lang': lang, 'feature': lf,
            'error': error}
    return render_page(request, 'language_description_detail.html', data)

@login_required()
def describe_languagefeature(request, *args, **kwargs):
    me = 'language'
    error = pop_error(request)
    lang = _get_lang(*args, **kwargs)
    feature = get_object_or_404(Feature, id=kwargs.get('object_id', None))
    lf = get_object_or_404(LanguageFeature, language=lang, feature=feature)
    may_edit, (is_admin, is_manager) = may_edit_lang(request.user, lang)
    if not may_edit:
        return HttpResponseForbidden(error_forbidden)
    descriptions = get_languagefeature_descriptions(lf=lf)
    if descriptions:
        description = descriptions[0]
    link = '/language/%s/feature/%i/' % (lang.slug, feature.id)
    if request.method == 'POST':
        if descriptions:
            form = DescriptionForm(data=request.POST, instance=descriptions[0])
        else:
            form = DescriptionForm(data=request.POST)
        if form.is_valid():
            lfd = form.save(commit=False)
            lfd.content_type = ContentType.objects.get_for_model(lf)
            lfd.object_id = lf.id
            lfd.save(user=request.user)
            request.session['error'] = None
            return HttpResponseRedirect(link)
    else:
        if descriptions:
            form = DescriptionForm(instance=descriptions[0])
        else:
            form = DescriptionForm()
    data = {'me': me,
            'form': form, 'lang': lang, 'feature': lf,
            'error': error}
    return render_page(request, 'language_description_form.html', data)

def show_profile(request, *args, **kwargs):
    me = 'people'
    error = pop_error(request)
    user = _get_profile(*args, **kwargs)
    profile = None
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
            'error': error}
    return render_page(request, 'profile_detail.html', data)

def show_stats(request, *args, **kwargs):
    me = 'statistics'
    error = pop_error(request)
    data = {'me': me, 
            'error': error}

    data.update(generate_global_stats())
    return render_page(request, 'statistics.html', data)

@login_required()
def change_profile(request, *args, **kwargs):
    me = 'people'
    error = pop_error(request)
    user = _get_profile(*args, **kwargs)
    if user != request.user:
        return HttpResponseNotFound()
    profile = None
    try:
        profile = user.get_profile()
    except Profile.DoesNotExist:
        return HttpResponseNotFound()
    #web20acc = user.web20.all()

    LOG.error('User: %s', user)
    LOG.error('Profile: %s', profile)
    uform = UserForm(instance=user)
    pform = ProfileForm(instance=profile)
    #w20forms = [Web20Form(instance=w20) for w20 in web20acc]
    #new_w20 = Web20Form(prefix="new_w20")
    if request.method == 'POST':
        LOG.error('POST %s', request.POST)
        uform = UserForm(data=request.POST, instance=user)
        pform = ProfileForm(data=request.POST, instance=profile)
        if uform.is_valid() and pform.is_valid():
            LOG.error('Saving form')
            user = uform.save()
            profile = pform.save()
            LOG.error('Form saved')
            LOG.error('Country:', profile.country)
            request.session['error'] = None
            return HttpResponseRedirect('/people/%i' % user.id)
    data = {#'w20forms': w20forms, 
            #'new_w20': new_w20, 
            'uform': uform,
            'pform': pform, 
            'me': me, 
            'error': error}
    return render_page(request, 'profile_form.html', data)

def auth_login(request, *args, **kwargs):
    LOG.critical('Starting auth_login')
    error = None
    messages = None
    greeting = None
    next = ''
    langs = Language.objects.exclude(slug__startswith='testarossa')
    langs_newest = langs.order_by('-created')[:5]
    langs_modified = langs.order_by('-last_modified')[:5]
    people = User.objects.exclude(username='countach')
    people_recent = people.order_by('-date_joined')[:5]
    if u'next' in request.REQUEST:
        next = request.REQUEST[u'next']
    if not request.user.is_authenticated():
        if request.method == 'POST':
            LOG.critical('request: %s', request.POST)
            username = asciify(smart_unicode(request.POST[u'username'], errors='ignore').strip())
            password = request.POST['password'].strip()
            if username and password:
                try:
                    LOG.critical('Form valid')
                    try:
                        user = User.objects.get(username=username)
                    except User.DoesNotExist:
                        error = "User '%s' does not exist! Typo?" % username
                        request.session['error'] = error
                        LOG.critical('User does not exist')
                        if u'next' in request.REQUEST:
                            LOG.error('Redirecting back to %s', request.POST[u'next'])
                            errorstring = ''
                            if error:
                                errorstring = '?error='+error
                            return HttpResponseRedirect(request.POST[u'next']+errorstring)
                    user = auth.authenticate(username=username, password=password)
                    LOG.critical("User: %s", pformat(user))
                    if user is not None:
                        auth.login(request, user)
                        request.session['error'] = None
                    else:
                        LOG.critical("Invalid user for some reason")
                        error = "Couldn't log you in: Your username and/or password does not match with what is stored here."
                        request.session['error'] = error
                        messages = [error]
                except CALSUserExistsError, e:
                    error = "Couldn't sign you up: " + e
                    request.session['error'] = error
            if u'next' in request.REQUEST:
                LOG.error('Redirecting back to %s', request.POST[u'next'])
                return HttpResponseRedirect(request.POST[u'next'])
    l_cloud = Tag.objects.cloud_for_model(Language, steps=7, min_count=2)
    #l_cloud = Tag.objects.cloud_for_model(Language, steps=7)

    data = {'me': 'home', 
            'error': error, 
            'next': next,
            'news': Entry.objects.order_by('-pub_date')[:2],
            'language_cloud': l_cloud,
            'langs_newest': langs_newest,
            'langs_modified': langs_modified,
            'people': people_recent,
            'messages': messages}
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

def change_or_add_feature(request, *args, **kwargs):
    categoryform = CategoryForm()
    featureform = FeatureForm()
    valueformset = NewFeatureValueFormSet()

    data = {u'me': u'feature',
        'featureform': featureform,
        'fvformset': valueformset,
    }

    return render_page(request, 'cals/suggested_feature_form.html', data)

def test(request, *args, **kwargs):
    error = pop_error(request)
    template = 'test.html'
    data = { 
            'testarossa': Language.objects.get(id=80),
            'langs': Language.objects.all(), 
            'features': Feature.objects.all(),
            'error': error,
            'news': Entry.objects.latest('pub_date')
            }
    return render_page(request, template, data)

