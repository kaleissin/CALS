from __future__ import absolute_import
from __future__ import unicode_literals

from django.contrib import admin

from translations.models import Translation, TranslationExercise, TranslationExerciseCategory


class TranslationAdmin(admin.ModelAdmin):
    model = Translation
    ordering = ('exercise', 'translator', 'translation')
    list_display = ('translation', 'exercise', 'language', 'translator')
    list_filter = ('exercise',)
    search_fields = [
        'translator__username',
        'language__name',
        'exercise__slug',
    ]
admin.site.register(Translation, TranslationAdmin)


class TranslationExerciseAdmin(admin.ModelAdmin):
    model = TranslationExercise
    ordering = ('category', 'name')
    list_display = ('name', 'category', 'added_by', 'added')
    list_filter = ('category',)
admin.site.register(TranslationExercise, TranslationExerciseAdmin)
admin.site.register(TranslationExerciseCategory)
