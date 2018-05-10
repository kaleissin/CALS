from unittest import TestCase
from collections import OrderedDict

from cals.templatetags.cals_tags import linkify_dict


class HelperTestCase(TestCase):

    def test_linkify_dict(self):
        url = 'http://example.com'
        content = 'Example'
        result = linkify_dict(url, content)
        self.assertEqual(result, OrderedDict(url=url, content=content, extra=None))
        result = linkify_dict(url, content, classes=('button', 'jikes'))
        expected = OrderedDict( url=url, content=content, extra='classes="button jikes"')
        self.assertEqual(
            result,
            expected
        )
