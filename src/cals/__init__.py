from __future__ import absolute_import
from __future__ import unicode_literals

import logging
from django.conf import settings

default_app_config = 'cals.apps.CalsConfig'


def markup_as_restructuredtext(value):
    try:
        from django.utils.encoding import smart_text, force_text
        from docutils.parsers.rst import directives
        from docutils.core import publish_parts
        from cals import rst
    except ImportError:
        return force_text(value)
    else:
        directives.register_directive('interlinear', rst.InterlinearDirective)
        docutils_settings = getattr(settings, "RESTRUCTUREDTEXT_FILTER_SETTINGS", {})
        parts = publish_parts(source=smart_text(value), writer=rst.CALSHTMLWriter(), settings_overrides=docutils_settings)
        return force_text(parts["fragment"])
