from django.db.models.signals import pre_save
from django.dispatch import receiver

from chat.models import RoomFriend


@receiver(pre_save, sender=RoomFriend)
def generate_room_key(sender, instance, **kwargs):
    if not instance.room_key:
        # 如果 room_key 不存在，生成并设置它
        uid1, uid2 = sorted([int(instance.uid1.id), int(instance.uid2.id)])
        instance.room_key = f"{uid1}_{uid2}"