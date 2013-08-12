# Create your views here.
import sys
sys.stderr = sys.stdout

import logging
_LOG = logging.getLogger(__name__)
_LOG.info(__name__)

from django.contrib.contenttypes.models import ContentType
from django.contrib import messages #.authenticate, auth.login
from django.contrib.auth.decorators import login_required
from django.http import HttpResponseRedirect, HttpResponseNotFound, HttpResponseForbidden
from django.shortcuts import get_object_or_404
from django.views.generic.list_detail import object_list

from cals.feature.models import Feature, FeatureValue, Category
from cals.tools.models import Description
from cals.language.models import Language
from cals.models import LanguageFeature

from cals.forms import FeatureValueForm, CategoryForm, FeatureForm, \
        NewFeatureValueFormSet, CompareTwoFeaturesForm, DescriptionForm, \
        CompareTwoForm
from cals.tools import description_diff, compare_features
from cals.modeltools import get_averageness_for_lang, LANGTYPES

from nano.tools import render_page

def _get_feature(*args, **kwargs):
    return get_object_or_404(Feature, id=kwargs.get('object_id', None))

def _get_featurevalue(*args, **kwargs):
    return get_object_or_404(FeatureValue, id=kwargs.get('object_id', None))


def _get_url_pieces(name='slug', **kwargs):
    _LOG.debug('Url-pieces: %s', kwargs)
    if name in kwargs:
        # split on +, remove empty pieces
        pieces = filter(None, kwargs[name].split('+'))
        if pieces:
            return pieces
    # '%s not in kwargs: %s' % (name, pformat(kwargs))
    return None

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

def fvlist_to_fvdict(fvlist):
    if fvlist:
        return dict([(fv.feature, fv) for fv in fvlist])
    return {}

def make_feature_list_for_lang(lang=None, fvlist=None):
    categories = Category.objects.all().select_related().order_by('id')
    cats = []
    fvdict = fvlist_to_fvdict(fvlist)
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

            if lang or fvdict:
                value = None
                if fvdict:
                    value = fvdict.get(feature, None)
                else:
                    try:
                        lf = LanguageFeature.objects.get(language=lang, feature=feature)
                        value = lf.value
                    except LanguageFeature.DoesNotExist:
                        pass
                if value:
                    form = FeatureValueForm(feature=feature,
                    initial={'value': '%s_%s' % (feature.id, value.id)})
            
            f.append({'feature': feature, 'form':form, 'value': lf})
        if f:
            cats.append({'name': category.name, 'features': f})
        else:
            cats.append({'name': category.name})
    return cats

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

@login_required
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
    return object_list(request, queryset=queryset, template_name=template,
            extra_context=extra_context)

def show_feature(request, features=None, object_id=None, template_name='feature_detail.html', *args, **kwargs):
    me = 'feature'
    if not features:
        features = Feature.objects.active()
    try:
        feature = features.get(id=object_id)
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
    return render_page(request, template_name, data)

@login_required
def change_feature_description(request, *args, **kwargs):
    me = 'feature'
    feature = get_object_or_404(Feature, id=kwargs.get('object_id', None))
    preview = u''
    link = '/feature/%i/' % feature.id
    if not request.user.is_staff:
        error = "You do not have permission to change this feature's description"
        messages.error(request, error)
        return HttpResponseRedirect(link)
    if request.method == 'POST':
        if feature.description:
            form = DescriptionForm(data=request.POST, instance=feature.description)
        else:
            form = DescriptionForm(data=request.POST)
        if form.is_valid():
            featured = form.save(commit=False)
            featured.freetext_type = 'rst'
            if request.POST.get('preview'):
                preview = featured.make_xhtml()
                msg = "You are previewing the description of this feature"
                messages.info(request, msg)
            elif request.POST.get('submit'):
                featured.content_type = ContentType.objects.get_for_model(feature)
                featured.object_id = feature.id
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
def revert_feature_description(request, object_id=None, *args, **kwargs):
    me = 'feature'
    feature = get_object_or_404(Feature, id=object_id)
    feature_type = ContentType.objects.get(app_label="cals", model="feature")
    # Needs to check ownership of description

    descriptions = Description.archive.filter(object_id=feature.id, content_type=feature_type).order_by('-last_modified')
    link_format = '/feature/%i/history/compare?' % feature.id

    revert_to = request.GET.get('id', 0)
    error = revert_description(request.user, descriptions, revert_to)
    if error:
        messages.error(request, error)
    return HttpResponseRedirect(link_format)

# Feature Values

def show_featurevalue(request, *args, **kwargs):
    # XXX
    me = 'feature'
    template = 'cals/featurevalue_detail.html'
    featurevalue = _get_featurevalue(*args, **kwargs)
    data = {}
    data['object'] = featurevalue
    data['conlangs'] = featurevalue.languagefeature_set.for_conlangs()
    #filter(language__natlang=False)
    data['natlangs'] = featurevalue.languagefeature_set.for_natlangs()
    #filter(language__natlang=True)

    return render_page(request, template, data)

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
    assert len(langs)
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

def denormalize_lang(lang):
    freq = get_averageness_for_lang(lang, scale=100, langtype=LANGTYPES.CONLANG)
    _LOG.info('Freq now: %s' % repr(freq))
    lang.num_features = LanguageFeature.objects.filter(language=lang).count()
    lang.num_avg_features = freq
    lang.set_average_score()
    return lang

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

