import time
import socket
import random
import urllib2
from string import split as L

from django.conf import settings
from django.utils.http import cookie_date, urlencode
from django.utils.hashcompat import md5_constructor


# Set these badboys in your settings file.
PUBLISHER_ID = getattr(settings, 'ADMOB_PUBLISHER_ID')
ANALYTICS_ID = getattr(settings, 'ADMOB_ANALYTICS_ID')
COOKIE_PATH = getattr(settings, 'ADMOB_COOKIE_PATH', '/')
COOKIE_DOMAIN = getattr(settings, 'ADMOB_COOKIE_DOMAIN', settings.SESSION_COOKIE_DOMAIN)
ENCODING = getattr(settings, 'ADMOB_ENCODING', settings.DEFAULT_CHARSET)
TEST = getattr(settings, 'ADMOB_TEST', True)

ENDPOINT = "http://r.admob.com/ad_source.php"
TIMEOUT = 1  # Timeout in seconds.
PUBCODE_VERSION = "20090601-DJANGO"
IGNORE = L("HTTP_PRAGMA HTTP_CACHE_CONTROL HTTP_CONNECTION HTTP_USER_AGENT HTTP_COOKIE")


class AdMobError(Exception):
    "Base class for AdMob exceptions."

class AdMob(object):
    """
    Handles requests for ads/analytics from AdMob.
    """
    def __init__(self, request, params=None, fail_silently=False):
        """
        * request - HttpRequest object
        * params - dict of parameters to pass to AdMob
        * fail_silently - set to True to raise HTTP exceptions    
        """
        self.request = request
        self.request.has_admob = True
        self.params = params or {}
        self.fail_silently = fail_silently
        self.session_id = getattr(request.session, 'session_key', None)

    def fetch(self):
        """Make an AdMob request!"""
        self.build_post_data()
        return self._fetch()

    def build_post_data(self):
        """Builds the post data from params and default settings."""
        # Determine the type of request
        self.ad_request = self.params.get("ad_request", False)
        self.analytics_request = self.params.get("analytics_request", False)
        self.request_type = {
            (False, False): None,
            (True, False): 0,
            (False, True): 1,
            (True, True): 2    
        }[(self.ad_request, self.analytics_request)]

        # AdMob session_id - An MD5 hash of the Django session.
        if self.session_id is not None:
            self.admob_session_id = md5_constructor(self.session_id).hexdigest()
        else:
            self.admob_session_id = None

        # AdMob cookie - If it hasn't been set yet then set it.
        if 'admobuu' in self.request.COOKIES:
            self.admobuu = self.request.COOKIES['admobuu']
        else:
            if not hasattr(self.request, 'admobuu'):
                self.admobuu = self.request.admobuu = cookie_value(self.request)
            else:
                self.admobuu = self.request.admobuu            

        # Shared parameters.
        self.post_data = {
            'rt': self.request_type,  # admob request type
            'u': self.request.META.get('HTTP_USER_AGENT'),  # user agent
            'i': self.request.META.get('REMOTE_ADDR'),  # ip address
            't': self.admob_session_id,  # AdMob session id
            'o': self.admobuu,  # AdMob cookie value
            'p': self.params.get('page', self.request.build_absolute_uri()),  # page for your reference
            'v': PUBCODE_VERSION,  # code version
            'z': round(time.time(), 2),  # current timestamp
        }

        # Header.
        for header, value in self.request.META.iteritems():
            if header.startswith("HTTP") and header not in IGNORE:
                self.post_data["h[%s]" % header] = value

        # Test.
        self.test = self.params.get('test', TEST)
        if self.test:
            self.post_data['m'] = 'test'

        # Analytics specific parameters.
        if self.analytics_request:
            self.post_data.update({
                'a': self.params.get('analytics_id', ANALYTICS_ID),
                'title': self.params.get('title'),  # page title for your reference
                'event': self.params.get('event')  # event for your reference
            })
        
        # Ad specific parameters.
        if self.ad_request:
            self.post_data.update({
                's': self.params.get('publisher_id', PUBLISHER_ID),  # admob publisher id
                'ma': self.params.get('markup'),  # xhtml / wml
                'f': self.params.get('format'),  # html / html_no_js
                'd[pc]': self.params.get('postal_code'),
                'd[ac]': self.params.get('area_code'),
                'd[coord]': self.params.get('coordinates'),  # lat,lng
                'd[dob]': self.params.get('dob'), # date of birth
                'd[gender]': self.params.get('gender'),
                'k': self.params.get('keywords'),  # space seperated keywords
                'search': self.params.get('search')  # visitor search term
            })

            # Text only.
            if 'text_only' in self.params:
                self.post_data['y'] = 'text'

            # Output encoding.
            self.encoding = self.params.get('encoding', ENCODING)
            if self.encoding:
                self.post_data['e'] = self.encoding

        # Don't send anything that is None.
        self.post_data = dict((k, v) for k, v in self.post_data.iteritems() if v is not None)

    def _fetch(self):
        """Fetch the AdMob resource using urllib2.urlopen."""
        # Python2.5 comptabile.
        original_timeout = socket.getdefaulttimeout()
        socket.setdefaulttimeout(TIMEOUT)
        try:
            self.response = urllib2.urlopen(ENDPOINT, urlencode(self.post_data))
            if self.test:
                print 'ADMOB: Making Request...'
                import pprint
                pprint.pprint(self.post_data)
        except urllib2.URLError, e:
            if self.fail_silently:
                return ''
            else:
                raise
        else:
            return self.response.read()        
        finally:
            socket.setdefaulttimeout(original_timeout)


def cookie_value(request):
    """Construct a unique AdMob cookie value from User-Agent and IP."""
    s = "%f%s%s%f" % (
        random.random(),
        request.META.get('HTTP_USER_AGENT', ''),
        request.META.get('REMOTE_ADDR', ''),
        time.time())
    return md5_constructor(s).hexdigest()

def set_cookie(request, response, domain=COOKIE_DOMAIN, path=COOKIE_PATH):
    """Given request set and AdMob cookie on response.    """
    # Don't make a new cookie if one exists.
    if 'admobuu' in request.COOKIES or 'admobuu' in response.cookies:
        return response
    
    value = getattr(request, 'admobuu', cookie_value(request))
    expires = cookie_date(0x7fffffff)  # End of 32 bit time.
    response.set_cookie('admobuu', value, expires=expires, path=path, domain=domain)
    return response
            
def analytics(request, params=None, fail_silently=False):
    params = params or {}
    params.update({"analytics_request": True, "ad_request": False})
    admob = AdMob(request, params, fail_silently)
    admob.fetch()
    
def ad(request, params=None, fail_silently=False):
    params = params or {}
    params.update({"analytics_request": False, "ad_request": True})
    admob = AdMob(request, params, fail_silently)
    return admob.fetch()