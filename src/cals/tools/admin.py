from __future__ import absolute_import
from __future__ import unicode_literals
from django.contrib import admin

from cals.tools.models import *

class DescriptionAdmin(admin.ModelAdmin): 
    model = Description
    list_display = ('object_id', 'content_type', 'current', 'last_modified', 'last_modified_by')
    list_filter = ('current', 'content_type',)
