from django.db.models.signals import pre_save, post_save
from django.dispatch import receiver, Signal

from chat.chat_message_resp import ChatMessageRespSchema, ChatMsgRecallRespSchema
from chat.models import RoomFriend, Message, Contact
from users.tasks import send_message_all_async

on_messages = Signal()


@receiver(pre_save, sender=RoomFriend)
def generate_room_key(sender, instance, **kwargs):
    if not instance.room_key:
        # 如果 room_key 不存在，生成并设置它
        uid1, uid2 = sorted([int(instance.uid1.id), int(instance.uid2.id)])
        instance.room_key = f"{uid1}_{uid2}"


@receiver(on_messages, dispatch_uid="on_messages")
def on_message(sender, **kwargs):
    """
    发送消息更新房间收信箱，并同步给房间成员信箱
    Args:
        sender:
        **kwargs:

    Returns:

    """
    msg_id = kwargs.get('msg_id')
    message = Message.objects.get(id=msg_id)
    room = message.room

    resp_message = ChatMessageRespSchema.from_orm(message).dict(exclude_none=True)

    # 所有房间更新房间最新消息
    room.refresh_active_time(message.id, message.create_time)

    if room.is_hot_room():
        # 热门群聊推送所有在线的人
        # TODO 更新热门群聊时间 -redis zset
        # 推送所有人
        message = {
            "type": "send.message",
            "message": {
                "type": 4,
                "data": resp_message

            }
        }
        send_message_all_async.delay(message)
    else:
        member_uid_list = []
        if room.is_room_group():
            # 普通群聊推送所有群成员
            member_uid_list = list(room.roomgroup.groupmember_set.values_list("uid_id", flat=True))
        elif room.is_room_friend():
            uid1 = room.roomfriend.uid1
            uid2 = room.roomfriend.uid2
            member_uid_list = [uid1, uid2]
        # 更新所有群成员的会话时间
        Contact.refresh_or_create_active_time(room.id, member_uid_list, msg_id, message.create_time)
        # TODO 推送房间成员


@receiver(post_save, sender=Message)
def recall_message(sender, instance, signal, created, update_fields, raw, using, **kwargs):
    print(sender)
    print(instance)
    print(signal)
    print(created)
    print(update_fields)
    print(raw)
    print(using)
    print([x for x in kwargs])
    if instance.type == Message.MessageTypeEnum.RECALL:
        resp_message = ChatMsgRecallRespSchema.from_orm(instance).dict()
        message = {
            "type": "send.message",
            "message": {
                "type": 9,
                "data": resp_message

            }
        }
        print(message)
        send_message_all_async.delay(message)