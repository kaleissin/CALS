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
        msg = u'%i language%s hidden' % (qs, u'' if qs == 1 else u's')
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
