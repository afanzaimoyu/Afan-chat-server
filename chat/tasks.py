from asgiref.sync import async_to_sync, sync_to_async
from celery import shared_task
from channels.layers import get_channel_layer
from django.core.cache import cache


@shared_task(ignore_result=True)
def ws_push_member_change(message=None, to=None):
    print(message, to)
    if to:
        uid = to
    else:
        uid = message['message']["message"]["data"]["uid"]
    channel = cache.get(uid)
    print('channel=', channel)
    if channel:
        channel_layer = get_channel_layer()
        sync_to_async(channel_layer.send)(channel, message)
