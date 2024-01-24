from django.urls import path
from users.service.websocket import consumers

websocket_urlpatterns = [
    path("websocket/", consumers.ChatConsumer.as_asgi()),
]
