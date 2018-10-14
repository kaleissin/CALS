from __future__ import absolute_import
from __future__ import unicode_literals
from django import forms

from wordlist.models import Word, Sense


class WordForm(forms.ModelForm):
    sense = forms.IntegerField(widget=forms.HiddenInput())
    pk = forms.IntegerField(required=False, widget=forms.HiddenInput())

    def __init__(self, **kwargs):
        super(WordForm, self).__init__(**kwargs)
        self.fields['word'].required = True

    class Meta:
        model = Word
        fields = ('word', 'notes', 'language')
        widgets = {
                'language': forms.HiddenInput()
        }

    def clean(self):
        cleaned_data = self.cleaned_data
        new_word = cleaned_data.get('word', '')
        notes = cleaned_data.get('notes', '')
        language = cleaned_data.get('language', None)
        sense = cleaned_data.get('sense', None)
        word_pk = cleaned_data.get('pk', None)
        if sense:
            sense = Sense.objects.get(pk=sense)
        words = Word.objects.filter(language=language, senses=sense)
        if word_pk:
            words = words.filter(pk=int(word_pk))
        if words:
            for word in words:
                if word.notes == notes:
                    raise forms.ValidationError(
                            "A word with the same sense \u201c%s\u201d "
                            "and the same notes already exists, "
                            "see: %s" % (sense.entry, word.word))
#                 if word.word == new_word:
#                     raise forms.ValidationError(
#                             u"A word with the same sense \u201c%s\u201d "
#                             u"and wordshape already exists" % sense.entry)
        return cleaned_data


class NAWordForm(forms.ModelForm):
    sense = forms.IntegerField(widget=forms.HiddenInput())
    pk = forms.IntegerField(required=False, widget=forms.HiddenInput())

    class Meta:
        model = Word
        fields = ('notes', 'language')
        widgets = {
                'language': forms.HiddenInput()
        }

    def clean(self):
        cleaned_data = self.cleaned_data
        notes = cleaned_data.get('notes', '')
        language = cleaned_data.get('language', None)
        sense = cleaned_data.get('sense', None)
        word_pk = cleaned_data.get('pk', None)
        if sense:
            sense = Sense.objects.get(pk=sense)
        words = Word.objects.filter(language=language, senses=sense)
        if word_pk:
            words = words.filter(pk=int(pk))
        if words:
            for word in words:
                if word.entry:
                    raise forms.ValidationError(
                            "A word for this sense already exists, "
                            "see: %s" % word.word)
                if word.notes == notes and word.not_applicable:
                    raise forms.ValidationError(
                            "This sense \u201c%s\u201d is already marked not "
                            "applicable" % sense.entry)
        return cleaned_data
