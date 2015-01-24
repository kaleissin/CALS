#!/usr/bin/env python
import os
import sys

sys.path.append('./src')

if __name__ == "__main__":
    os.environ.setdefault("DJANGO_SETTINGS_MODULE", "CALS.settings.production")

    from django.core.management import execute_from_command_line

    execute_from_command_line(sys.argv)
