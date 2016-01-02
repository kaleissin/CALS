#!/usr/bin/env python

from __future__ import absolute_import
from __future__ import unicode_literals

import os
import sys

sys.path.append('./src')

if __name__ == "__main__":
    os.environ.setdefault("DJANGO_SETTINGS_MODULE", "CALS.settings.local")

    from django.core.management import execute_from_command_line

    execute_from_command_line(sys.argv)
