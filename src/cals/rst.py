# -*- coding: utf8 -*-

from __future__ import absolute_import
from __future__ import print_function
from __future__ import unicode_literals

from docutils.parsers import rst
from docutils.parsers.rst import directives
from docutils import nodes
from docutils.writers import html4css1

from interlinears.leipzig import InterlinearText, InterlinearError


class CALSHTMLWriter(html4css1.Writer):
    def __init__(self):
        html4css1.Writer.__init__(self)
        self.translator_class = CALSHTMLTranslator


class CALSHTMLTranslator(html4css1.HTMLTranslator):

#     def should_be_compact_paragraph(self, node):
#         if (isinstance(node.parent, nodes.block_quote)):
#             return 0
#         return super(CALSHTMLTranslator, self).should_be_compact_paragraph(node)

    def visit_literal_block(self, node):
        self.body.append(self.starttag(node, 'pre', CLASS='literal-block plaintext'))

    def visit_interlinear(self, node):
        il = InterlinearText()
        text = il.do_text(node.astext())
        self.body.append(text)
        node.children = []

    def depart_interlinear(self, node):
        pass


class InterlinearDirective(rst.Directive):
    final_argument_whitespace = True
    has_content = True

    class interlinear(nodes.General, nodes.TextElement): pass

    def run(self):
        self.assert_has_content()
        text = '\n'.join(self.content)
        try:
            il = InterlinearText()
            html = il.do_text(text)
        except InterlinearError as e:
            raise self.error(e.args[0])
        text_nodes, messages = self.state.inline_text(text, self.lineno)
        node = self.interlinear(text, '', *text_nodes)
        node.line = self.content_offset + 1
        return [node] + messages

if __name__ == '__main__':
    from docutils.core import publish_parts

    from pprint import pprint

    il = InterlinearText()

    directives.register_directive('interlinear', InterlinearDirective)

    def test(text):
        parts = publish_parts(source=text, writer=CALSHTMLWriter())
        return parts['fragment']

    goodteststring = """
.. interlinear::
    x a
    z b

    y
    0
    "foo ba"
"""

    badteststring = """
.. interlinear::
    x a
    z
"""

    print(test(goodteststring))
    print(test(badteststring))

