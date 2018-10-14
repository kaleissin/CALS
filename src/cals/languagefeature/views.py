from __future__ import absolute_import
from __future__ import unicode_literals

import logging
from six.moves import map
_LOG = logging.getLogger(__name__)
_LOG.info(__name__)

from django.contrib.contenttypes.models import ContentType
from django.contrib import messages
from django.contrib.auth.decorators import login_required
from django.http import (HttpResponseRedirect,
        HttpResponseForbidden)
from django.shortcuts import get_object_or_404, render
from django.template.loader import render_to_string
from django.db.models import Q
from django.views.generic import ListView, DeleteView, DetailView

from cals.feature.models import Feature, FeatureValue
from cals.tools.models import Description
from cals.tools.auth import may_edit_lang
from cals.tools.decorators import MayEditMixin, SuperUserMixin
from cals.language.models import Language
from cals.languagefeature.models import LanguageFeature

from cals.forms import FeatureValueForm, DescriptionForm
from cals.tools import description_diff

from cals.feature.views import set_language_feature_value

_error_forbidden_msg = "You don't have the necessary permissions to edit here."
error_forbidden = render_to_string('error.html',
        {'error_message': _error_forbidden_msg })


def _get_lang(all=False, **kwargs):
    language = kwargs.get('language', None)
    if all:
        return get_object_or_404(Language.all_langs, slug=language)
    return get_object_or_404(Language, slug=language)


def revert_description(user, descriptions, revert_to):
    if revert_to:
        try:
            description = descriptions.get(id=int(revert_to))
        except Description.DoesNotExist:
            error = 'Invalid version. This revert-attempt by %s has been logged.' % user.profile
            return error
        else:
            description.current = True
            description_last_modified_by = user
            description.save()


class LanguageFeatureMixin(object):
    model = LanguageFeature
    me = 'language'
    ct = ContentType.objects.get(app_label="cals", model="languagefeature")

    def get_object(self, queryset=None):
        self.language = _get_lang(**self.kwargs)
        self.feature = get_object_or_404(Feature, id=self.kwargs.get('feature', None))
        self.object = get_object_or_404(LanguageFeature, language=self.language, feature=self.feature)
        may_edit, (admin, manager) = may_edit_lang(self.request.user, self.language)
        self.may_edit = may_edit
        self.user_is_superuser = admin
        self.user_is_manager = manager
        return self.object

    def get_context_data(self, **kwargs):
        context = kwargs
        context['me'] = self.me
        context['description'] = self.object.description or None
        context['language'] = self.language
        context['feature'] = self.feature
        context['may_edit'] = self.may_edit
        return context

class LanguageFeatureDetailView(LanguageFeatureMixin, DetailView):
    template_name = 'languagefeature/language_description_detail.html'
show_languagefeature = LanguageFeatureDetailView.as_view()


class LanguageFeatureDeleteView(MayEditMixin, LanguageFeatureMixin, DeleteView):
    template_name = 'languagefeature/languagefeature_confirm_delete.html'

    def get_success_url(self):
        return '/language/%s/' % self.language.slug
delete_languagefeature = LanguageFeatureDeleteView.as_view()


class LanguageFeatureDescriptionMixin(LanguageFeatureMixin):

    def get_object(self, queryset=None):
        super(LanguageFeatureDescriptionMixin, self).get_object(queryset)
        self.descriptions = Description.archive.filter(object_id=self.object.id, content_type=self.ct).order_by('-last_modified')
        return self.object

    def get_context_data(self, **kwargs):
        context = super(LanguageFeatureDescriptionMixin, self).get_context_data(**kwargs)
        context['descriptions'] = self.descriptions
        return context


class LanguageFeatureDescriptionHistoryView(LanguageFeatureDescriptionMixin, DetailView):
    template_name = 'languagefeature/language_description_history_list.html'
show_languagefeature_history = LanguageFeatureDescriptionHistoryView.as_view()


class LanguageFeatureDescriptionCompareView(LanguageFeatureDescriptionMixin, DetailView):
    template_name = 'languagefeature/language_description_history_compare.html'

    def get_context_data(self, **kwargs):
        context = super(LanguageFeatureDescriptionCompareView, self).get_context_data(**kwargs)
        oldest, newest, patch = None, None, ''
        descriptions = self.descriptions
        if descriptions:
            newest = descriptions[0]
            oldest = tuple(descriptions)[-1]
            oldid = self.request.GET.get('oldid', oldest.id)
            newid = self.request.GET.get('newid', newest.id)
            if oldid:
                oldest = descriptions.get(id=int(oldid))
            if newid:
                newest = descriptions.get(id=int(newid))
            link_format = '/language/%s/feature/%i/history/compare?' % (self.language.slug, self.feature.id)
            patch = ''
            if self.request.method == 'GET':
                patch = description_diff(oldest, newest, link_format, self.may_edit, self.user_is_superuser)
        context['patch'] = patch
        context['oldest'] = oldest
        context['newest'] = newest
        return context
compare_languagefeature_history = LanguageFeatureDescriptionCompareView.as_view()


class LanguageFeatureRevertDescriptionView(MayEditMixin, LanguageFeatureDescriptionMixin, DetailView):

    def get(self, request, *args, **kwargs):
        self.object = self.get_object()
        context = self.get_context_data(object=self.object)
        link_format = '/language/%s/feature/%i/' % (self.language.slug, self.feature.id)
        revert_to = self.request.GET.get('id', 0)
        error = revert_description(self.request.user, self.descriptions, revert_to)
        if error:
            messages.error(request, error)
        return HttpResponseRedirect(link_format)
revert_languagefeature_description = LanguageFeatureRevertDescriptionView.as_view()


class LanguageFeatureDeleteDescriptionVersionView(LanguageFeatureDescriptionMixin, DetailView):

    def get(self, request, *args, **kwargs):
        self.object = self.get_object()
        context = self.get_context_data(object=self.object)

        link_format = '/language/%s/feature/%i/' % (self.language.slug, self.feature.id)
        remove = self.request.GET.get('id', 0)
        deleted_is_current = False
        try:
            description = self.descriptions.get(id=remove)
            deleted_is_current = description.current
            Description.objects.filter(id=remove).delete()
        except Description.DoesNotExist:
            return HttpResponseRedirect(link_format+'history/')
        if deleted_is_current:
            new_current_description = descriptions.latest()
            new_current_description.current = True
            new_current_description.save(batch=True)
        messages.info(request, 'Version as of %s is deleted' % description.last_modified)
        return HttpResponseRedirect(link_format)
remove_languagefeature_description_version = LanguageFeatureDeleteDescriptionVersionView.as_view()


@login_required
def describe_languagefeature(request, *args, **kwargs):
    me = 'language'
    lang = _get_lang(*args, **kwargs)
    may_edit, _ = may_edit_lang(request.user, lang)
    if not may_edit:
        return HttpResponseForbidden(error_forbidden)

    feature = get_object_or_404(Feature, id=kwargs.get('feature', None))
    lf = get_object_or_404(LanguageFeature, language=lang, feature=feature)
    value_str = '%s_%s' % (feature.id, lf.value.id)
    preview = ''
    preview_value = ''
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
            new_f, new_v = list(map(int, valueform.cleaned_data.get('value', value_str).split('_')))
            if not new_v:
                messages.error(request, "Cannot delete a feature that way")
                return HttpResponseRedirect(link + 'change')

            new_fv = FeatureValue.objects.get(feature=feature, id=new_v)
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
            value_change = ''
            if new_v and new_f == feature.id and new_v != lf.value.id:
                lf.value = new_fv
                lf.save()
                value_change = 'Value now "%s." ' % lf.value

            # description
            desc_change = ''
            # Add/change desc
            if new_lfd and new_xhtml:
                if not lf.description or new_lfd.freetext != lf.description.freetext \
                        or new_xhtml != lf.description.freetext_xhtml \
                        or lfd.freetext_type != lf.description.freetext_type:
                    new_lfd.content_type = ContentType.objects.get_for_model(lf)
                    new_lfd.object_id = lf.id
                    new_lfd.save(user=request.user)
                    desc_change = 'Description changed.'
            # Delete desc
            else:
                if lfd:
                    lfd.delete()
                descriptionform = DescriptionForm()
            messages.info(request, '%s%s' % (value_change, desc_change))
            return HttpResponseRedirect(link)
    else:
        valueform = FeatureValueForm(feature=feature, initial={'value': value_str})

        if lf.description:
            descriptionform = DescriptionForm(instance=lf.description)
        else:
            descriptionform = DescriptionForm()

    data = {'me': me,
            'form': descriptionform,
            'language': lang,
            'feature': feature,
            'object': lf,
            'valueform': valueform,
            'preview': preview,
            'preview_value': preview_value,
            'may_edit': may_edit,
            'user': request.user,
            'description': lf.description,
            }
    return render(request, 'languagefeature/language_description_form.html', data)
