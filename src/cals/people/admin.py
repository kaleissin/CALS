from __future__ import absolute_import
from __future__ import unicode_literals
from django.contrib import admin

from cals.people.models import Profile


class ProfileAdmin(admin.ModelAdmin):
    model = Profile
    ordering = ('display_name',)
    list_display = ('display_name', 'username')
    search_fields = ('display_name', 'username')
