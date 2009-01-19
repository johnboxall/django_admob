from admob.helpers import set_admob_cookie


class AdMobMiddleware(object):
    def process_response(self, request, response):
        "If it looks like an AdMob cookie should be set then go ahead."        
        if getattr(request, 'has_admob', False):
            print 'Request has AdMob!'
            response = set_admob_cookie(request, response)
        return response
