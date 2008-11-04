from django import forms

from translation.models import Translation

class TranslationForm(forms.ModelForm):
    class Meta:
        model = Translation
        fields = ('translation', 'interlinear', 'il_format')

    def __init__(self, *args, **kwargs):
        help_text = """The format of the interlinear is currently one of
        <a href="http://en.wikipedia.org/wiki/WYSIWYG">WYSIWYG</a>
        <tt>monospace</tt> or <a
        href="http://www.eva.mpg.de/lingua/resources/glossing-rules.php">Leipzig
        Glossing Rules</a> one-word-one-column space separated. HTML
        won't work."""
        super(TranslationForm, self).__init__(*args, **kwargs)
        self.fields[u'interlinear'].widget = forms.Textarea(attrs={'cols': 120})
        self.fields[u'interlinear'].required = False
        self.fields[u'interlinear'].help_text = help_text

