from asgiref.sync import async_to_sync, sync_to_async
from channels.layers import get_channel_layer
from django.contrib.auth.models import update_last_login
from django.core.cache import cache
from django.db.models.signals import post_save, post_delete, pre_delete
from django.db.transaction import on_commit
from django.dispatch import receiver, Signal
from django.utils import timezone

from .models import *
from .user_schema.ipinfo_schema import Ipinfo
from .user_tools.cache_lock import distribute_item
from users.tasks import refresh_ip_detail_async, send_message_all_async

user_online_signal = Signal()


@distribute_item
def distribute_items(user_instance, item_id, idempotent_enum, business_id, idempotent=None):
    """
    发放物品功能
        如需默认佩戴，子类继承该方法进行修改
    Args:
        user_instance: 用户实例
        item_id: 要发放的物品id
        idempotent_enum: 幂等类型  1:UID  2:消息id
        business_id: 业务唯一标识
        idempotent: 幂等键 ！！无需传入，装饰器自动组装！！

    Returns:

    """
    with transaction.atomic():
        # 检查是否已发放过
        if user_instance.userbackpack_set.filter(idempotent=idempotent).exists():
            return
        # 检查物品是否存在
        if not ItemConfig.objects.filter(id=item_id).exists():
            return
        # 检查用户是否已经有相同的徽章
        if item_id in user_instance.get_user_badges:
            return
        # 发放物品
        user_instance.backpacks.add(item_id, through_defaults={"idempotent": idempotent})
    return user_instance


def update_blacklist_cache():
    black_ipx_key = "black_ipx"

    blacklist = list(Blacklist.objects.all().values_list("target", flat=True).distinct())

    if blacklist:
        cache.set(black_ipx_key, blacklist)
    print("缓存更新成功")


@receiver(post_save, sender=CustomUser)
def create_rename_card(sender, instance, created, **kwargs):
    if created:
        distribute_items(instance, 1, 1, instance)

        user_list = len(CustomUser.objects.all())
        if user_list <= 10:
            distribute_items(instance, 3, 1, instance)
        if user_list <= 100:
            distribute_items(instance, 4, 1, instance)


# 当黑名单添加了type=2的时候，就会调用这个方法
@receiver(post_save, sender=Blacklist)
def change_user_status(sender, instance, created, **kwargs):
    if created:
        if instance.type == 2:
            user = CustomUser.objects.get(id=instance.target)
            user.status = 1
            user.save(update_fields=['status'])
            print("修改成功")
    update_blacklist_cache()


@receiver(post_delete, sender=Blacklist)
def clear_black_cache(sender, instance, **kwargs):
    update_blacklist_cache()


@receiver(post_save, sender=Blacklist)
def send_message(sender, instance, created, **kwargs):
    if created:
        if instance.type == 2:
            print("发送消息")
            message = {
                "type": "send.message.all",
                "message": {
                    "user": instance.target,
                }
            }
            send_message_all_async.delay(message)


@receiver(user_online_signal, dispatch_uid="user_online")
def user_online(sender, **kwargs):
    # 更新 时间，在线状态，ip信息
    user: CustomUser = kwargs.get('user')
    ip = kwargs.get('ip')

    user.last_login = timezone.now()
    user.is_active = 1
    user.refresh_ip(ip)
    user.save()
    print("更新成功")

    # 解析ip
    on_commit(lambda: refresh_ip_detail_async.delay(user.id))
    print("解析成功")
