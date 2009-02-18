Django AdMob
============

About:
------

AdMob specializes in ads and analytics for mobile websites. Django AdMob is a pluggable application for Django to help you get up and running with AdMob quickly. Django AdMob is based off the [AdMob RubyGem](http://admob.rubyforge.org/admob/ "RubyForge").

Usage:
------

1. First pull down Django AdMob from github and put it on your `PYTHONPATH`:

        git clone git://github.com/johnboxall/django_admob.git admob

1. Add the `AdMobMiddleware` to your `MIDDLEWARE_CLASSES` in settings.py:

        MIDDLEWARE_CLASSES = (
          'admob.middleware.AdMobMiddleware',
          ...
        )

1. Add AdMob settings in settings.py:

        # Required Settings:
        ADMOB_PUBLISHER_ID = '???'            # Get from AdMob
        ADMOB_ANALYTICS_ID = '???'            # Get from AdMob
        
        # Optional Settings:
        ADMOB_COOKIE_PATH = '/'               # Defaults to '/'
        ADMOB_COOKIE_DOMAIN = '.example.org'  # Defaults to `None`
        ADMOB_ENCODING = 'utf-8'              # Defaults to 'utf-8'
        ADMOB_TEST = True                     # Defaults to `True`

1. Use `admob_ad` in a template for AdMob ads:

        {% load admob_tags %}
        ... 
        {% admob_ad %}

1. Use the `analytics` decorator on a view:

        from admob.decorators import analytics

        @analytics
        def view(request):
          ...
    
Technicals:
-----------

`admob.middleware.AdMobMiddleware` is needed because AdMob uses cookies to help track users. The middleware steps in at the `process_response` phase and looks if any AdMob actions happened by checking if `request.has_admob = True`. If so it sets an AdMob cookie on the response.

Secondly there is some stuff going on with `request.admobuu` - this is the value that the AdMob cookie will eventually have. It's also needed for the AdMob interactions - so we might end up calculating it early and storing it in `request.admobuu` for later use in the middleware.

If you are caching responses with AdMob ads be sure to remove the 'admobuu' attribute from requests so it will be recalculated?