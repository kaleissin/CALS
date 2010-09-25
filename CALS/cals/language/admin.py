from django.contrib import admin

from cals.language.models import *

class LanguageAdmin(admin.ModelAdmin): 
    model = Language
    ordering = ('name',)
    list_display = ('name', 'added_by', 'from_earth', 'family', 'last_modified')
    list_filter = ('from_earth', 'natlang', 'added_by',)
    search_fields = ('name', 'internal_name', 'added_by__display_name',)
    #radio_fields = {'from_earth': admin.VERTICAL }

class LanguageFamilyAdmin(admin.ModelAdmin): 
    model = LanguageFamily
    list_display = ('name', 'part_of', 'path',)

class LanguageNameAdmin(admin.ModelAdmin): 
    model = LanguageName
    ordering = ('language',)
    list_display = ('name', 'language', 'added')
    ordering = ('name', 'language', '-added')
