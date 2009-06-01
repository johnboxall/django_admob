from django.core.handlers.wsgi import WSGIRequest
from django.http import HttpResponse
from django.test import TestCase
from django.test.client import Client

from admob.admob import AdMob, set_cookie


class RequestFactory(Client):
    def request(self, **request):
        environ = {
            'HTTP_COOKIE': self.cookies,
            'PATH_INFO': '/',
            'QUERY_STRING': '',
            'REQUEST_METHOD': 'GET',
            'SCRIPT_NAME': '',
            'SERVER_NAME': 'testserver',
            'SERVER_PORT': 80,
            'SERVER_PROTOCOL': 'HTTP/1.1',
        }
        environ.update(self.defaults)
        environ.update(request)
        return WSGIRequest(environ)

rf = RequestFactory()

# Monkey-patch the fetch method so we don't make actual requests.
def test_fetch(self):
    print 'ADMOB: Making Request...'
    import pprint
    pprint.pprint(self.post_data)
    return ''    
    
AdMob._fetch = test_fetch



class AdMobTest(TestCase):
    def test_set_cookie(self):
        "admob.admob.set_cookie: Don't overwrite existing cookies."
        response = HttpResponse("Test")
        request = rf.get("/", HTTP_USER_AGENT="Test", REMOTE_ADDR="127.0.0.1")

        set_cookie(request, response)
        cookie_value = response.cookies["admobuu"].value
        
        set_cookie(request, response)        
        self.assertEquals(cookie_value, response.cookies["admobuu"].value)