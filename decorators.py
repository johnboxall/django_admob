try:
    from functools import update_wrapper
except ImportError:
    from django.utils.functional import update_wrapper  # Python 2.3, 2.4 fallback.

from admob.helpers import set_admob_cookie, admob_analytics


def analytics(view):
    """
    Construct an AdMob analytics request.
    Use with `admob.middleware.AdMobMiddleware`.
    
    """
    def _dec(request, *args, **kwargs):
        admob_analytics(request, params=None, fail_silently=False)
        request.has_admob = True
        return view(request, *args, **kwargs)
    return _dec
    
    
def analytics_and_cookie(view):
    """
    Construct an AdMob analytics for `request` and then an AdMob cookie
    on the `response`. Be aware that this evaluates `view` and returns a
    response object (won't play nice with other decorators!)
        
    """
    def _dec(request, *args, **kwargs):
        admob_analytics(request, params=None, fail_silently=False)
        response = view(request, *args, **kwargs)
        response = set_admob_cookie(request , response)
        return response
    return _dec