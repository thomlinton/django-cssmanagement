from django.utils.translation import ugettext_lazy as _
from django.conf import settings
from django import template
from cssmanagement.util import Stylesheet

register = template.Library()
class CSSVersionNode(template.Node):
    def render(self, context):
        return Stylesheet.render()

def get_stylesheets_url(parser, token):
    try:
        tag_name = token.split_contents()
    except ValueError:
        raise template.TemplateSyntaxError(_(u'%s tag takes no arguments') % tag_name)
    return CSSVersionNode()

register.tag('stylesheets_url', get_stylesheets_url)
