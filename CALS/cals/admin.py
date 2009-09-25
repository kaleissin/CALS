from django.contrib import admin

from cals.models import *

class LanguageAdmin(admin.ModelAdmin): 
    model = Language
    ordering = ('name',)
    list_display = ('name', 'added_by', 'from_earth', 'last_modified')
    list_filter = ('from_earth', 'added_by',)
    search_fields = ('name', 'internal_name', 'added_by__display_name',)
    #radio_fields = {'from_earth': admin.VERTICAL }
admin.site.register(Language, LanguageAdmin)

class FeatureValueAdmin(admin.ModelAdmin):
    model = FeatureValue 
    list_display = ('name', 'position', 'feature')
admin.site.register(FeatureValue, FeatureValueAdmin)

class FeatureValueInline(admin.TabularInline): 
    model = FeatureValue 
    extra = 5 

class FeatureAdmin(admin.ModelAdmin): 
    model = Feature
    inlines = [FeatureValueInline] 
    ordering = ('id',)
    list_display = ('name', 'category')
    list_filter = ('category',)
admin.site.register(Feature, FeatureAdmin)

class LanguageFeatureAdmin(admin.ModelAdmin): 
    model = LanguageFeature
    inlines = [FeatureValueInline] 
    list_display = ('language', 'feature', 'value')
    list_filter = ('language',)
admin.site.register(LanguageFeature, LanguageFeatureAdmin)

class CategoryAdmin(admin.ModelAdmin): 
    model = Category
    ordering = ('id',)
admin.site.register(Category, CategoryAdmin)
 
class ProfileAdmin(admin.ModelAdmin): 
    model = Profile
    ordering = ('display_name',)
    list_display = ('display_name', 'username')
admin.site.register(Profile, ProfileAdmin)

class DescriptionAdmin(admin.ModelAdmin): 
    model = Description
    #ordering = ('display_name',)
    list_display = ('object_id', 'content_type')
    list_filter = ('content_type',)
admin.site.register(Description, DescriptionAdmin)

#admin.site.register(ExternalInfo)
