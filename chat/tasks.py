from asgiref.sync import async_to_sync
from celery import shared_task
from channels.layers import get_channel_layer
from django.core.cache import cache


@shared_task(ignore_result=True)
def ws_push_member_change(message):
    # TODO 优化任务过多的问题    任务队列满了，就不再发送任务
    # TODO 发送失败，查询是channels layer 的原因 换channels-redis也许可以
    # 参考 : https://stackoverflow.com/questions/57595453/getting-django-channel-access-in-celery-task
    uid = message['message']["message"]["data"]["uid"]
    channel = cache.get('uid')
    channel_layer = get_channel_layer()
    async_to_sync(channel_layer.send)("channel", message)
