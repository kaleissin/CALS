from __future__ import absolute_import
from __future__ import unicode_literals

import logging
_LOG = logging.getLogger(__name__)

import unicodedata

from django.contrib.auth import get_user_model
from django import forms
from django.forms.formsets import formset_factory
from django.forms.models import modelformset_factory, BaseModelFormSet

from django.db import models

from nano.countries.models import Country

from cals.feature.models import Feature, FeatureValue, Category
from cals.people.models import Profile
from cals.tools.models import Description
from cals.language.models import Language
from cals.languagefeature.models import LanguageFeature
from cals.language.models import ExternalInfo


def asciify(string):
    return unicodedata.normalize(string, 'NFKD').encode('ascii', 'ignore')


class TruncCharField(forms.CharField):
    """A CharField that truncates input longer than max_length."""

    def __init__(self, max_length=None, *args, **kwargs):
        """ TruncCharField must have a max_length."""
        assert max_length
        super(TruncCharField, self).__init__(max_length=max_length, *args, **kwargs)

    def clean(self, value):
        if value and len(value) > self.max_length:
            value = value[:self.max_length]
        return super(TruncCharField, self).clean(value)


class EditorForm(forms.ModelForm):
    editors = forms.ModelMultipleChoiceField(
            queryset=Profile.objects.filter(is_visible=True),
            required=False)

    class Meta:
        model = Language
        fields = ('editors',)

    def clean_editors(self):
        editors = self.cleaned_data['editors']
        self.cleaned_data['editors'] = get_user_model().objects.filter(id__in=[e.user_id for e in editors])
        return self.cleaned_data['editors']

    def save(self, commit=True, user=None):
        return super(EditorForm, self).save(commit)


class SearchForm(forms.Form):
    """Generalized search-form"""
    LIMITS = (
        ('10', '10'),
        ('20', '20'),
        ('50', '50'),
        ('100', '100'),
    )

    q = forms.CharField(max_length=64)
    anywhere = forms.BooleanField(required=False, initial=False)
    limit = forms.TypedChoiceField(choices=LIMITS, coerce=int, required=False, initial='10')


class LanguageForm(forms.ModelForm):
    background = TruncCharField(required=False, max_length=256,
            widget=forms.Textarea(attrs={'cols': '64', 'rows': '4'}),
            help_text="""Maximum <span class="count" id="background_max">256</span> characters, formatting included.""")
    # Because auth.User isn't sorted
    manager = forms.ModelChoiceField(queryset=Profile.objects.filter(is_visible=True), required=False)

    class Meta:
        model = Language
        exclude = ('created', 'editors', 'last_modified_by', 'visible', 'natlang')

    def clean_manager(self):
        manager = self.cleaned_data.get('manager', None)
        try:
            manager = manager.user
        except AttributeError:
            pass
        return manager

    def save(self, commit=True, user=None):
        new_manager = self.cleaned_data.get('manager', None)
        if new_manager:
            manager = get_user_model().objects.get(id=new_manager.pk)
            self.cleaned_data['manager'] = manager
#         if user:
#             _LOG.info('CALS new language #1: %s', self.cleaned_data)
#             self.cleaned_data['added_by_id'] = user.id
#             _LOG.info('CALS new language #2: %s', self.cleaned_data)
        return super(LanguageForm, self).save(commit)


class CompareTwoForm(forms.Form):
    lang2 = forms.ModelChoiceField(Language.objects.all())


class CompareTwoFeaturesForm(forms.Form):
    feature2 = forms.ModelChoiceField(Feature.objects.active().all())


class FeatureForm(forms.ModelForm):

    class Meta:
        model = Feature
        fields = '__all__'


class FeatureValueForm(forms.Form):
    value = forms.ChoiceField(required=False, choices=())

    def __init__(self, feature=None, *args, **kwargs):
        super(FeatureValueForm, self).__init__(*args, **kwargs)
        initial = kwargs.get('initial', None)
        if feature:
            fvs = FeatureValue.objects.filter(feature=feature).order_by('id')
            self.fields['value'].choices = [('%s_0' %
            feature.id,'----------')]+[('%s_%s' % (feature.id, fv.id), fv.name) for fv in fvs]
            if initial:
                self.fields['value'].initial = initial.get('value', None)


class DescriptionForm(forms.ModelForm):
    freetext = forms.CharField(widget=forms.Textarea(attrs={'rows': '20', 'cols':'66'}))

    class Meta:
        model = Description
        fields = ('freetext', 'freetext_link', 'freetext_type')


class FeatureDescriptionForm(forms.ModelForm):
    description = forms.CharField(widget=forms.Textarea(attrs={'rows': '20', 'cols':'60'}))

    class Meta:
        model = Feature
        fields = ('description',)


class LanguageFeatureForm(forms.ModelForm):

    class Meta:
        model = LanguageFeature
        fields = '__all__'


class UserForm(forms.ModelForm):
    username = forms.CharField(max_length=16, min_length=3)
    first_name = forms.CharField(label='Real name', max_length=30, required=False)
    email = forms.EmailField(required=True,
            help_text= """Used to mail you your password,
                    should you forget it""",
            )

    class Meta:
        model = get_user_model()
        fields = ('username', 'first_name', 'email')


class ProfileForm(forms.ModelForm):
    country = forms.ModelChoiceField(Country.objects.all(), required=False)

    def __init__(self, *args, **kwargs):
        super(ProfileForm, self).__init__(*args, **kwargs)
        self.fields['native_tongue'].queryset = Language.natlangs.all()
#         self.fields.keyOrder = ['username', 'first_name', 'last_name',
#                 'email', 'homepage', 'homepage_title', 'country']


    class Meta:
        model = Profile
        exclude = ('user', 'is_visible', 'date_format', 'secret',
                'altitude', 'show_username', 'seen_ipv6')


class CategoryForm(forms.ModelForm):

    class Meta:
        model = Category
        fields = '__all__'


class FeatureForm(forms.ModelForm):

    class Meta:
        model = Feature
        exclude = ('added_by',)


class NewFeatureValueForm(forms.Form):
    name = forms.CharField(max_length=60)

NewFeatureValueFormSet = formset_factory(NewFeatureValueForm, extra=10, max_num=10, can_order=True)
ChangeFeatureValueFormSet = formset_factory(NewFeatureValueForm, extra=10, max_num=10, can_order=True, can_delete=True)

