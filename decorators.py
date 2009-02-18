try:
    from functools import update_wrapper
except ImportError:
    from django.utils.functional import update_wrapper  # Python 2.3, 2.4 fallback.

from admob import analytics


def analytics(view):
    """
    Construct an AdMob analytics request.
    Requires admob.middleware.AdMobMiddleware.
    
    """
    def _dec(request, *args, **kwargs):
        analytics(request, params=None, fail_silently=False)
        request.has_admob = True
        return view(request, *args, **kwargs)
    return _dec