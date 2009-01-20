Django AdMob
============

About:
------

AdMob specializes in ads and analytics for mobile websites. Django AdMob is a pluggable application for Django to help you get up and running with AdMob quickly. Django AdMob is based off the [AdMob RubyGem](http://admob.rubyforge.org/admob/ "RubyForge").

Usage:
------

1. First pull down Django AdMob from github and put it on your `PYTHONPATH`:

git clone git://github.com/johnboxall/django_admob.git admob

2. Add the `AdMobMiddleware` to your `MIDDLEWARE_CLASSES` in settings.py:

MIDDLEWARE_CLASSES = (
    'admob.middleware.AdMobMiddleware',
    ...
)

3. Use `admob_ad` in a template for AdMob ads:

{% load admob_tags %}
...
{% admob_ad %}

4. Use the `analytics` decorator on a view:

from admob.decorators import analytics

@analytics
def view(request):
    ...
    
Technicals:
-----------

We need the Middleware because AdMob uses cookies to help track things. If you use any of the AdMob functions on a request be sure to set `request.has_admob = True` so that the middleware will pick it up and set the cookies appropriately. 