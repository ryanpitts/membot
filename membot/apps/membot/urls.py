from django.conf import settings
from django.conf.urls import url, patterns, include

from .views import homepage, CommandView

urlpatterns = patterns('',
    url(
        regex   = '^$',
        view    = homepage,
        kwargs  = {},
        name    = 'homepage',
    ),
    url(
        regex   = '^command/$',
        view    = CommandView.as_view(),
        kwargs  = {},
        name    = 'command',
    ),
)
