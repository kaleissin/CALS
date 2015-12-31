from __future__ import unicode_literals

import logging
_LOG = logging.getLogger(__name__)
_LOG.info(__name__)

from actstream import action as streamaction

from django.conf import settings
from django.contrib.contenttypes.models import ContentType
from django.contrib import messages #.authenticate, auth.login
from django.contrib.auth.decorators import login_required
from django.contrib.auth import get_user_model
from django.db import transaction
from django.db.models import Q
from django.http import (HttpResponseRedirect,
        HttpResponseNotFound,
        HttpResponseForbidden,
        Http404)
from django.shortcuts import get_object_or_404, render, redirect
from django.template.loader import render_to_string
from django.utils.html import escape
from django.views.generic import ListView

from paginators.stringpaginator import SingleLetterPaginator, InvalidPage
from paginators import Paginator

from cals.feature.models import Feature, FeatureValue, Category
from cals.people.models import Profile
from cals.tools.models import Description
from cals.tools.auth import may_edit_lang
from cals.tools.comparison import (
    _generate_comparison_url,
    _generate_comparison_type,
    _compare)
from cals.language.models import Language, LanguageName
from cals.languagefeature.models import LanguageFeature

from cals.tools import uslugify
from cals.forms import FeatureValueForm, CategoryForm, FeatureForm, \
        NewFeatureValueFormSet, DescriptionForm, \
        CompareTwoForm, LanguageForm, EditorForm, SearchForm
from cals.tools import description_diff, compare_features
from cals.modeltools import compare_languages, \
        get_averageness_for_lang, LANGTYPES
from cals.tools.language import random_conlang, conlangs_with_homes

from cals.people.views import auth_login
from cals.language.views import show_language

from cals.feature.views import (show_feature,
    make_feature_list_for_lang,
    set_language_feature_value)

from translations.models import TranslationExercise, Translation

from nano.blog.models import Entry
from nano.blog.tools import get_nano_blog_entries

from tagtools.tools import set_tags_for_model, get_tagcloud_for_model

_error_forbidden_msg = "You don't have the necessary permissions to edit here."
error_forbidden = render_to_string('error.html',
        {'error_message': _error_forbidden_msg })

class CALSError(Exception):
    pass

class CALSUserExistsError(CALSError):
    pass

def _get_lang(all=False, *args, **kwargs):
    if all:
        return get_object_or_404(Language.all_langs, slug=kwargs.get('lang', None))
    return get_object_or_404(Language, slug=kwargs.get('lang', None))

def _get_user(*args, **kwargs):
    return get_object_or_404(settings.AUTH_USER_MODEL, username=kwargs.get('user', None))

def _get_url_pieces(name='slug', **kwargs):
    _LOG.debug('Url-pieces: %s', kwargs)
    if name in kwargs:
        # split on +, remove empty pieces
        pieces = filter(None, kwargs[name].split('+'))
        if pieces:
            return pieces
    return None

def langs_for_user(user):
    if isinstance(user, Profile):
        profile = user
        user = user.user
    else:
        user = user
        profile = user.profile
    return Language.objects.filter(Q(public=True) | Q(manager=user) | Q(editors=user))

# language

def _check_langslugs(langslugs):
    langs = []
    for langslug in langslugs:
        try:
            lang = Language.objects.get(slug=langslug)
        except Language.DoesNotExist:
            continue
        langs.append(lang)
    return langs

class LanguageViewMixin(object):
    queryset = Language.objects.conlangs().order_by('name')

    def get_context_data(self, **kwargs):
        context = super(LanguageViewMixin, self).get_context_data(**kwargs)
        context['me'] = 'language'
        if self.submenu:
            context['submenu'] = self.submenu
        return context

def dispatch_langslugs(request, func_one, func_many, *args, **kwargs):
    """Returns a tuple of (True, payload) if the func is to
    be returned, (False, payload) if the payload will be further
    processed.
    """
    # Check that langslugs are for existing langs
    langslugs = _get_url_pieces(name='slugs', **kwargs)
    if not langslugs:
        return True, HttpResponseForbidden(error_forbidden)
    langs = _check_langslugs(langslugs)
    if len(langs) == 1:
        return func_one(request, langs[0], *args, **kwargs)
    else:
        return func_many(request, langs, *args, **kwargs)

def compare_language(request, *args, **kwargs):
    me = 'language'

    def single_lang(request, lang, *args, **kwargs):
        kwargs['slug'] = lang.slug
        return True, show_language(request, *args, **kwargs)

    def multi_lang(request, langs, *args, **kwargs):
        return False, (langs, [l.slug for l in langs])

    finished, payload = dispatch_langslugs(request, single_lang, multi_lang, *args, **kwargs)
    if finished:
        return payload
    langs, langslugs = payload

    if request.method == 'POST':
        comparison_type = request.POST.get('compare', kwargs.get('opt', None))
        same, different = _generate_comparison_type(comparison_type)

        # remove slugs from langslugs
        remove_langs = request.POST.getlist('removelang')
        if remove_langs:
            langslugs = [l for l in langslugs if l not in remove_langs]
            redirect_to = _generate_comparison_url(langslugs, comparison_type)
            return HttpResponseRedirect(redirect_to)

        if not len(langslugs): # Nothing to compare
            raise Http404
        # Add a slug to langslugs
        return _compare(request, langslugs, comparison_type)

    comparison_type = kwargs.get('opt', request.REQUEST.get('compare', None))
    same, different = _generate_comparison_type(comparison_type)
    cform = CompareTwoForm()
    _LOG.debug('0: %s', comparison_type)
    _LOG.debug('1: same %s, different %s', (same, different))
    comparison = compare_languages(langs, same=same, different=different)
    _LOG.debug('Last: Features compared: %s (%s)', (len(comparison), comparison_type))
    data = {
            'comparison': comparison,
            'me': me,
            'cform': cform,
            'langs': langs,
            'comparison_type': comparison_type,
            }
    return render(request, 'language_compare.html', data)

def search_languages(request, *args, **kwargs):
    me = 'language'

    raw_q = request.GET.get('q', '')
    limit = int(request.GET.get('limit', 10))
    anywhere = request.GET.get('anywhere', False)
    q = uslugify(raw_q)

    if raw_q:
        if q:
            lns = LanguageName.objects.find(q, anywhere)
        else:
            lns = LanguageName.objects.filter(slug='')
        lns = lns.select_related('language').filter(language__visible=True)
        ls = Language.objects.filter(id__in=[ln.language.id for ln in lns])
        ls = ls.order_by()
    else:
        ls = []

    paginator = Paginator(ls, request, per_page=limit, allow_empty_first_page=True)
    pagenum = page_in_kwargs_or_get(request, kwargs) or 1

    try:
        page = paginator.page(pagenum)
    except (InvalidPage):
        raise
        page = paginator.page(paginator.num_pages)

    form = SearchForm(initial={'q': raw_q, 'anywhere': anywhere, 'limit': limit})
    data = {u'me': me,
            u'submenu': 'search',
            u'q': raw_q,
            u'anywhere': anywhere,
            u'limit': limit,
            u'searchform': form,
            u'object_list': page.object_list,
            u'page_obj': page,
            u'paginator': paginator,
            u'is_paginated': True}
    return render(request, 'cals/languagenames_search.html', data)

def denormalize_lang(lang):
    freq = get_averageness_for_lang(lang, scale=100, langtype=LANGTYPES.CONLANG)
    _LOG.info('Freq now: %s' % repr(freq))
    lang.num_features = LanguageFeature.objects.filter(language=lang).count()
    lang.num_avg_features = freq
    lang.set_average_score()
    return lang

def set_featurevalues_for_lang(lang, valuelist):
    """Given a (saved but not committed) language and a list of feature
    value pairs in the form 'featureid_valueid'... """
    for value in valuelist:
        feature_id, value_id = value.split('_')
        if not value_id:
            continue
        set_language_feature_value(lang, feature_id, value_id)
    lang = denormalize_lang(lang)
    return lang

def set_tags_for_lang(tags, lang):
    return set_tags_for_model(tags, lang)

def language_exists(name):
    slug = uslugify(name)
    langs = Language.all_langs.filter(slug=slug)
    if not langs:
        return False
    return True

@login_required
def create_language(request, lang=None, fvlist=None, clone=False, *args, **kwargs):
    me = 'language'
    state = 'new'
    user = request.user

    # sort values into categories
    cats = make_feature_list_for_lang(lang=lang, fvlist=fvlist)

    editorform = EditorForm()

    cloned_from_lang = None
    if clone:
        author = request.user.profile.display_name
        name = 'Clone'
        if lang:
            name = 'Clone of %s' % lang
        elif fvlist:
            name = 'Clone of %i features' % len(fvlist)
        background = name
        langform = LanguageForm(initial={
                'name': name,
                'background': background,
                'author': author})
        cloned_from_lang = lang
    else:
        langform = LanguageForm()

    if request.method == 'POST':
        langform = LanguageForm(data=request.POST, initial=request.POST)
        if langform.is_valid():
            with transaction.atomic():
                lang = langform.save(commit=False)
                if language_exists(lang.name):
                    url = '/language/%s/' % lang.get_slug()
                    msg = '''A language named <a href="%s">%s</a> already
                    exists, you should edit that one or change the name of
                    this one''' % (url, escape(lang.name))
                    messages.error(request, msg)
                else:
                    # Good, not a dupe
                    lang.added_by = user
                    lang.last_modified_by = user
                    if not lang.manager:
                        lang.manager = user
                    # Must save early since is foreign-key in many other tables
                    lang.save(user=user, solo=False)
                    # Save tags if any
                    lang, tags_changed = set_tags_for_lang(langform.cleaned_data['tags'], lang)
                    # Set editors
                    editorform = EditorForm(data=request.POST, instance=lang)
                    if editorform.is_valid():
                        editorform.save()
                    # greeting
                    if lang.greeting:
                        # use signal instead?
                        greetingexercise = TranslationExercise.objects.get(id=1)
                        trans = Translation(translation=lang.greeting, language=lang,
                                translator=user, exercise=greetingexercise)
                        trans.save()

                    # values
                    lang = set_featurevalues_for_lang(lang, request.POST.getlist(u'value'))

                    # Final save
                    lang.save(user=user)
                    if cloned_from_lang:
                        streamaction.send(request.user, verb='cloned the language', action_object=cloned_from_lang, target=lang)
                    else:
                        streamaction.send(request.user, verb='added the language', action_object=lang)
                    messages.info(request, u'You successfully added the language %s to CALS' % lang.name)
                    return HttpResponseRedirect('/language/%s/' % lang.slug)
        else:
            if not clone:
                error = "Couldn't store language-description: " + str(langform.errors)
                messages.error(request, error)
            else:
                help = "Remember to fill out the name and author of the language"
                messages.warn(request, help)
    data = {'form': langform,
            'categories': cats,
            'me': me,
            'editorform': editorform,
            'state': state,
            'clone': clone,
    }
    return render(request, 'language_form.html', data)

@login_required
def clone_language(request, *args, **kwargs):
    me = 'language'
    state = 'clone'
    user = request.user

    def single_lang(request, lang, *args, **kwargs):
        return True, create_language(request, lang=lang, clone=True)

    def multi_lang(request, langs, *args, **kwargs):
        comparison = compare_languages(langs, same=True, different=False)[1:]
        fvlist = [featureline[1] for featureline in comparison]
        return True, create_language(request, fvlist=fvlist, clone=True)

    _, payload = dispatch_langslugs(request, single_lang, multi_lang, *args, **kwargs)

    return payload


def _change_editors_managers(request, manager_then, lang, langform):
    # editors and managers
    if request.user == manager_then:
        editorform = EditorForm(data=request.POST, instance=lang)
        if editorform.is_valid():
            editors_then = set(lang.editors.all())
            lang = editorform.save()
            editors_now = set(lang.editors.all())
            new_editors = editors_now - editors_then
            _LOG.debug('New editors? %s', new_editors)
            for new_editor in new_editors:
                streamaction.send(manager_then, verb='grants edit rights to', action_object=new_editor, target=lang)
            former_editors = editors_then - editors_now
            _LOG.debug('Former editors? %s', former_editors)
            for former_editor in former_editors:
                streamaction.send(manager_then, verb='revokes edit rights from', action_object=former_editor, target=lang)
            manager_now = lang.manager
            _LOG.debug('Manager then: %s', manager_then)
            _LOG.debug('Manager now: %s', manager_now)
            if manager_now != manager_then:
                streamaction.send(manager_then, verb='retires as manager of', target=lang)
                streamaction.send(manager_now, verb='is the new manager of', target=lang)
        else:
            _LOG.debug('Editorform invalid: %s', editorform)
        if not 'manager' in langform.cleaned_data:
            lang.manager = manager_then
    else:
        _LOG.debug('User %s may not manage %s, manager is %s', request.user, lang, manager_then)
        # Just in case: must be manager also in view in order to
        # change who can be manager
        lang.manager = manager_then
    return lang

@login_required
def change_language(request, *args, **kwargs):
    me = 'language'
    state = 'change'
    lang = _get_lang(*args, **kwargs)
    old_name = lang.name
    user = request.user

    may_edit, (is_admin, is_manager) = may_edit_lang(user, lang)
    if not may_edit:
        return HttpResponseForbidden(error_forbidden)

    _LOG.info('%s about to change %s', (user, lang))

    langform = LanguageForm(instance=lang)
    #profile = user.profile
    manager = lang.manager
    if is_manager:
        editorform = EditorForm(instance=lang)
    else:
        editorform = None
    _LOG.info('User is manager: %s', user == lang.manager)
    # sort values into categories
    cats = make_feature_list_for_lang(lang)

    if request.method == 'POST':
        langform = LanguageForm(data=request.POST, instance=lang, initial=request.POST)
        try:
            if langform.is_valid():
                with transaction.atomic():
                    new_lang = langform.save(commit=False)
                    new_name = new_lang.name
                    if new_name != old_name and language_exists(new_name):
                        new_name = escape(new_name)
                        url = '/language/%s/' % lang.get_slug()
                        msg = '''The name "%s" is taken,
                        see <a href="%s">%s</a>''' % (new_name, url, new_name)
                        messages.error(request, msg)
                    else:
                        _LOG.info('Actually changing %s!', lang)

                        lang = _change_editors_managers(request, manager, new_lang, langform)

                        lang.last_modified_by = user

                        # break out in separate function
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
                        # values
                        lang = set_featurevalues_for_lang(lang, request.POST.getlist(u'value'))

                        # Final save
                        lang.save(user=user)
                        lang, tags_changed = set_tags_for_lang(langform.cleaned_data['tags'], lang)
                        streamaction.send(user, verb='updated', action_object=lang)
                        return HttpResponseRedirect('.')
            else:
                error = "Couldn't change language-description: " + str(langform.errors)
                messages.error(request, error)
        except ValueError:
            assert False, langform
    data = {'form': langform,
            'categories': cats,
            'editorform': editorform,
            #'moreinfoformset': moreinfoformset,
            'me': me,
            'state': state,}
    return render(request, 'language_form.html', data)

def list_natlangs(request, *args, **kwargs):
    return language_list(request, natlang=True, *args, **kwargs)

def list_conlangs(request, *args, **kwargs):
    return language_list(request, natlang=False, *args, **kwargs)

def show_random_conlang(request, *args, **kwargs):
    random = random_conlang()
    return redirect('/language/%s/' % random, *args, **kwargs)

class LanguageList(LanguageViewMixin, ListView):
    template_name = 'cals/language_list.html'
langauge_list_test = LanguageList.as_view()

class LanguageHomepageList(LanguageList):
    queryset = conlangs_with_homes()
    template_name = 'cals/language/homepage_list.html'
    submenu = 'homepage'
list_conlang_homepages = LanguageHomepageList.as_view()

def list_languages(request, *args, **kwargs):
    """Select and dispatch to a view of the list of languages"""

    me = 'language'

    mapping = {
        'cloud': language_cloud,
        'jrk': language_jrklist,
        'jrklist': language_jrklist,
        'natlang': list_natlangs,
        'conlang': list_conlangs,
        'random': show_random_conlang,
        'homepage': list_conlang_homepages,
    }

    action = in_kwargs_or_get2(request, kwargs, 'action', *mapping.keys())
    if action:
        return mapping[action](request, *args, **kwargs)
    form = SearchForm()
    data = {
        'me': me,
        'submenu': 'overview',
        'searchform': form
    }
    return render(request, 'cals/language_index.html', data)

class LanguageCloud(LanguageViewMixin, ListView):
    template_name = 'cals/language/cloud.html'
    queryset = Language.objects.conlangs().order_by('name')
    submenu = 'cloud'

    def get_context_data(self, **kwargs):
        context = super(LanguageCloud, self).get_context_data(**kwargs)
        langs = []
        for lang in self.get_queryset():
            langs.append({'slug': lang.slug,
                    'size': int(round(lang.get_infodensity() * 6)) + 1,
                    'name': lang.name,
            })
        context['langs'] = langs
        return context
language_cloud = LanguageCloud.as_view()

class ListJRKLanguageView(LanguageViewMixin, ListView):
    queryset = LanguageName.objects.filter(language__natlang=False).exclude(language__background='').order_by('name')
    template_name = 'cals/language/jrklist.html'
    submenu = 'jrk'
language_jrklist = ListJRKLanguageView.as_view()

def language_list(request, natlang=False, *args, **kwargs):
    if natlang or in_kwargs_or_get(request, kwargs, 'action', 'natlang'):
        natlang = True
        queryset = Language.objects.natlangs().order_by('name')
    else:
        queryset = Language.objects.conlangs().order_by('name')
    paginator = SingleLetterPaginator(queryset, on="name", request=request)
    page = page_in_kwargs_or_get(request, kwargs) or 1

    try:
        page = paginator.page(page)
    except (InvalidPage):
        page = paginator.page(paginator.num_pages)

    submenu = 'alphabetic' if not natlang else 'natlang'
    data = {u'me': u'language',
            u'submenu': submenu,
            u'object_list': page.object_list,
            u'natlang': natlang,
            u'page_obj': page,
            u'paginator': paginator,
            u'is_paginated': True}

    return render(request, 'cals/language_list.html', data)

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

def in_kwargs_or_get2(request, kwargs, key, *values):
    assert values and values[0], 'At least one non-falsey value needed'
    value = kwargs.get(key, '')
    if value in values:
        return value
    if key in request.GET:
        value = request.GET[key]
        if value in values:
            return value
    for query in request.GET.keys():
        if query in values:
            return query
    return False

def in_kwargs_or_get(request, kwargs, key, value):
    """If an url has the key-value-pair key=<value> in kwargs or
    the key <value> in GET, return the value, else return False."""
    assert value, '"value" cannot be empty/false'
    if kwargs.get(key, '') == value:
        return value
    if value in request.GET:
        return value
    return False

def test(request, *args, **kwargs):
    template = 'test.html'
    data = {
            'testarossa': Language.objects.get(id=80),
            'langs': Language.objects.all(),
            'features': Feature.objects.all(),
            'news': Entry.objects.latest('pub_date')
            }
    return render(request, template, data)

def home(request, *args, **kwargs):
    _LOG.info('Homepage')
    greeting = None
    nexthop = ''
    nextfield = u'next'
    User = get_user_model()
    langs = Language.objects.exclude(slug__startswith='testarossa')
    langs_newest = langs.order_by('-created')[:5]
    langs_modified = langs.order_by('-last_modified')[:5]
    people = User.objects.exclude(username='countach')
    people_recent = people.order_by('-date_joined')[:5]
    trans_ex_recent = TranslationExercise.objects.order_by('-added')[:5]
    if nextfield in request.REQUEST:
        nexthop = request.REQUEST[nextfield]
    if request.method == 'POST':
        _LOG.debug('request: %s', request.POST)

        did_login = auth_login(request, *args, **kwargs)
        if did_login:
            return did_login

    l_cloud = get_tagcloud_for_model(Language, steps=7, min_count=2)

    news, devel_news = get_nano_blog_entries()

    data = {'me': 'home',
            'next': nexthop,
            'news': news,
            'devel_news': devel_news,
            'language_cloud': l_cloud,
            'langs_newest': langs_newest,
            'langs_modified': langs_modified,
            'trans_exs_newest': trans_ex_recent,
            'people': people_recent,}
    return render(request, 'index.html', data)
