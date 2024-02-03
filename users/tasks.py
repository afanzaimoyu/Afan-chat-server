import logging

import requests
from asgiref.sync import async_to_sync, sync_to_async
from celery import shared_task
from channels.layers import get_channel_layer
from django.core.cache import cache

from users.models import CustomUser
from users.user_schema.ipinfo_schema import Ipinfo

"""
在window中，一定要指定协程库，否则会报错 （eventlet/gevent）
celery -A config.celery_app worker -l INFO -Q single_process_queue --concurrency=1
celery -A config.celery_app worker -l INFO -Q send_message_queue
Celery -A config.celery_app -b "redis://127.0.0.1:6379/1" flower --address=127.0.0.1 --port=5555
Celery -A config.celery_app worker -l info -P eventlet
"""

logger = logging.getLogger(__name__)


def retry_on_failure(self, countdown=10, exc=None):
    try:
        logger.info(f"重试任务 {self.request.id} 在 {countdown} 秒后")
        raise self.retry(exc=exc, countdown=countdown)
    except self.MaxRetriesExceededError:
        logger.warning(f"{self.request.id} 超出了任务的最大重试次数")


# @shared_task(bind=True, max_retries=5, rate_limit='5/s', ignore_result=True, queue='refresh_ip_queue')
@shared_task(bind=True, max_retries=5, rate_limit='5/s', ignore_result=True)
def refresh_ip_detail_async(self, uid):
    logger.info("celery 准备更新用户ip信息")
    user = CustomUser.objects.get(id=uid)
    user_ipinfo = user.ip_info
    if not user_ipinfo:
        logger.info("用户ip信息为空")
        return
    # 根据updateip和updateipdetail判断是否需要更新，
    # 如果updateipdetail中的ip和updateip中的ip相同，则不需要更新，不同或者updateipdetail为空，则需要更新

    if user_ipinfo.get("updateIp") == user_ipinfo.get("updateIpDetail", {}).get("ip"):
        logger.info("用户ip信息无需更新")
        return
    # 获取详细
    ipinfo = Ipinfo(**user_ipinfo)

    url = f"https://ip.taobao.com/outGetIpInfo?ip={ipinfo.updateIp}&accessKey=alibaba-inc"
    try:
        response = requests.get(url)
        response.raise_for_status()
        data = response.json()
        if data.get('data'):
            ipinfo.refresh_ip(data.get('data'))
            user.ip_info = ipinfo.dict()
            user.save(update_fields=['ip_info'])
            logger.info(f"用户{user.name}ip信息更新成功-->{ipinfo.dict()}")
        else:  # 请求超过最大QPS
            retry_on_failure(self)
    except requests.exceptions.RequestException as exc:
        # 如果请求失败，等待2秒后重试
        retry_on_failure(self, countdown=10, exc=exc)
    # 数据保存失败，等待2秒后重试


@shared_task(ignore_result=True)
def send_message_all_async(message):
    # TODO send_to_all_oline已实现 待删除
    # TODO 优化任务过多的问题    任务队列满了，就不再发送任务
    # 发送失败，查询是channels layer 的原因 换channels-redis可以
    # 参考 : https://stackoverflow.com/questions/57595453/getting-django-channel-access-in-celery-task
    try:
        print("发送消息")
        print(message)
        channel_layer = get_channel_layer()
        async_to_sync(channel_layer.group_send)("chat_group", message)
    except Exception as e:
        print("error", e)


@shared_task(ignore_result=True)
def send_to_all_oline(resp):
    logger.info("celery 发送消息")
    message = {
        "type": "out_send_msg",
        "message": resp
    }
    channel_layer = get_channel_layer()
    try:
        async_to_sync(channel_layer.group_send)("chat_group", message)
    except Exception as e:
        logger.error('发送全部消息失败，失败原因：-->', e)


@shared_task(ignore_result=True)
def send_message_async(member_uid_list, message):
    try:
        print("发送消息")
        print(message)
        for uid in member_uid_list:
            channel = cache.get(uid)
            if not channel:
                continue
            channel_layer = get_channel_layer()
            async_to_sync(channel_layer.send)(channel, message)
    except Exception as e:
        print("error", e)
