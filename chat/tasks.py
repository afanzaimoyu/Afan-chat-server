from asgiref.sync import async_to_sync
from celery import shared_task
from channels.layers import get_channel_layer
from django.core.cache import cache


@shared_task(ignore_result=True)
def ws_push_member_change(message,to=None):
    if to:
        uid = to
    else:
        uid = message['message']["message"]["data"]["uid"]
    channel = cache.get(uid)
    channel_layer = get_channel_layer()
    async_to_sync(channel_layer.send)("channel", message)
