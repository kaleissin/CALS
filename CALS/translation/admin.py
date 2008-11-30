from django.contrib import admin

from translation.models import Translation, TranslationExercise, TranslationExerciseCategory

class TranslationAdmin(admin.ModelAdmin):
    model = Translation
    ordering = ('exercise', 'translator', 'translation')
    list_display = ('exercise', 'translation', 'translator')
admin.site.register(Translation, TranslationAdmin)

admin.site.register(TranslationExercise)
admin.site.register(TranslationExerciseCategory)

