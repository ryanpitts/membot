from django.urls import path, re_path

from .views import hello, CommandView, MessageView

urlpatterns = [
    re_path('^$', hello, {}, 'membot_hello',),
    re_path('^hey-bmo/$', CommandView.as_view(), {}, 'hey_bmo_command',),
    re_path('^message/inbound/$', MessageView.as_view(), {}, 'membot_message_inbound',),
]
