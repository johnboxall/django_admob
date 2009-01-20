from django import template

from admob.helpers import admob_ad


register = template.Library()

class AdMobAdTag(template.Node):
    """
    Write out an AdMob ad for this `request`.
    Use with `admob.middleware.AdMobMiddleware`.
    Note `request` must be in the context of this template.
    
    """
    def render(self, context):
        context['request'].has_admob = True
        return admob_ad(context['request'], params=None, fail_silently=False)

def do_admobad(parser, token):
    return AdMobAdTag()
register.tag('admob_ad', do_admob)