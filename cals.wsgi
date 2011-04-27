import site
import os, sys

SITE_ROOT = os.path.dirname(os.path.realpath(__file__))
PROJECT='CALS'

site.addsitedir(SITE_ROOT + '/lib/python2.6/site-packages')
sys.path.append(SITE_ROOT+'/%s/env' % PROJECT)
sys.path.append(SITE_ROOT+'/%s' % PROJECT)
sys.path.append(SITE_ROOT)

os.environ['DJANGO_SETTINGS_MODULE'] = '%s.settings' % PROJECT

sys.stdout = sys.stderr

import django.core.handlers.wsgi
application = django.core.handlers.wsgi.WSGIHandler()
