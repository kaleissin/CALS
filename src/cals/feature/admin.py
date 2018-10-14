from __future__ import absolute_import
from __future__ import unicode_literals
from django.contrib import admin

from cals.feature.models import Feature, FeatureValue, Category


class FeatureValueAdmin(admin.ModelAdmin):
    model = FeatureValue 
    list_display = ('name', 'position', 'feature')


class FeatureValueInline(admin.TabularInline): 
    model = FeatureValue 
    extra = 5 


class FeatureAdmin(admin.ModelAdmin): 
    model = Feature
    inlines = [FeatureValueInline] 
    ordering = ('id',)
    list_display = ('name', 'category')
    list_filter = ('category',)


class CategoryAdmin(admin.ModelAdmin): 
    model = Category
    ordering = ('id',)
