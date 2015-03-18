from django.conf import settings
from django.conf.urls import url, patterns, include
from django.contrib import admin

from .views import hello, MembotCommandView, RevisedCommandView, MessageView

urlpatterns = patterns('',
    url(
        regex   = '^$',
        view    = hello,
        kwargs  = {},
        name    = 'membot_hello',
    ),
    url(
        regex   = '^hey-cody/$',
        view    = RevisedCommandView.as_view(),
        kwargs  = {},
        name    = 'hey_cody_command',
    ),
    url(
        regex   = '^command/$',
        view    = MembotCommandView.as_view(),
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
