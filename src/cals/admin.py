from __future__ import absolute_import
from __future__ import unicode_literals

from django.contrib import admin

from cals.people.models import Profile
from cals.people.admin import ProfileAdmin
from cals.feature.models import Category, Feature, FeatureValue
from cals.feature.admin import CategoryAdmin, \
        FeatureAdmin, FeatureValueAdmin
from cals.tools.models import Description
from cals.tools.admin import DescriptionAdmin
from cals.language.models import Language, LanguageFamily, LanguageName
from cals.language.admin import LanguageAdmin, \
        LanguageFamilyAdmin, LanguageNameAdmin
from cals.languagefeature.models import LanguageFeature

admin.site.register(Profile, ProfileAdmin)
admin.site.register(Category, CategoryAdmin)
admin.site.register(FeatureValue, FeatureValueAdmin)
admin.site.register(Feature, FeatureAdmin)
admin.site.register(Description, DescriptionAdmin)
admin.site.register(Language, LanguageAdmin)
admin.site.register(LanguageFamily, LanguageFamilyAdmin)
admin.site.register(LanguageName, LanguageNameAdmin)

class LanguageFeatureAdmin(admin.ModelAdmin):
    model = LanguageFeature
    list_display = ('language', 'feature', 'value')
    list_filter = ('language',)
admin.site.register(LanguageFeature, LanguageFeatureAdmin)
#admin.site.register(ExternalInfo)

