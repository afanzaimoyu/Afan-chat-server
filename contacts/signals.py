from asgiref.sync import async_to_sync
from channels.layers import get_channel_layer
from django.core.cache import cache
from django.db.models.signals import post_save, post_delete, pre_delete
from django.db.transaction import on_commit
from django.dispatch import receiver, Signal
from django.utils import timezone

from contacts.models import UserApply
from users.tasks import refresh_ip_detail_async, send_message_all_async


@receiver(post_save, sender=UserApply)
def user_apply_message(sender, instance, created, **kwargs):
    print("UserApply post_save")
    un_read_count = UserApply.objects.filter(target_id=instance.uid, read_status=UserApply.ReadStatus.UNREAD).count()
    message = {
        "type": "send.message",
        "message": {
            "type": 10,
            "data": {
                "uid": instance.target_id,
                "unreadCount": un_read_count
            }
        }
    }
    channel_name = cache.get(instance.uid_id)
    print(channel_name)
    channel_layer = get_channel_layer()
    async_to_sync(channel_layer.send)(channel_name, message)
