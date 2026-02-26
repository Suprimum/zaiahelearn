from django.urls import re_path
from .consumers import ChatConsumer

websocket_urlpatterns = [
    re_path(r'ws/classroom/(?P<classroom_id>\d+)/$', ChatConsumer.as_asgi()),
]
