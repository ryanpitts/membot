from django.conf import settings
from django.conf.urls import url, patterns, include
from django.contrib import admin

from .views import homepage, CommandView, MessageView

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
    url(
        regex   = '^message/inbound/$',
        view    = MessageView.as_view(),
        kwargs  = {},
        name    = 'message_inbound',
    ),
    url(r'^admin/', include(admin.site.urls)),
)
