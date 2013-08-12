from django.contrib import admin

from wordlist.models import BuckCategory, Sense, Word
from wordlist.models import SkippedWord

class BuckCategoryAdmin(admin.ModelAdmin):
    model = BuckCategory
    #ordering = (id,)
    list_display = ('id', 'name')
admin.site.register(BuckCategory, BuckCategoryAdmin)
 
class SenseAdmin(admin.ModelAdmin):
    prepopulated_fields = {"slug": ("entry",)}
    model = Sense
    search_fields = ('entry',)
    list_filter = ('pos', 'swadesh_100', 'yakhontov', 'holman_list',
            'buck_category', 'buck', 'ids', 'wold')
#     list_display = ('entry', 'pos', 'notes', 'swadesh_100', 'yakhontov',
#             'holman_list', 'swadesh_207', 'holman_rank', 'buck_number',
#             'buck', 'ids', 'wold')
    list_display = ('id', 'entry', 'pos', 'notes',
            'uld2', 'buck_number', 'ids_number', 'wold_number')
    list_editable = ('pos', 'uld2',)
admin.site.register(Sense, SenseAdmin)

class WordAdmin(admin.ModelAdmin):
    model = Word
    ordering = ('id',)
    #search_fields = ('entry',)
    list_filter = ('not_applicable',)
    list_display = ('word', 'not_applicable', 'notes', 'language',
            'added_by')
admin.site.register(Word, WordAdmin)

class SkippedWordAdmin(admin.ModelAdmin):
    list_display = ('sense', 'language', 'added_by')
admin.site.register(SkippedWord, SkippedWordAdmin)
