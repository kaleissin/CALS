import logging
import csv
import operator

from django.http import HttpResponse
from django.views.generic import TemplateView
from django.utils.decorators import method_decorator
from django.contrib.auth.decorators import login_required
from django.db.models import Q

from cals.tools import uslugify

from wordlist import WordlistMixin
from wordlist.models import Sense

LOG = logging.getLogger(__name__)

# Wordlist views

class ListAllWordlistView(WordlistMixin, TemplateView):
    template_name = "wordlist/list_all.html"

class SpecificListView(WordlistMixin, TemplateView):
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
            'uld2',
            'id',
            )
    fields = ()
    info = ''
    more_info = ''

    def __init__(self, *args, **kwargs):
        self.csv_types = {
                'simple': self.csv_simple,
                'full': self.csv_full,
                }

        assert self.title is not None
        # Check and prep fields that should exist or be true
        self._fields={}
        self.clean_fields = []
        for k in self.fields:
            if k in self._unnumbered_fields:
                self._fields[k] = True
                self.clean_fields.append(k)
            elif k in self._numbered_fields:
                self._fields['%s__isnull' % k] = False
                self.clean_fields.append(k)
        # Check and prep fields that should be null or false
        self._exclude={}
        for k in getattr(self, 'exclude', ()):
            if k in self._unnumbered_fields:
                self._exclude[k] = False
            elif k in self._numbered_fields:
                self._exclude['%s__isnull' % k] = True
        # Check and prep ordering
        self._ordering = []
        for k in getattr(self, 'ordering', ()):
            if k in self._unnumbered_fields+self._numbered_fields:
                self._ordering.append(k)
        super(SpecificListView, self).__init__(*args, **kwargs)

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

    def csv(self, queryset, fields, filename):
        response = HttpResponse(content_type='text/csv')
        response['Content-Disposition'] = 'attachment; filename=%s' % filename
        CSV = csv.writer(response, quoting=csv.QUOTE_NONNUMERIC)
        CSV.writerow(fields)
        for row in queryset.values_list(*fields):
            CSV.writerow([unicode(value).encode('utf8') for value in row])
        return response

    def csv_simple(self, queryset):
        fields = ('id', 'entry', 'pos', 'notes') + tuple(self.clean_fields)
        return self.csv(queryset, fields, uslugify(self.title) + '-simple.csv')

    def csv_full(self, queryset):
        fields = [f.name for f in queryset[0]._meta.fields 
                if f.name not in ('added', 'suggested_by', 'uld2')]
        return self.csv(queryset, fields, uslugify(self.title) + '-full.csv')

    def render_to_response(self, context):
        csv_type = self.request.GET.get('csv', None)
        if csv_type in self.csv_types:
            return self.csv_types[csv_type](context['words'])
        return TemplateView.render_to_response(self, context)

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
