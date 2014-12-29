import logging
from django.conf import settings

def markup_as_restructuredtext(value):
    try:
        from django.utils.encoding import smart_str, force_unicode
        from docutils.parsers.rst import directives
        from docutils.core import publish_parts
        from cals import rst
    except ImportError:
        return force_unicode(value)
    else:
        directives.register_directive('interlinear', rst.InterlinearDirective)
        docutils_settings = getattr(settings, "RESTRUCTUREDTEXT_FILTER_SETTINGS", {})
        parts = publish_parts(source=smart_str(value), writer=rst.CALSHTMLWriter(), settings_overrides=docutils_settings)
        return force_unicode(parts["fragment"])

