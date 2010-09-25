from django.contrib import admin

from cals.people.models import Profile

class ProfileAdmin(admin.ModelAdmin): 
    model = Profile
    ordering = ('display_name',)
    list_display = ('display_name', 'username')
