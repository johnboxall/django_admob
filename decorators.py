try:
    from functools import update_wrapper
except ImportError:
    from django.utils.functional import update_wrapper  # Python 2.3, 2.4 fallback.

from admob.helpers import set_admob_cookie, admob_analytics

def analytics(view):
    "Alter the response of a view to include an admob cookie."
    def _dec(request, *args, **kwargs):
        am = admob_analytics(request, params=None, fail_silently=False)
        
        print "AM: %s" % am
        
        response = view(request, *args, **kwargs)
        response = set_admob_cookie(response, request)
        return response
    return _dec