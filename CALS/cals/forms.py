from cals import getLogger
LOG = getLogger('cals.forms')

import unicodedata

from django.contrib.auth.models import User
from django import forms
from django.db import models

from countries.models import Country

from cals.models import *

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
    #editors = ModelMultipleChoiceField(queryset=User.objects.order_by('profile_set__display_name'))

    class Meta:
        model = Language
        fields = ('editors',)

class LanguageForm(forms.ModelForm):
    background = TruncCharField(required=False, max_length=256,
            widget=forms.Textarea(attrs={'cols': '64', 'rows': '4'}),
            help_text="""Maximum <span class="count" id="background_max">256</span> characters, formatting included.""")
    #manager = forms.MultipleChoiceField(queryset=Profile.objects.filter)
    greeting = forms.CharField(max_length=64, required=False)

    class Meta:
        model = Language
        exclude = ('editors', 'greeting')

#     def save(self, commit=True, user=None):
#         if user:
#             LOG.info('CALS new language #1: %s', self.cleaned_data)
#             self.cleaned_data['added_by_id'] = user.id
#             LOG.info('CALS new language #2: %s', self.cleaned_data)
#         super(LanguageForm, self).save(commit)

class CompareTwoForm(forms.Form):
    lang2 = forms.ModelChoiceField(Language.objects.all())

class CompareTwoFeaturesForm(forms.Form):
    feature2 = forms.ModelChoiceField(Feature.objects.all())

class FeatureForm(forms.ModelForm):

    class Meta:
        model = Feature

class FeatureValueForm(forms.Form):

    def __init__(self, feature=None, *args, **kwargs):
        super(FeatureValueForm, self).__init__(*args, **kwargs)
        initial = kwargs.get('initial', None)
        if feature:
            fvs = FeatureValue.objects.filter(feature=feature).order_by('id')
            self.fields['value'].choices = [('','----------')]+[(fv.id, fv.name) for fv in fvs]
            if initial:
                self.fields['value'].initial = initial.get('value', None)

    value = forms.ChoiceField(required=False, choices=())

class DescriptionForm(forms.ModelForm):
    freetext = forms.CharField(widget=forms.Textarea(attrs={'rows': '20', 'cols':'60'}))

    class Meta:
        model = Description
        fields = ('freetext', 'freetext_link')

class FeatureDescriptionForm(forms.ModelForm):
    description = forms.CharField(widget=forms.Textarea(attrs={'rows': '20', 'cols':'60'}))

    class Meta:
        model = Feature
        fields = ('description', 'description_link')

class LanguageFeatureForm(forms.ModelForm):

    class Meta:
        model = LanguageFeature

class SignupForm(forms.Form):
    help_text = {
            'last_name': """If you set "Personal name" or """
                    """"Family name", these will """
                    """be shown instead of the username""",
            'email': """Only used to mail you your password, """
                    """should you forget it""",
    }
    username = forms.CharField(label='Username', max_length=30,
            min_length=2, 
            help_text="Will be stored as ASCII")
    password1 = forms.CharField(label='Password', max_length=30, widget=forms.PasswordInput)
    password2 = forms.CharField(label='Repeat password', max_length=30, widget=forms.PasswordInput)
    email = forms.EmailField(label='Email', required=False, help_text=help_text['email'])

    def clean_password2(self):
        password1 = self.cleaned_data.get('password1')
        password2 = self.cleaned_data.get('password2')
        if password1 and password2:
            if password1 != password2:
                raise forms.ValidationError("The two password fields didn't match.")
        return password2

class PasswordChangeForm(forms.Form):
    password1 = forms.CharField(label='New password', max_length=30, widget=forms.PasswordInput)
    password2 = forms.CharField(label='Repeat new password', max_length=30, widget=forms.PasswordInput)

    def clean_password2(self):
        password1 = self.cleaned_data.get('password1')
        password2 = self.cleaned_data.get('password2')
        if password1 and password2:
            if password1 != password2:
                raise forms.ValidationError(_("The two password fields didn't match."))
        return password2

class PasswordResetForm(forms.Form):
    username = forms.CharField(label='Username', max_length=30, min_length=2)
    secret = forms.CharField(label='Secret', max_length=64, required=False)

class UserForm(forms.ModelForm):
    username = forms.CharField(max_length=16, min_length=3)
    first_name = forms.CharField(label='Real name', max_length=30, required=False)
    email = forms.EmailField(required=False,
            help_text= """Only used to mail you your password,
                    should you forget it""",
            )

    class Meta:
        model = User
        fields = ('username', 'first_name', 'email')

class ProfileForm(forms.ModelForm):
    country = forms.ModelChoiceField(Country.objects.all(), required=False)

#     def __init__(self, *args, **kwargs):
#         super(ProfileForm, self).__init__(*args, **kwargs)
#         self.fields.keyOrder = ['username', 'first_name', 'last_name',
#                 'email', 'homepage', 'homepage_title', 'country']

    class Meta:
        model = Profile
        exclude = ('user', 'is_visible', 'date_format', 'secret',
                'altitude')

class LanguageTranslationForm(forms.Form):
    translation = forms.CharField()

