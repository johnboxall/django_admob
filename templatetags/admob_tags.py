from django import template

from admob import ad, analytics


register = template.Library()

class AdMobAdTag(template.Node):
    """
    Write out an AdMob ad for this request.
    Use with admob.middleware.AdMobMiddleware.
    Note request must be in the context of the template.
    
    """
    def render(self, context):
        context['request'].has_admob = True
        return ad(context['request'], params=None, fail_silently=True)

def do_admobad(parser, token):
    return AdMobAdTag()
register.tag('admob', do_admobad)


class AnalyticsMaybeAd(template.Node):
    """
    If condition is True show an Ad otherwise just Analytics.
    
    usage:
    {% admob_analytics_maybe_ad boolean_var %}
    
    """
    def __init__(self, var_name):
        self.var = template.Variable(var_name)
        
    def render(self, context):
        context['request'].has_admob = True
        if self.var.resolve(context):
            return ad(context['request'], fail_silently=True)
        else:
            return analytics(context['request'], fail_silently=True)

def do_analyticsmaybead(parser, token):
    bits = token.contents.split()
    if len(bits) != 2:
        raise TemplateSyntaxError, "abmob_analytics_maybe_ad tag takes exactly one argument"
    return AnalyticsMaybeAd(bits[1])
register.tag('abmob_analytics_maybe_ad', do_analyticsmaybead)