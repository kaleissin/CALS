import logging

from django.views.generic import (TemplateView,
                                  DetailView,
                                  ListView,
                                  ModelFormMixin,
                                  ProcessFormView,
                                  SingleObjectTemplateResponseMixin,
                                  TemplateResponseMixin,
                                  View,
                                  )
from django.http import HttpResponseRedirect, HttpResponseForbidden
from django.utils.decorators import method_decorator
from django.contrib.auth.decorators import login_required
from django.db.models import Q
from django.db import transaction
from django.shortcuts import get_object_or_404
from django.core.urlresolvers import reverse as url_reverse

from wordlist.models import Sense, Word, SkippedWord
from wordlist.forms import WordForm

from cals.language.models import Language

from wordlist import WordlistMixin
from wordlist import get_field_from_kwargs
from wordlist import get_language_from_kwargs
from wordlist import may_edit

LOG = logging.getLogger(__name__)

class CreateUpdateView(SingleObjectTemplateResponseMixin, ModelFormMixin,
        ProcessFormView):
    pass

class WordlistView(WordlistMixin, TemplateView):
    template_name = "wordlist/index.html"

# Wordlist views

class ListAllWordlistView(WordlistMixin, TemplateView):
    template_name = "wordlist/list_all.html"

class SpecificListView(WordlistMixin, TemplateView):
    """Base class for all list views

    Child classes *must* set:

        * fields: which fields should be visible
        * title:  title of the resulting page

    They *may* set:

        * template_name: if different from the default
        * ordering:      which fields to sort on
        * exclude:       if one of these field is set in the row, hide it
    """
    template_name = 'wordlist/unnumbered_list.html'

    _unnumbered_fields = (
            'swadesh_100',
            'holman_list',
            'yakhontov',
            'buck',
            'ids',
            'wold')
    _numbered_fields = (
            'swadesh_207',
            'holman_rank',
            'buck_number',
            'ids_number',
            'wold_number',
            'buck_category',
            'id',
            )
    fields = ()
    info = ''
    more_info = ''

    def _set_fields(self):
        """Check and prep fields that should exist or be true"""
        self._fields = {}
        for k in self.fields:
            if k in self._unnumbered_fields:
                self._fields[k] = True
            elif k in self._numbered_fields:
                self._fields['%s__isnull' % k] = False

    def _set_exclude(self):
        """Check and prep fields that should be null or false"""
        self._exclude = {}
        for k in getattr(self, 'exclude', ()):
            if k in self._unnumbered_fields:
                self._exclude[k] = False
            elif k in self._numbered_fields:
                self._exclude['%s__isnull' % k] = True

    def _set_ordering(self):
        """Check and prep ordering"""
        self._ordering = []
        for k in getattr(self, 'ordering', ()):
            if k in self._unnumbered_fields+self._numbered_fields:
                self._ordering.append(k)

    def __init__(self, *args, **kwargs):
        super(SpecificListView, self).__init__(*args, **kwargs)
        assert self.title is not None
        assert self.fields is not None
        self._set_fields()
        self._set_exclude()
        self._set_ordering()

    def clean_queryset(self, qs):
        if self._exclude:
            qs = qs.filter(**self._exclude)
        if self._ordering:
            qs = qs.order_by(*self._ordering)
        return qs

    def generate_queryset(self):
        if self._fields:
            senses = Sense.objects.filter(**self._fields)
        else:
            senses = Sense.objects.all()
        return self.clean_queryset(senses)

    def get_context_data(self, **kwargs):
        context = super(SpecificListView, self).get_context_data(**kwargs)
        context['words'] = self.generate_queryset()
        context['title'] = self.title
        context['info'] = self.info
        context['more_info'] = self.more_info
        return context

class Swadesh100View(SpecificListView):
    title = 'The Swadesh 100 list'
    fields = ('swadesh_100',)

class HolmanListView(SpecificListView):
    title = 'The Holman list'
    fields = ('holman_list',)

class YakhontovListView(SpecificListView):
    title = 'The Yakhontov list'
    fields = ('yakhontov',)

class HolmanAndYakhontovView(SpecificListView):
    template_name = 'wordlist/holman-yakhontovlist.html'
    title = 'Words Holman and Yakhontov have in common'
    fields = ('yakhontov', 'holman_list',)

class Swadesh207View(SpecificListView):
    template_name = 'wordlist/swadesh207.html'
    title = 'The Swadesh 207 list'
    fields = ('swadesh_207',)
    ordering = ('swadesh_207',)

class SwadeshNotBuckView(SpecificListView):
    template_name = 'wordlist/swadesh-notbuck.html'
    title = 'Swadesh minus Buck'
    fields = ('swadesh_207',)
    exclude = ('buck','ids', 'wold')
    ordering = ('id',)

class Swadesh207Not100View(SpecificListView):
    title = 'Swadesh 207 minus Swadesh 100'
    fields = ('swadesh_207',)
    exclude = ('swadesh_100',)
    ordering = ('id',)

class BuckView(SpecificListView):
    template_name = 'wordlist/buck.html'
    title = 'Buck (combined)'
    fields = ('buck_category',)
    ordering = ('buck_category', 'buck_number', 'ids_number', 'wold_number')

class CommonBuckView(SpecificListView):
    template_name = 'wordlist/buck.html'
    title = 'Buck (exists in all three)'
    fields = ('buck', 'ids', 'wold',)
    ordering = ('buck_category', 'buck_number', 'ids_number', 'wold_number')

class BuckIDSView(SpecificListView):
    template_name = 'wordlist/buck.html'
    title = 'Buck (IDS)'
    fields = ('ids_number',)
    ordering = ('buck_category', 'ids_number',)

class Buck1949View(SpecificListView):
    template_name = 'wordlist/buck.html'
    title = 'Buck (1949)'
    fields = ('buck_number',)
    ordering = ('buck_category', 'buck_number',)

class BuckWOLDView(SpecificListView):
    template_name = 'wordlist/buck.html'
    title = 'Buck (WOLD)'
    fields = ('wold_number',)
    ordering = ('buck_category', 'wold_number',)

class OnlyBuck1949View(SpecificListView):
    template_name = 'wordlist/buck.html'
    title = 'Buck, unique to the 1949 book'
    fields = ('buck_number',)
    exclude = ('ids_number', 'wold_number',)
    ordering = ('buck_category', 'buck_number',)

class OnlyBuckIDSView(SpecificListView):
    template_name = 'wordlist/buck.html'
    title = 'Buck (IDS)'
    fields = ('ids_number',)
    exclude = ('buck_number', 'wold_number',)
    ordering = ('buck_category', 'ids_number',)

class OnlyBuckWOLDView(SpecificListView):
    template_name = 'wordlist/buck.html'
    title = 'Buck, unique to WOLD'
    fields = ('wold_number',)
    exclude = ('buck_number', 'ids_number',)
    ordering = ('buck_category', 'wold_number',)

class OnlyBuckIDSWOLDView(SpecificListView):
    template_name = 'wordlist/buck.html'
    title = 'The words added by IDS and WOLD'
    fields = ('ids_number', 'wold_number',)
    or_list = True
    exclude = ('buck_number',)
    ordering = ('buck_category', 'ids_number', 'wold_number',)

    def generate_queryset(self):
        senses = Sense.objects.filter(Q(ids_number__isnull=False)
                |Q(wold_number__isnull=False)).distinct()
        return self.clean_queryset(senses)

class NotOnAnyListView(SpecificListView):
    title = 'Not on any list'
    info = "The following senses are CALS originals and can not be " \
            "found in any of the other lists."
    exclude = ('buck', 'ids', 'wold', 'swadesh_207', 'swadesh_100', 'uld2')

    def generate_queryset(self):
        senses = Sense.objects.all()
        return self.clean_queryset(senses)

# Complex views

class LanguageListView(WordlistMixin, ListView):
    template_name = 'wordlist/language_list.html'
    model = Language
    context_object_name='languages'

    def get_context_data(self, **kwargs):
        context = super(LanguageListView, self).get_context_data(**kwargs)
        context['languages'] = Language.objects.filter(words__isnull=False).distinct()
        return context

class LanguageWordListView(WordlistMixin, ListView):
    template_name = 'wordlist/language_word_list.html'
    model = Word

    def get(self, request, **kwargs):
        self.language = get_language_from_kwargs(**kwargs)
        self.user = request.user
        return super(LanguageWordListView, self).get(request, **kwargs)

    def get_context_data(self, **kwargs):
        context = super(LanguageWordListView, self).get_context_data(**kwargs)
        queryset = Word.objects.filter(language=self.language)

        context['language'] = self.language
        context['words'] = queryset.filter(not_applicable=False).order_by('word', 'id')
        context['not_words'] = queryset.filter(not_applicable=True).order_by('word', 'id')
        context['skipped_words'] = SkippedWord.objects.filter(language=self.language)
        context['may_edit'] = may_edit(self.language, self.user)
        return context

class AddWordForLanguageView(WordlistMixin, TemplateResponseMixin, View):
    template_name = 'wordlist/language_add_word.html'
    model = Sense
    form_class = WordForm
    object = None

    @method_decorator(login_required)
    def dispatch(self, *args, **kwargs):
        return super(AddWordForLanguageView, self).dispatch(*args, **kwargs)

    def get(self, request, *args, **kwargs):
        self.object = None
        self.user = request.user
        context = self.get_context_data(**kwargs)
        if not may_edit(self.language, self.user):
            return HttpResponseForbidden()
        return self.render_to_response(context)

    def get_success_url(self):
        context = {
            'langslug': self.language.slug,
            'pk': self.sense.pk,
        }
        return url_reverse('show_sense_for_language', kwargs=context)

    def get_initial(self):
        initial = {
                'language': self.language,
                'sense': self.sense.pk,
        }
        if self.word_id:
            self.object = get_object_or_404(Word, pk=self.word_id, language=self.language)
            initial['pk'] = self.object.id
            initial['word'] = self.object.word
            initial['notes'] = self.object.notes
        return initial

    def get_context_data(self, **kwargs):
        context = super(AddWordForLanguageView, self).get_context_data(**kwargs)
        self.language = get_language_from_kwargs(**context['params'])
        pk = context['params'].get('pk', None) or kwargs.get('pk', None)
        self.word_id = get_field_from_kwargs(field='wordid', **context)
        self.sense = get_object_or_404(Sense, pk=pk)
        self.object = None
        form = WordForm(initial=self.get_initial())

        context['language'] = self.language
        context['form'] = form
        context['sense'] = self.sense
        context['word'] = self.object
        #assert False, context
        return context

    def get_form(self, form_class):
        """
        Returns an instance of the form to be used in this view.
        """
        return form_class(**self.get_form_kwargs())

    def get_form_kwargs(self):
        """
        Returns the keyword arguments for instanciating the form.
        """
        kwargs = {'initial': self.get_initial()}
        if self.request.method in ('POST', 'PUT'):
            kwargs.update({
                'data': self.request.POST,
                'files': self.request.FILES,
            })
        return kwargs

    def post(self, request, *args, **kwargs):
        self.context = self.get_context_data(**kwargs)
        self.user = request.user
        form = self.get_form(self.form_class)
        if form.is_valid():
            return self.form_valid(form)
        else:
            return self.form_invalid(form)

    def form_valid(self, form):
        with transaction.atomic():
            old_word = self.context.get('word', None)
            word = form.save(commit=False)
            if old_word:
                old_word.notes = word.notes
                old_word.not_applicable = False
                old_word.word = word.word
                old_word.last_modified_by = self.user
                old_word.save()
            else:
                word.language = self.language
                word.not_applicable = False
                word.added_by = self.user
                word.last_modified_by = self.user
                word.save()
                word.senses.add(self.sense)
            return HttpResponseRedirect(self.get_success_url())

    def form_invalid(self, form):
        self.context['form'] = form
        return self.render_to_response(self.get_context_data(**self.context))

class SenseDetailView(WordlistMixin, DetailView):
    template_name = 'wordlist/sense_detail.html'
    model = Sense
    object = None

    def get(self, request, *args, **kwargs):
        self.user = request.user
        return self.render_to_response(self.get_context_data(**kwargs))

    def get_context_data(self, **kwargs):
        context = super(SenseDetailView, self).get_context_data(**kwargs)
        pk = int(context['params'].get('pk', None))
        self.sense = get_object_or_404(Sense, pk=pk)
        context['sense'] = self.sense
        context['words'] = Word.objects.filter(senses=self.sense)
        return context

class LanguageSenseDetailView(WordlistMixin, DetailView):
    template_name = 'wordlist/language_sense_detail.html'
    model = Sense
    object = None

    def get(self, request, *args, **kwargs):
        self.user = request.user
        return self.render_to_response(self.get_context_data(**kwargs))

    def get_context_data(self, **kwargs):
        context = super(LanguageSenseDetailView, self).get_context_data(**kwargs)
        self.language = get_language_from_kwargs(**kwargs)
        pk = int(context['params'].get('pk', None))
        self.sense = get_object_or_404(Sense, pk=pk)
        context['language'] = self.language
        context['sense'] = self.sense
        context['words'] = Word.objects.filter(senses=self.sense, language=self.language)
        return context

