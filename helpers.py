import time
import socket
import random
import urllib
import urllib2

from django.conf import settings
from django.utils.http import cookie_date
from django.utils.hashcompat import md5_constructor


# Set these badboys in your settings file.
PUBLISHER_ID = getattr(settings, 'ADMOB_PUBLISHER_ID')
ANALYTICS_ID = getattr(settings, 'ADMOB_ANALYTICS_ID')
COOKIE_PATH = getattr(settings, 'ADMOB_COOKIE_PATH', '/')
COOKIE_DOMAIN = getattr(settings, 'ADMOB_COOKIE_DOMAIN', settings.SESSION_COOKIE_DOMAIN)
ENCODING = getattr(settings, 'ADMOB_ENCODING', 'utf-8')
TEST = getattr(settings, 'ADMOB_TEST', True)

ENDPOINT = "http://r.admob.com/ad_source.php"
TIMEOUT = 1  # Timeout in seconds.
PUBCODE_VERSION = "20090116-DJANGO"
IGNORE = "HTTP_PRAGMA HTTP_CACHE_CONTROL HTTP_CONNECTION HTTP_USER_AGENT HTTP_COOKIE".split()

class AdMobError(Exception):
    "Base class for AdMob exceptions."

class AdMob(object):
    """
    Handles requests for ads/analytics from AdMob.
    
    """

    def __init__(self, request, params=None, fail_silently=False):
        """
        `request` - a Django HttpRequest object
        `params` - a dict of parameters to pass to AdMob
        `fail_silently` - set to True to catch exceptions.
        
        """
        self.request = request
        self.session_id = getattr(request.session, 'session_key', None)
        self.params = params or {}
        self.fail_silently = fail_silently

    def build_post_data(self):
        """
        Builds the post data from params and default settings.
        
        """
        self.publisher_id = self.params.get('publisher_id', PUBLISHER_ID)
        self.analytics_id = self.params.get('analytics_id', ANALYTICS_ID)
        self.encoding = self.params.get('encoding', ENCODING)
        self.test = self.params.get('test', TEST)

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
        if 'admobuu' not in self.request.COOKIES:
            if not hasattr(self.request, 'admobuu'):
                self.admobuu = _admob_cookie_value(self.request)
                self.request.admobuu = self.admobuu
            else:
                self.admobuu = self.request.admobuu
        else:
            self.admobuu = self.request.COOKIES['admobuu']
        
        self.post_data = {
          'rt': self.request_type,                       # => request_type
          'z': time.time(),                              # => Time.now.getutc.to_f        
          'u': self.request.META.get('HTTP_USER_AGENT'), # => request.user_agent,
          'i': self.request.META.get('REMOTE_ADDR'),     # => request.remote_ip,
          'p': self.request.build_absolute_uri(),        # => request.request_uri,
          't': self.admob_session_id,                    # => MD5.hexdigest(session_id),
          'v': PUBCODE_VERSION,                          # => PUBCODE_VERSION,
          'o': self.admobuu,                             # => request.cookies['admobuu'][0] || request.env['admobuu'],
          's': self.publisher_id,                        # => publisher_id,
          'a': self.analytics_id,                        # => analytics_id,
          'ma': self.params.get('markup'),               # => params[:markup],
          'd[pc]': self.params.get('postal_code'),       # => params[:postal_code],
          'd[ac]': self.params.get('area_code'),         # => params[:area_code],
          'd[coord]': self.params.get('coordinates'),    # => params[:coordinates],
          'd[dob]': self.params.get('dob'),              # => params[:dob],
          'd[gender]': self.params.get('gender'),        # => params[:gender],
          'k': self.params.get('keywords') ,             # => params[:keywords],
          'search': self.params.get('search'),           # => params[:search],
          'f': self.params.get('format', 'html'),        # => 'html',
          'title': self.params.get('title'),             # => params[:title],
          'event': self.params.get('event'),             # => params[:event]
          'p': self.params.get('page', self.request.build_absolute_uri())  # ### Not in GEM.
        }

        # Add in header data.
        for header, value in self.request.META.iteritems():
            if header.startswith("HTTP") and header not in IGNORE:
                self.post_data["h[%s]" % header] = value

        # Add in optional data        
        if self.test:
            self.post_data['m'] = 'test'
        if self.encoding:
            self.post_data['e'] = self.encoding
        if 'text_only' in self.params:
            self.post_data['y'] = 'text'
            
        # Don't send anything that is `None`
        self.post_data = dict((k, v) for k, v in self.post_data.iteritems() if v is not None)        

    def fetch(self):
        """
        Fetch the AdMob resource using urllib2.urlopen.
        
        """
        original_timeout = socket.getdefaulttimeout()
        socket.setdefaulttimeout(TIMEOUT)
        try:
        
            print self.request.META
        
            print 'POSTING:'
            import pprint
            
            print ENDPOINT
            pprint.pprint(self.post_data)
            self.response = urllib2.urlopen(ENDPOINT, urllib.urlencode(self.post_data))            
            print '---'
            print self.response
            print self.response.read()
            print '---'


        except urllib2.URLError, e:
            if self.fail_silently:
                return ''
            else:
                raise
        else:
            return self.response.read()        
        finally:
            socket.setdefaulttimeout(original_timeout)


def set_admob_cookie(request, response, params=None):
    """
    Given a `response` and `request` set an AdMob cookie.
    
    """
    params = params or {}
    # Don't make a new cookie if one already exists
    if 'admobuu' in request.COOKIES:
        return response
    # Make a new cookie
    if hasattr(request, 'admobuu'):
        value = request.admobuu
    else:
        value = _admob_cookie_value(request)
    expires = cookie_date(0x7fffffff)  # End of 32 bit time.
    path = params.get('cookie_path', COOKIE_PATH)
    domain = params.get('cookie_domain', COOKIE_DOMAIN)
    response.set_cookie('admobuu', value, expires=expires, path=path, domain=domain)
    return response

def _admob_cookie_value(request):
    "Return the AdMob cookie value for this `request`."
    s = "%f%s%s%f" % (
        random.random(),
        request.META.get('HTTP_USER_AGENT', ''),
        request.META.get('REMOTE_ADDR', ''),
        time.time()
    )
    return md5_constructor(s).hexdigest()
    
def admob(request, params=None, fail_silently=False):
    "Ad and Analytics."
    return _admob(request, dict(analytics_request=True, ad_request=True), fail_silently)

def admob_ad(request, params=None, fail_silently=False):
    "Ad only."
    return _admob(request, dict(analytics_request=False, ad_request=True), fail_silently)

def admob_analytics(request, params=None, fail_silently=False):
    "Analytics only."
    return _admob(request, dict(analytics_request=True, ad_request=False), fail_silently)

def _admob(request, params=None, fail_silently=False):
    params = params or {}
    admob = AdMob(request, params, fail_silently)
    admob.build_post_data()
    return admob.fetch()