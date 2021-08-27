from django.conf import settings
from django.conf.urls import url, patterns, include
from django.contrib import admin

urlpatterns = patterns('',
    url(r'^membot/', include('membot.apps.membot.urls')),
    #url(r'^admin/', include(admin.site.urls)),
)

if settings.DEBUG:
    from django.contrib.staticfiles.urls import staticfiles_urlpatterns
    urlpatterns += staticfiles_urlpatterns()
