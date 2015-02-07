from __future__ import unicode_literals

from django import forms

from translations.models import Translation

class TranslationForm(forms.ModelForm):

    class Meta:
        il_help_text = """The format of the interlinear is currently one of
        <a href="http://en.wikipedia.org/wiki/WYSIWYG">WYSIWYG</a>
        <tt>monospace</tt> or <a
        href="http://www.eva.mpg.de/lingua/resources/glossing-rules.php">Leipzig
        Glossing Rules</a> one-word-one-column space separated. HTML
        won't work."""
        model = Translation
        fields = ('translation', 'interlinear', 'il_format')
        widgets = {'interlinear': forms.Textarea(attrs={'cols': 120}),}
        help_texts = {'interlinear': il_help_text}
