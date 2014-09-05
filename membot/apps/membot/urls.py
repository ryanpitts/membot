from django.conf import settings
from django.conf.urls import url, patterns, include

from .views import homepage

urlpatterns = patterns('',
    url(
        regex   = '^$',
        view    = homepage,
        kwargs  = {},
        name    = 'homepage',
    ),
)
