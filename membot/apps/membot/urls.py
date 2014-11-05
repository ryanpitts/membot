from django.conf import settings
from django.conf.urls import url, patterns, include
from django.contrib import admin

from .views import hello, CommandView, MessageView

urlpatterns = patterns('',
    url(
        regex   = '^$',
        view    = hello,
        kwargs  = {},
        name    = 'membot_hello',
    ),
    url(
        regex   = '^command/$',
        view    = CommandView.as_view(),
        kwargs  = {},
        name    = 'membot_command',
    ),
    url(
        regex   = '^message/inbound/$',
        view    = MessageView.as_view(),
        kwargs  = {},
        name    = 'membot_message_inbound',
    ),
)
