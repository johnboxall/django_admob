from django import template

from admob import analytics, ad


register = template.Library()

# class AdMobAdTag(template.Node):
#     """
#     Write out an AdMob ad for this `request`.
#     Use with `admob.middleware.AdMobMiddleware`.
#     Note `request` must be in the context of this template.
#     
#     """
#     def render(self, context):
#         context['request'].has_admob = True
#         return admob_ad(context['request'], params=None, fail_silently=False)
# 
# def do_admobad(parser, token):
#     return AdMobAdTag()
# register.tag('admob', do_admobad)
# 
# class AnalyticsMaybeAd(template.Node):
#     """
#     If condition then show an ad otherwise stick to analytics.
#     By default set to fail silently.
#     
#     usage:
#     {% admob_analytics_maybe_ad true_or_false_var %}
#     
#     """
#     def __init__(self, var_name):
#         self.var = template.Variable(var_name)
#         
#     def render(self, context):
#         context['request'].has_admob = True
#         # Show ad?
#         if self.var.resolve(context):
#             return ad(context['request'], fail_silently=True)
#         # Otherwise just analytics.
#         else:
#             return analytics(context['request'], fail_silently=True)
# 
# def do_analyticsmaybead(parser, token):
#     bits = token.contents.split()
#     if len(bits) != 2:
#         raise TemplateSyntaxError, "admob_if_ad tag takes exactly one argument"
#     return AnalyticsMaybeAd(bits[1])
# register.tag('abmob_analytics_maybe_ad', do_analyticsmaybead)
#     