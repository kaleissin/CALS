from django.contrib import admin

from cals.models import *
from cals.people.admin import ProfileAdmin
from cals.feature.admin import CategoryAdmin, \
        FeatureAdmin, FeatureValueAdmin
from cals.tools.admin import DescriptionAdmin

#from cals.sound.admin import SoundDataPointAdmin
admin.site.register(Profile, ProfileAdmin)
admin.site.register(Category, CategoryAdmin)
admin.site.register(FeatureValue, FeatureValueAdmin)
admin.site.register(Feature, FeatureAdmin)
admin.site.register(Description, DescriptionAdmin)
#admin.site.register(SoundDataPoint, SoundDataPointAdmin)

class LanguageAdmin(admin.ModelAdmin): 
    model = Language
    ordering = ('name',)
    list_display = ('name', 'added_by', 'from_earth', 'family', 'last_modified')
    list_filter = ('from_earth', 'natlang', 'added_by',)
    search_fields = ('name', 'internal_name', 'added_by__display_name',)
    #radio_fields = {'from_earth': admin.VERTICAL }
admin.site.register(Language, LanguageAdmin)

class LanguageFeatureAdmin(admin.ModelAdmin): 
    model = LanguageFeature
    list_display = ('language', 'feature', 'value')
    list_filter = ('language',)
admin.site.register(LanguageFeature, LanguageFeatureAdmin)

class LanguageFamilyAdmin(admin.ModelAdmin): 
    model = LanguageFamily
    list_display = ('name', 'part_of', 'path',)
admin.site.register(LanguageFamily, LanguageFamilyAdmin)

class LanguageNameAdmin(admin.ModelAdmin): 
    model = LanguageName
    ordering = ('language',)
    list_display = ('name', 'language', 'added')
    ordering = ('name', 'language', '-added')
admin.site.register(LanguageName, LanguageNameAdmin)

#admin.site.register(ExternalInfo)

