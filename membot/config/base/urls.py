from django.conf import settings
from django.urls import path, include

urlpatterns = [
    path('membot/', include('membot.apps.membot.urls')),
]

if settings.DEBUG:
    from django.contrib.staticfiles.urls import staticfiles_urlpatterns
    urlpatterns += staticfiles_urlpatterns()
