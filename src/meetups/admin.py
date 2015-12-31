from __future__ import absolute_import
from __future__ import unicode_literals

from django.contrib import admin

from meetups.models import Meetup

class MeetupAdmin(admin.ModelAdmin):
    model = Meetup
    list_display = ('badge', 'keygroup')


admin.site.register(Meetup, MeetupAdmin)
