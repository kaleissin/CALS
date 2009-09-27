from docutils.parsers import rst
from docutils.parsers.rst import directives
from docutils import nodes
from docutils.writers import html4css1

from leipzig import InterlinearText

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
        self.body.append(self.starttag(node, 'div'))
        il = InterlinearText()
        text = il.do_text(node.astext())
        self.body.append(text)
        node.children = []

    def depart_interlinear(self, node):
        self.body.append('</div>') #self.endtag(node, 'div'))
        self.body.append('<p></p>\n')
        pass

class InterlinearDirective(rst.Directive):
    final_argument_whitespace = True
    has_content = True

    class interlinear(nodes.General, nodes.TextElement): pass

    def run(self):
        self.assert_has_content()
        #il = InterlinearText()
        #il.add_lines(self.content)
        text = '\n'.join(self.content)
        text_nodes, messages = self.state.inline_text(text, self.lineno)
        node = self.interlinear(text, '', *text_nodes)
        node.line = self.content_offset + 1
        return [node] + messages

# template tag
# def restructuredtext(value):
#    directives.register_directive('interlinear', InterlinearDirective)
#     try:
#         from docutils.core import publish_parts
#     except ImportError:
#         if settings.DEBUG:
#             raise template.TemplateSyntaxError, "Error in {% restructuredtext %} filter: The Python docutils library isn't installed."
#         return force_unicode(value)
#     else:
#         docutils_settings = getattr(settings, "RESTRUCTUREDTEXT_FILTER_SETTINGS", {})
#         parts = publish_parts(source=smart_str(value), writer_name="html4css1", settings_overrides=docutils_settings)
#         return mark_safe(force_unicode(parts["fragment"]))
# restructuredtext.is_safe = True

        

if __name__ == '__main__':
    from docutils.core import publish_parts

    from pprint import pprint

    teststring = """
.. interlinear::
    x
    z

    y
    0

"""
    directives.register_directive('interlinear', InterlinearDirective)

    parts = publish_parts(source=teststring, writer=CALSHTMLWriter())

    print parts['fragment']
