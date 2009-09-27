import logging
from CALS import settings

LOG_FORMAT = '%(asctime)s %(name)s %(module)s:%(lineno)d %(levelname)s %(message)s'
LOG_FILE = '/tmp/cals.log'

def getLogger(name):
    log_formatter = logging.Formatter(LOG_FORMAT)
    log_handler = logging.FileHandler(LOG_FILE, 'a+')
    log_handler.setFormatter(log_formatter)
    logger = logging.getLogger(name)
    logger.addHandler(log_handler)
    return logger

def markup_as_restructuredtext(value):
    try:
        from django.utils.encoding import smart_str, force_unicode
        from docutils.parsers.rst import directives
        from docutils.core import publish_parts
    except ImportError:
        return force_unicode(value)
    else:
        from cals import rst
        directives.register_directive('interlinear', rst.InterlinearDirective)
        docutils_settings = getattr(settings, "RESTRUCTUREDTEXT_FILTER_SETTINGS", {})
        parts = publish_parts(source=smart_str(value), writer=rst.CALSHTMLWriter(), settings_overrides=docutils_settings)
        return force_unicode(parts["fragment"])

