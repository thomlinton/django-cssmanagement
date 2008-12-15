from django.utils.translation import ugettext_lazy as _
from django.conf import settings
from django import template
from cssmanagement.util import Stylesheet

register = template.Library()
class CSSVersionNode(template.Node):
    def __init__(self, context_var=None):
        self.context_var = context_var
    def render(self, context):
        if not self.context_var:
            return Stylesheet.render()
        else:
            context[self.context_var] = Stylesheet.render(False)
            return ''

def get_stylesheets_url(parser, token):
    """
    This template tags provides two modes of operation for passing compiled stylesheet information
    in templates.

    In the simplest case::

        {% stylesheets_url %}

    will output either a series of link elements or single (packed) stylesheet referenced by a single
    element.

    ``stylesheets_url`` also takes a single optional parameter, a template variable, where the single
    path element or list of path elements mentioned above will be stored.

    For example::

        {% stylesheets_url as stylesheets %}
        {% for path in stylesheets %}
          <link rel='stylesheets' type='text/css' href='{{ path }}'>
        {% endfor %}

    """
    bits = token.split_contents()
    if len(bits) == 1:
        return CSSVersionNode()
    elif len(bits) == 3:
        return CSSVersionNode(context_var=bits[2])
    else:
        raise template.TemplateSyntaxError(_(u'%s tag takes either two arguments or none') % bits[0])

register.tag('stylesheets_url', get_stylesheets_url)
