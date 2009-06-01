from admob import set_cookie


class AdMobMiddleware(object):
    def process_response(self, request, response):
        """Sets an AdMob cookie if required."""
        if getattr(request, 'has_admob', False):
            response = set_cookie(request, response)
        return response