from django.contrib import admin

from translation.models import Translation, TranslationExercise, TranslationExerciseCategory

class TranslationAdmin(admin.ModelAdmin):
    model = Translation
    ordering = ('exercise', 'translator', 'translation')
    list_display = ('translation', 'exercise', 'language', 'translator')
    list_filter = ('exercise',)
admin.site.register(Translation, TranslationAdmin)

class TranslationExerciseAdmin(admin.ModelAdmin):
    model = TranslationExercise
    ordering = ('category', 'name')
    list_display = ('name', 'category')
    list_filter = ('category',)
admin.site.register(TranslationExercise, TranslationExerciseAdmin)
admin.site.register(TranslationExerciseCategory)

