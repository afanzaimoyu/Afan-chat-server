from django.urls import path
from users import consumers

websocket_urlpatterns = [
    path("websocket/", consumers.ChatConsumer.as_asgi()),
]
