import logging

from django.views.generic import (TemplateView,
                                  DetailView,
                                  ListView,
                                  TemplateResponseMixin,
                                  View,
                                  )
from django.http import HttpResponseRedirect, HttpResponseForbidden
from django.utils.decorators import method_decorator
from django.contrib.auth.decorators import login_required
from django.db import transaction
from django.shortcuts import get_object_or_404, redirect
from django.core.urlresolvers import reverse as url_reverse

from wordlist.models import BuckCategory, Sense, Word, SkippedWord
from wordlist.forms import WordForm

from cals.language.models import Language

from wordlist import WordlistMixin, get_field_from_kwargs
from wordlist import get_language_from_kwargs, may_edit

LOG = logging.getLogger(__name__)

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

    def get_context_data(self, **kwargs):
        context = super(AddWordForLanguageView, self).get_context_data(**kwargs)
        self.language = get_language_from_kwargs(**context['params'])
        pk = context['params'].get('pk', None) or kwargs.get('pk', None)
        self.word_id = get_field_from_kwargs(field='wordid', **context)
        self.object = None
        if self.word_id:
            self.object = get_object_or_404(Word, pk=self.word_id, language=self.language)
        self.sense = get_object_or_404(Sense, pk=pk)
        form = WordForm(initial=self.get_initial())

        context['language'] = self.language
        context['form'] = form
        context['sense'] = self.sense
        context['word'] = self.object
        #assert False, context
        return context

    def get(self, request, *args, **kwargs):
        context = self.get_context_data(**kwargs)
        self.user = request.user
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
        if self.object:
            initial['pk'] = self.object.id
            initial['word'] = self.object.word
            initial['notes'] = self.object.notes
        return initial

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
        if 'go' in request.POST:
            self.user = request.user
            form = self.get_form(self.form_class)
            if form.is_valid():
                return self.form_valid(form)
            else:
                return self.form_invalid(form)
        return redirect('show_sense_for_language', langslug=self.language.slug,
                pk=self.sense.pk)

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

