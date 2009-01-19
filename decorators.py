try:
    from functools import update_wrapper
except ImportError:
    from django.utils.functional import update_wrapper  # Python 2.3, 2.4 fallback.

from admob.helpers import set_admob_cookie, admob_analytics


def analytics(view):
    """
    Construct an AdMob analytics request and set the AdMob cookie on the response.
    
    """
    def _dec(request, *args, **kwargs):
        admob_analytics(request, params=None, fail_silently=False)
        response = view(request, *args, **kwargs)
        response = set_admob_cookie(request , response)
        return response
    return _dec