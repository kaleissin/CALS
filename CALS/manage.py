#!/usr/bin/env python
import os
import sys
print sys.path
#SITE_ROOT = os.path.dirname(os.path.realpath(__file__))
#sys.path.insert(0, os.path.join(SITE_ROOT, 'env'))

if __name__ == "__main__":
    os.environ.setdefault("DJANGO_SETTINGS_MODULE", "CALS.settings")

    from django.core.management import execute_from_command_line

    execute_from_command_line(sys.argv)
