import logging
_LOG = logging.getLogger(__name__)
_LOG.info(__name__)

from actstream import action as streamaction

from django.contrib.contenttypes.models import ContentType
from django.contrib import messages #.authenticate, auth.login
from django.contrib.auth.decorators import login_required
from django.contrib.auth.models import User
from django.http import (HttpResponseRedirect,
        HttpResponseNotFound,
        HttpResponseForbidden,
        Http404)
from django.shortcuts import get_object_or_404, render
from django.template.loader import render_to_string
from django.views.generic import ListView
from django.db.models import Q

from paginators.stringpaginator import SingleLetterPaginator, InvalidPage
from paginators import Paginator

from cals.feature.models import Feature, FeatureValue, Category
from cals.people.models import Profile
from cals.tools.models import Description
from cals.language.models import Language, LanguageName
from cals.models import LanguageFeature

from cals.models import slugify
from cals.forms import FeatureValueForm, CategoryForm, FeatureForm, \
        NewFeatureValueFormSet, DescriptionForm, \
        CompareTwoForm, LanguageForm, EditorForm, SearchForm
from cals.statistics import generate_global_stats
from cals.tools import description_diff, compare_features
from cals.modeltools import compare_languages, \
        get_averageness_for_lang, LANGTYPES

from cals.people.views import auth_login

from cals.feature.views import (show_feature,
    make_feature_list_for_lang,
    set_language_feature_value)

from translations.models import TranslationExercise, Translation

from nano.blog.models import Entry
from nano.blog.tools import get_nano_blog_entries

from tagtools import set_tags_for_model, get_tagcloud_for_model

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
    return get_object_or_404(User, username=kwargs.get('user', None))

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

def revert_description(user, descriptions, revert_to):
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

# language

def _generate_comparison_type(comparison_type):
    same = None
    different = None
    if comparison_type == 'different':
        same = False
        different = True
    elif comparison_type == 'same':
        same = True
        different = False
    return same, different

def _generate_comparison_url(langs, comparison_type=''):
    redirect_to = '/language/%s/' % '+'.join(langs)
    if comparison_type in ('same', 'different'):
        redirect_to += comparison_type
    return redirect_to

def _compare(request, langs, comparison_type=None):
    # langs should be a non-string iterator/generator over strings
    if not len(langs):
        raise ValueError('No languages given to compare')
    langs = tuple(langs)

    # Get existing comparison-type
    comparison_type = comparison_type or request.REQUEST.get('compare', None)
    same, different = _generate_comparison_type(comparison_type)

    cform = CompareTwoForm(data=request.POST)
    if cform.is_valid():
        lang2 = cform.cleaned_data['lang2']
        redirect_to = _generate_comparison_url(langs + (lang2.slug,), comparison_type)
    else:
        redirect_to = _generate_comparison_url(langs, comparison_type)
    return HttpResponseRedirect(redirect_to)

def _check_langslugs(langslugs):
    langs = []
    for langslug in langslugs:
        try:
            lang = Language.objects.get(slug=langslug)
        except Language.DoesNotExist:
            continue
        langs.append(lang)
    return langs

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
    q = slugify(raw_q)

    if raw_q:
        if q:
            ls = Language.objects.filter(id__in=[ln.language.id for ln in LanguageName.objects.find(q, anywhere)])
        else:
            ls = Language.objects.filter(id__in=[ln.language.id for ln in LanguageName.objects.filter(slug='')])
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
            u'q': raw_q, 
            u'anywhere': anywhere,
            u'limit': limit,
            u'searchform': form,
            u'object_list': page.object_list,
            u'page_obj': page,
            u'paginator': paginator,
            u'is_paginated': True}
    return render(request, 'cals/languagenames_search.html', data)

def show_language(request, *args, **kwargs):
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
    return render(request, 'language_detail.html', data)

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
        author = request.user.get_profile().display_name
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
            lang = langform.save(commit=False)
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
                streamaction.send(request.user, verb='added the language', action_object=lang)
            else:
                streamaction.send(request.user, verb='cloned the language', action_object=cloned_from_lang, target=lang)
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
    user = request.user

    may_edit, (is_admin, is_manager) = may_edit_lang(user, lang)
    if not may_edit:
        return HttpResponseForbidden(error_forbidden)

    _LOG.info('%s about to change %s', (user, lang))

    langform = LanguageForm(instance=lang)
    #moreinfoformset = ExternalInfoFormSet(queryset=lang.externalinfo.all())
    #profile = user.get_profile()
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
                new_lang = langform.save(commit=False)
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
    #             # more info
    #             moreinfoformset = ExternalInfoFormSet(request.POST)
    #             if moreinfoformset.is_valid():
    #                 moreinfo = moreinfoformset.save()
    #                 assert False, moreinfo
    # 
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

def list_languages(request, *args, **kwargs):
    """Select and dispatch to a view of the list of languages"""

    me = 'language'

    if in_kwargs_or_get(request, kwargs, 'action', 'cloud'):
        return language_cloud(request, *args, **kwargs)
    for value in ('jrk', 'jrklist'):
        if in_kwargs_or_get(request, kwargs, 'action', value):
            return language_jrklist(request, *args, **kwargs)
    if in_kwargs_or_get(request, kwargs, 'action', 'natlang'):
        return language_list(request, natlang=True, *args, **kwargs)
    if in_kwargs_or_get(request, kwargs, 'action', 'conlang'):
        return language_list(request, *args, **kwargs)
    #if not kwargs or kwargs.get('action', None) is None:
    form = SearchForm()
    data = {'me': me, 'searchform': form }
    return render(request, 'cals/language_index.html', data)

def language_cloud(request, *args, **kwargs):
    me = 'language'
    queryset = Language.objects.conlangs().order_by('name')
    langs = []
    for lang in queryset:
        langs.append({'slug': lang.slug,
                'size': int(round(lang.get_infodensity() * 6)) + 1,
                'name': lang.name,
        })
    data = {'me': me, 'langs': langs}
    return render(request, 'cals/language_cloud.html',
            data)


class ListJRKLanguageView(ListView):
    queryset = LanguageName.objects.filter(language__natlang=False).exclude(language__background='').order_by('name')
    template_name = 'jrklist.html'

    def get_context_data(self, **kwargs):
        context = super(ListJRKLanguageView, self).get_context_data(**kwargs)
        context['me'] = 'language'
        return context
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

    data = {u'me': u'language',
            u'object_list': page.object_list,
            u'natlang': natlang,
            u'page_obj': page,
            u'paginator': paginator,
            u'is_paginated': True}

    return render(request, 'cals/language_list.html', data)

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
    return render(request, 'language_description_detail.html', data)

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
    return render(request, 'language_description_history_list.html', data)

def compare_languagefeature_history(request, *args, **kwargs):
    me = 'language'
    lang = _get_lang(*args, **kwargs)
    feature = get_object_or_404(Feature, id=kwargs.get('object_id', None))
    lf_type = ContentType.objects.get(app_label="cals", model="languagefeature")
    lf = get_object_or_404(LanguageFeature, language=lang, feature=feature)
    descriptions = Description.archive.filter(object_id=lf.id, content_type=lf_type).order_by('-last_modified')
    may_edit, (is_admin, is_manager) = may_edit_lang(request.user, lang)

    if descriptions:
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
    else:
        oldest, newest, patch = None, None, u''
    data = {'me': me,
            'oldest': oldest,
            'newest': newest,
            'patch': patch,
            'lang': lang, 
            'feature': lf,}
    return render(request, 'language_description_history_compare.html', data)

@login_required
def revert_languagefeature_description(request, lang=None, object_id=None, *args, **kwargs):
    me = 'language'
    lang = _get_lang(*args, **kwargs)
    lang = get_object_or_404(Language, slug=lang)
    feature = get_object_or_404(Feature, id=object_id)
    lf_type = ContentType.objects.get(app_label="cals", model="languagefeature")
    lf = get_object_or_404(LanguageFeature, language=lang, feature=feature)
    may_edit, (is_admin, is_manager) = may_edit_lang(request.user, lang)
    if not may_edit:
        return HttpResponseForbidden(error_forbidden)

    descriptions = Description.archive.filter(object_id=lf.id, content_type=lf_type).order_by('-last_modified')
    link_format = '/language/%s/feature/%i/' % (lang.slug, feature.id)

    revert_to = request.GET.get('id', 0)
    error = revert_description(request.user, descriptions, revert_to)
    if error:
        messages.error(request, error)
    return HttpResponseRedirect(link_format)

@login_required
def remove_languagefeature_description_version(request, lang=None, object_id=None, *args, **kwargs):
    me = 'language'
    lang = get_object_or_404(Language, slug=lang)
    feature = get_object_or_404(Feature, id=object_id)
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
    messages.info(request, 'Version as of %s is deleted')
    return HttpResponseRedirect(link_format)

@login_required
def describe_languagefeature(request, *args, **kwargs):
    me = 'language'
    lang = _get_lang(*args, **kwargs)
    may_edit, (is_admin, is_manager) = may_edit_lang(request.user, lang)
    if not may_edit:
        return HttpResponseForbidden(error_forbidden)

    feature = get_object_or_404(Feature, id=kwargs.get('object_id', None))
    lf = get_object_or_404(LanguageFeature, language=lang, feature=feature)
    value_str = '%s_%s' % (feature.id, lf.value.id)
    preview = u''
    preview_value = u''
    link = '/language/%s/feature/%i/' % (lang.slug, feature.id)
    new_xhtml = ''
    lfd = lf.description
    if lfd:
        new_xhtml = lfd.make_xhtml()

    if request.method == 'POST':
        if lf.description:
            descriptionform = DescriptionForm(data=request.POST, instance=lf.description)
        else:
            descriptionform = DescriptionForm(data=request.POST)
        valueform = FeatureValueForm(feature=feature, data=request.POST)

        if valueform.is_valid():
            new_f, new_v = map(int, valueform.cleaned_data.get('value', value_str).split('_'))
            try:
                new_fv = FeatureValue.objects.get(feature=feature, id=new_v)
            except FeatureValue.DoesNotExist:
                err = 'Attempted to get value "%s" for feature "%s" (form feature: "%s")'
                _LOG.debug(err % (new_v, feature, new_f))
                raise
            preview_value = new_fv

        new_lfd = None
        if descriptionform.is_valid():
            # Need to prevent extraenous saving here because of versioning
            new_lfd = descriptionform.save(commit=False)
            
            new_xhtml = new_lfd.make_xhtml()

        if request.POST.get('preview'):
            preview = new_xhtml
            msg = "You are previewing the description of '%s: %s' for %s" % (feature, new_fv, lang)
            messages.info(request, msg)
            if not new_lfd:
                descriptionform = DescriptionForm()
        elif request.POST.get('submit'):
            # value
            value_change = u''
            if new_v and new_f == feature.id and new_v != lf.value.id:
                lf.value = new_fv
                lf.save()
                value_change = u'Value now "%s." ' % lf.value
        
            # description
            desc_change = u''
            # Add/change desc
            if new_lfd and new_xhtml:
                if not lf.description or new_lfd.freetext != lf.description.freetext \
                        or new_xhtml != lf.description.freetext_xhtml \
                        or lfd.freetext_type != lf.description.freetext_type:
                    new_lfd.content_type = ContentType.objects.get_for_model(lf)
                    new_lfd.object_id = lf.id
                    new_lfd.save(user=request.user)
                    desc_change = u'Description changed.'
            # Delete desc
            else:
                if lfd:
                    lfd.delete()
                descriptionform = DescriptionForm()
            messages.info(request, u'%s%s' % (value_change, desc_change))
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
    return render(request, 'language_description_form.html', data)

# END LF

def show_stats(request, *args, **kwargs):
    me = 'statistics'
    data = {'me': me}

    data.update(generate_global_stats())
    return render(request, 'statistics.html', data)

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
