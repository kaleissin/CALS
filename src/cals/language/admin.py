from __future__ import absolute_import
from __future__ import unicode_literals
from django.contrib import admin

from cals.language.models import *


class LanguageAdmin(admin.ModelAdmin): 
    model = Language
    ordering = ('name',)
    list_display = ('name', 'added_by', 'from_earth', 'family', 'last_modified')
    list_filter = ('from_earth', 'natlang', 'added_by',)
    search_fields = ('name', 'internal_name')
    actions = ['make_invisible']

    #radio_fields = {'from_earth': admin.VERTICAL }

    def make_invisible(self, request, queryset):
        qs = queryset.update(visible=False)
        msg = '%i language%s hidden' % (qs, '' if qs == 1 else 's')
        self.message_user(request, msg)
        language_hidden.send(sender=self, languages=queryset)
    make_invisible.short_description = "Hide languages"


class LanguageFamilyAdmin(admin.ModelAdmin):
    model = LanguageFamily
    list_display = ('name', 'part_of', 'path',)


class LanguageNameAdmin(admin.ModelAdmin):
    model = LanguageName
    ordering = ('language',)
    list_display = ('name', 'language', 'added')
    ordering = ('name', 'language', '-added')
    search_fields = ['name']
    list_filter = ('internal', 'alternate', 'previous',)


class WALSCodeAdmin(admin.ModelAdmin):
    model = WALSCode
    ordering = ('walscode',)
    list_display = ('walscode', 'language')
    search_fields = ['walscode', 'language__name']


class GlottocodeAdmin(admin.ModelAdmin):
    model = Glottocode
    ordering = ('glottocode',)
    list_display = ('glottocode', 'language')
    search_fields = ['glottocode', 'language__name']


class ISO639_3Admin(admin.ModelAdmin):
    model = ISO639_3
    ordering = ('iso639_3',)
    list_display = ('iso639_3', 'language')
    search_fields = ['iso639_3', 'language__name']
