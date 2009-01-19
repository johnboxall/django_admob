"""
Make an AdMob ad/analytics request. The first param is the request variable from Rails; the second is a unique session
identifier. In general, requests should always be of the form <tt><%= AdMob::request(request, session.session_id, ...) %></tt>.
Regardless of how many times AdMob::request is called, only one analytics call will be made per page load.
The remaining params set optional features of the request. Params that can be set are:

[<tt>:publisher_id</tt>] your admob publisher_id, a default can be set using <tt>AdMob::config {|c| c.publisher_id = "YOUR_PUBLISHER_ID"}</tt>
[<tt>:analytics_id</tt>] your admob analytics_id, a default can be set using <tt>AdMob::config {|c| c.analytics_id = "YOUR_ANALYTICS_ID"}</tt>
[<tt>:ad_request</tt>] whether to make an ad request, defaults to true
[<tt>:analytics_request</tt>] whether to make an analytics request, defaults to true
[<tt>:encoding</tt>] char encoding of the response, either "UTF-8" or "SJIS", defaults to UTF-8
[<tt>:markup</tt>] your site's markup, e.g. "xhtml", "wml", "chtml"
[<tt>:postal_code</tt>] postal code of the current user, e.g. "94401"
[<tt>:area_code</tt>] area code of the current user, e.g. "415"
[<tt>:coordinates</tt>] lat/long of the current user, comma separated, e.g. "37.563657,-122.324807"
[<tt>:dob</tt>] date of birth of the current user, e.g. "19800229"
[<tt>:gender</tt>] gender of the current user, e.g. "m" or "f"
[<tt>:keywords</tt>] keywords, e.g. "ruby gem admob"
[<tt>:search</tt>] searchwords (much more restrictive than keywords), e.g. "ruby gem admob"
[<tt>:title</tt>] title of the page, e.g. "Home Page"
[<tt>:event</tt>] the event you want to report to analytics, e.g. "reg_success"
[<tt>:text_only</tt>] if set to true, don't return a banner ad for this request
[<tt>:test</tt>] whether this should issue a test ad request, not a real one
[<tt>:timeout</tt>] override the default timeout value for this ad request in seconds, e.g. 2
[<tt>:raise_exceptions</tt>] whether to raise exceptions when something goes wrong (defaults to false); exceptions will all be instances of 
"""
import time
import socket
import urllib
import urllib2
import random

from django.conf import settings
from django.utils.hashcompat import md5_constructor
from django.utils.http import cookie_date

from django.contrib.sites.models import Site
 
ENDPOINT = "http://r.admob.com/ad_source.php"
TIMEOUT = 1  # Timeout in seconds.
PUBCODE_VERSION = None # Not sure what to put here??? 
PUBLISHER_ID = getattr(settings, 'ADMOB_PUBLISHER_ID')
ANALYTICS_ID = getattr(settings, 'ADMOB_ANALYTICS_ID')
COOKIE_PATH = getattr(settings, 'ADMOB_COOKIE_PATH', '/')
COOKIE_DOMAIN = getattr(settings, 'ADMOB_COOKIE_DOMAIN', None)
# Need to be reworked for Django???
IGNORE_HEADERS = [
    'HTTP_PRAGMA', 
    'HTTP_CACHE_CONTROL',
    'HTTP_CONNECTION',
    'HTTP_USER_AGENT',
    'HTTP_COOKIE',
]

ENCODING_DEFAULT = 'utf-8'
TEST_DEFAULT = True

class AdMobError(Exception):
    pass

class AdMob(object):
    def __init__(self, request, params=None, fail_silently=False):
        self.request = request
        self.session_id = getattr(request.session, 'session_key', None)
        self.params = params or {}
        self.fail_silently = fail_silently

    def build_post_data(self):
        self.publisher_id = self.params.get('publisher_id', PUBLISHER_ID)
        self.analytics_id = self.params.get('analytics_id', ANALYTICS_ID)
        self.encoding = self.params.get('encoding', ENCODING_DEFAULT)
        self.test = self.params.get('test', TEST_DEFAULT)

        # Determine the type of request
        self.analytics_request = self.params.get("analytics_request", False)
        self.ad_request = self.params.get("ad_request", True)
        
        print "analytics_request: %s" % repr(self.analytics_request)
        print "ad_request: %s" % repr(self.ad_request)

        self.request_type = {
            (False, False): None,
            (True, False): 0,
            (False, True): 1,
            (True, True): 2    
        }[(self.ad_request, self.analytics_request)]

        # Admob gets an MD5 hash of the session.
        if self.session_id is not None:
            self.admob_session_id = md5_constructor(self.session_id).hexdigest()
        else:
            self.admob_session_id = None

        # Build the basic request
        self.post_data = {
          'rt': self.request_type,
          'z': time.time(),                              # => Time.now.getutc.to_f        
          'u': self.request.META.get('HTTP_USER_AGENT'), # => request.user_agent,
          'i': self.request.META.get('REMOTE_ADDR'),     # => request.remote_ip,
          'p': self.request.build_absolute_uri(),        # => request.request_uri,
          't': self.admob_session_id,                    # => MD5.hexdigest(session_id),
          'v': PUBCODE_VERSION,                          # => PUBCODE_VERSION,
          'o': self.request.COOKIES.get('admobuu'),      # => request.cookies['admobuu'][0] || request.env['admobuu'],
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
          'event': self.params.get('event')              # => params[:event]
        }

        ## Not sure what the Rails would end up sending there... so fake it!
        # Add in headers
        #  for k, v in self.request.META.iteritems():
        #    if k not in IGNORE_HEADERS:
        #        self.post_data["h[%s]" % k] = v

        # Add in optional data
        if self.encoding:
            self.post_data['e'] = self.encoding
        if 'text_only' in self.params:
            self.post_data['y'] = 'text'
        if self.test:
            self.post_data['m'] = 'test'
            
        # Don't send anything that's nil (but send if empty string)
        self.post_data = dict((k, v) for k, v in self.post_data.iteritems() if v is not None)
        
        print self.post_data
        

    def fetch(self):
        original_timeout = socket.getdefaulttimeout()
        socket.setdefaulttimeout(TIMEOUT)
        try:
            self.response = urllib2.urlopen(ENDPOINT, urllib.urlencode(self.post_data))            
            return self.response.read()
        except urllib2.HTTPError, e:
            if self.fail_silently:
                pass
            else:
                raise e
        finally:
            socket.setdefaulttimeout(original_timeout)

def admob_ad(request, params=None, fail_silently=False):
    params = params or {}
    params.update({'analytics_request': False, 'ad_request': True})
    admob = AdMob(request, params, fail_silently)
    admob.build_post_data()
    return admob.fetch()


def admob_analytics(request, params=None, fail_silently=False):
    params = params or {}
    params.update({'analytics_request': True, 'ad_request': False})
    admob = AdMob(request, params, fail_silently)
    admob.build_post_data()
    return admob.fetch()

def set_admob_cookie(request, response, params=None):
    """
    Given a `response` and `request` set an AdMob cookie.
    
    """
    params = params or {}
    # Don't make a new cookie if one already exists    
    if 'admobuu' in request.COOKIES:
        return response
    # Make a new cookie
    s = "%f%s%s%f" % (
        random.random(),
        request.META.get('HTTP_USER_AGENT', ''),
        request.META.get('REMOTE_ADDR', ''),
        time.time()
    )
    value = md5_constructor(s).hexdigest()
    expires = cookie_date(0x7fffffff)  # End of 32 bit time.
    path = params.get('cookie_path') or COOKIE_PATH
    domain = params.get('cookie_domain') or COOKIE_DOMAIN
    response.set_cookie('admobuu', value, expires=expires, path=path, domain=domain)
    return response