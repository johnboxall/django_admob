from admob.helpers import set_admob_cookie


class AdMobMiddleware(object):
    def process_response(self, request, response):
        "If AdMob ads/analytics have been set then set an AdMob cookie on the response."
        if getattr(request, 'has_admob', False):
            response = set_admob_cookie(request, response)
        return response
