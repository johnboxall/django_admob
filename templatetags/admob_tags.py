from django import template

from admob.helpers import admob_ad

register = template.Library()


class AdMob(template.Node):
    def render(self, context):
        context['request'].has_admob = True
        ad = admob_ad(context['request'], params=None, fail_silently=False)
        
        print "ad: %s" % ad
        
        return ad

def do_admob(parser, token):
    return AdMob()
register.tag('admob', do_admob)
