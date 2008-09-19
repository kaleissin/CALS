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
from django.views.generic.list_detail import object_list
from django.views.generic.create_update import delete_object
from django.utils.encoding import smart_unicode

from tagging.models import Tag

from pygooglechart import StackedVerticalBarChart, Axis

from cals.models import *
from cals.forms import *
from cals.statistics import *

from nano.tools import *
from nano.blog.models import Entry

show_error = loader.get_template('error.html')

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

def _get_url_pieces(name='slug', **kwargs):
    LOG.error('Url-pieces: %s' % kwargs)
    if name in kwargs:
        # split on +, remove empty pieces
        pieces = filter(None, kwargs[name].split('+'))
        if pieces:
            return pieces
    # '%s not in kwargs: %s' % (name, pformat(kwargs))
    return None

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
            f = Feature.objects.get(id=feature)
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
        raise Http404
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
         feature = Feature.objects.get(id=kwargs['object'])
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

@login_required()
def create_language(request, *args, **kwargs):
    me = 'language'
    error = pop_error(request)
    langform = LanguageForm()

    # sort values into categories
    categories = Category.objects.all().select_related().order_by('id')
    cats = []
    for category in categories:
        try:
            fvs = FeatureValue.objects.filter(feature__category=category)
        except FeatureValue.DoesNotExist:
            continue
        features = Feature.objects.filter(category=category)
        f = []
        for feature in features:
            form = FeatureValueForm(feature=feature)
            f.append({'feature': feature, 'form':form})
        if f:
            cats.append({'name': category.name, 'features': f})
        else:
            cats.append({'name': category.name})

    greetingexercise = TranslationExercise.objects.get(id=1)
    if request.method == 'POST':
        langform = LanguageForm(data=request.POST, initial=request.POST)
        if langform.is_valid():
            lang = langform.save(commit=False)
            lang.added_by = request.user
            lang.save(solo=False)
            # greeting
            greeting = langform.cleaned_data[u'greeting']
            if greeting:
                trans = Translation(translation=greeting,language=lang,
                        translator=request.user,exercise=greetingexercise)
                trans.save()
            else:
                trans = None
            lang.greeting = trans
            # values
            for value_id in request.POST.getlist(u'value'):
                if not value_id:
                    continue
                fv = FeatureValue.objects.get(id=int(value_id))
                feature = Feature.objects.get(id=fv.feature_id)
                lf = LanguageFeature.objects.create(language=lang, feature=feature, value=fv)
                lf.save()
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
            'error': error}
    return render_page(request, 'language_form.html', data)

def may_edit_lang(user, language):
    standardreturn = (True, (False, False))
    if language.public:
        return standardreturn
    if user.is_superuser:
        return True, (True, True)
    profile = user.get_profile()
    if profile == language.manager:
        return True, (False, True)
    if profile in language.editors.all():
        return standardreturn
    return False, (False, False)

@login_required()
def change_language(request, *args, **kwargs):
    me = 'language'
    error = pop_error(request)
    lang = _get_lang(*args, **kwargs)
    user = request.user

    may_edit, (is_admin, is_manager) = may_edit_lang(user, lang)
    if not may_edit:
        error_message = "You don't have the necessary permissions to edit %s." % lang.name
        c = Context({ 'error_message': error_message,})
        return HttpResponseForbidden(show_error.render(c))

    LOG.critical('Stopped here')
    try:
        greeting = lang.greeting
    except Translation.DoesNotExist:
        greeting = ''
    langform = LanguageForm(instance=lang, initial={'greeting': greeting})
    #profile = user.get_profile()
    #is_manager = user.get_profile() == lang.manager
    if is_manager:
        editorform = EditorForm(instance=lang)
    else:
        editorform = None
    LOG.error('User is manager: %s' % request.user == lang.manager.user)
    # sort values into categories
    categories = Category.objects.all().select_related().order_by('id')
    cats = []
    for category in categories:
        try:
            fvs = FeatureValue.objects.filter(feature__category=category)
        except FeatureValue.DoesNotExist:
            continue
        features = Feature.objects.filter(category=category)
        f = []
        for feature in features:
            lf = None
            try:
                lf = LanguageFeature.objects.get(language=lang, feature=feature)
            except LanguageFeature.DoesNotExist:
                pass
            if lf:
                print feature, 'exists:', lf.value
                form = FeatureValueForm(feature=feature,
                        initial={'value': lf.value.id})
                        #instance=lf.value, initial={'name': lf.value.id})
            else:
                form = FeatureValueForm(feature=feature)
            f.append({'feature': feature, 'form':form})
            lf = None
        if f:
            cats.append({'name': category.name, 'features': f})
        else:
            cats.append({'name': category.name})

    greetingexercise = TranslationExercise.objects.get(id=1)
#     try:
#         greeting = Translation.objects.get(language=lang, exercise=greetingexercise)
#     except Translation.DoesNotExist:
#         pass
    if request.method == 'POST':
        langform = LanguageForm(data=request.POST, instance=lang, initial=request.POST)
        if langform.is_valid():
            editorform = EditorForm(data=request.POST, instance=lang)
            old_manager = lang.manager
            old_editors = lang.editors
            old_greeting = lang.greeting #translations.get(exercise=greetingexercise)
            lang = langform.save()
            # editors and managers
            if not 'manager' in langform.cleaned_data:
                lang.manager = old_manager
            if is_manager and editorform.is_valid():
                editors = editorform.save()
                LOG.error('editors: %s' % editors)
            # greeting
            new_greeting = langform.cleaned_data.get(u'greeting', None)
            if new_greeting: 
                greeting = Translation(language=lang,
                        exercise=greetingexercise,
                        translation=greeting,
                        translator=request.user)
                if old_greeting and old_greeting != new_greeting:
                    try:
                        old_greeting.translator = request.user
                        old_greeting.translation = new_greeting
                        old_greeting.save()
                    except Translation.DoesNotExist:
                        greeting.save()
                        lang.greeting = greeting
                else:
                    greeting.save()
                    lang.greeting = greeting
            else:
                if old_greeting:
                    Translation.objects.filter(id=old_greeting.id).delete()
            # values
            for value_id in request.POST.getlist(u'value'):
                if not value_id:
                    print 'skip'
                    continue
                print 'Value:', value_id
                fv = FeatureValue.objects.get(id=int(value_id))
                feature = Feature.objects.get(id=fv.feature_id)
                try:
                    lf_old = LanguageFeature.objects.get(language=lang, feature=feature)
                except LanguageFeature.DoesNotExist:
                    lf_new = LanguageFeature.objects.create(language=lang, feature=feature, value=fv)
                else:
                    if lf_old.value != fv:
                        lf_old.value = fv
                        lf_old.save()
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
            'me': me, 
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
            lf = form.save()
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
    data = {'object': user, 
            'profile': profile, 
            'me': me, 
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
    web20acc = user.web20.all()

    LOG.error('User: %s', user)
    LOG.error('Profile: %s', profile)
    uform = UserForm(instance=user)
    pform = ProfileForm(instance=profile)
    w20forms = [Web20Form(instance=w20) for w20 in web20acc]
    new_w20 = Web20Form(prefix="new_w20")
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
    data = {'w20forms': w20forms, 
            'new_w20': new_w20, 
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
    #l_cloud = Tag.objects.cloud_for_model(Language, steps=7, min_count=2)
    l_cloud = Tag.objects.cloud_for_model(Language, steps=7)

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

# @login_required
# def password_change(request, *args, **kwargs):
#     error = pop_error(request)
#     template_name = 'password_change_form.html'
#     if request.method == "POST":
#         form = PasswordChangeForm(request.POST)
#         if form.is_valid():
#             password = form.cleaned_data[u'password2']
#             user = request.user
#             user.set_password(password)
#             user.save()
#             request.session['error'] = None
#             return HttpResponseRedirect('/password/change/done/')
#     else:
#         form = PasswordChangeForm()
#     data = { 'form': form,
#             'error': error,}
#     return render_page(request, template_name, data)
# 
# def password_reset(request, *args, **kwargs):
#     error = pop_error(request)
#     template = 'password_reset_form.html'
#     help_message = None
#     e_subject = 'CALS password assistance'
#     e_message = """Your new password is: 
# 
# %s
# 
# It is long deliberately, so change it to 
# something you'll be able to remember.
# 
# 
# CALS' little password-bot
# """
#     e_from = 'kaleissin+cals@gmail.com'
#     form = PasswordResetForm()
#     if request.method == 'POST':
#         form = PasswordResetForm(request.POST)
#         if form.is_valid():
#             user = get_object_or_404(User, username=form.cleaned_data['username'])
#             if user.email:
#                 tmp_pwd = random_password()
#                 user.set_password(tmp_pwd)
#                 result = send_mail(subject=e_subject, from_email=e_from, message=e_message % tmp_pwd, recipient_list=(user.email,))
#                 user.save()
#                 request.session['error'] = None
#                 return HttpResponseRedirect('/password/reset/sent/')
#             else:
#                 error = """There's no email-address registered for '%s',
# the password can't be reset. Try leaving a ticket at <a href="http://trac.aldebaaran.uninett.no/cals/">Bugs and features</a>."""
#                 request.session['error'] = error
#                 
#     data = {'form': form,
#             'help_message': help_message,
#             'error':error}
#     return render_page(request, template, data)

def show_languagetranslations(request, *args, **kwargs):
    me = 'language'
    error = pop_error(request)
    template = 'cals/languagetranslation_list.html'
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

@login_required
def add_languagetranslations(request, *args, **kwargs):
    me = 'language'
    error = pop_error(request)
    template = 'languagetranslation_form.html'
    help_message = ''
    lang = _get_lang(*args, **kwargs)
    exercise = _get_exercise(*args, **kwargs)
    form = LanguageTranslationForm()
    if request.method == 'POST':
        form = LanguageTranslationForm(request.POST)
        if form.is_valid():
            trans = Translation()
            trans.translation = form.cleaned_data['translation']
            trans.translator = request.user
            trans.language = lang
            trans.exercise = exercise
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
    me = 'language'
    error = pop_error(request)
    template = 'languagetranslation_form.html'
    help_message = ''
    lang = _get_lang(*args, **kwargs)
    exercise = _get_exercise(*args, **kwargs)
    trans = Translation.objects.get(language=lang, translator=request.user, exercise=exercise)
    form = LanguageTranslationForm(initial={'translation': trans})
    if request.method == 'POST':
        form = LanguageTranslationForm(data=request.POST, initial={'translation': trans})
        if form.is_valid():
            trans.translation = form.cleaned_data.get('translation', '')
            trans.save()
            request.session['error'] = None
            return HttpResponseRedirect('..')
    data = {'form': form,
            'exercise': exercise, 'help_message': help_message,
            'error':error, 'me': me}
    return render_page(request, template, data)

def show_translationexercise(request, *args, **kwargs):
    me = 'translation'
    error = pop_error(request)
    exercises = TranslationExercise.objects.all()
    extra_context={'me': me, 'error': error,}
    return object_list(request, queryset=exercises, 
            extra_context=extra_context)

def show_translation(request, *args, **kwargs):
    me = 'translation'
    error = pop_error(request)
    exercise = _get_exercise(*args, **kwargs)
    trans = exercise.translations.exclude(translation__isnull=True).exclude(translation='').order_by('language')
    extra_context={'me': me, 'error': error,}
    return object_list(request, queryset=trans, #template_name=template,
            extra_context=extra_context)

@login_required
def delete_languagetranslations(request, *args, **kwargs):
    me = 'language'
    template = 'delete.html'
    error = pop_error(request)
    lang = _get_lang(*args, **kwargs)
    exercise = _get_exercise(*args, **kwargs)
    trans = Translation.objects.get(language=lang, translator=request.user, exercise=exercise)
    extra_context={'me': me, 'error': error,}
    return delete_object(request, model=Translation, object_id=trans.id,
            post_delete_redirect="..", extra_context=extra_context)

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

