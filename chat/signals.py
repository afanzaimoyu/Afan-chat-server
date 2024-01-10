from django.db.models.signals import pre_save, post_save, post_delete
from django.dispatch import receiver, Signal

from chat.chat_message_resp import ChatMessageRespSchema, ChatMsgRecallRespSchema, ChatMessageMarkRespSchema
from chat.member_resp import WSMemberChange
from chat.models import RoomFriend, Message, Contact, MessageMark
from chat.tasks import ws_push_member_change
from users.signals import distribute_items
from users.tasks import send_message_all_async

on_messages = Signal()
send_add_msg = Signal()


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
        # TODO 如果redis保存了热门群聊 更新热门群聊时间 -redis zset

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


@receiver(post_save, sender=MessageMark)
def update_or_create_mark(sender, instance, created, **kwargs):
    add_item_and_push(instance)


@receiver(post_delete, sender=MessageMark)
def delete_mark(sender, instance, **kwargs):
    add_item_and_push(instance)


def add_item_and_push(instance):
    # 如果不是文本消息，直接返回
    # 获取消息被标记的次数。
    # 根据标记的类型和次数，判断是否满足升级条件。如果满足条件，给用户发送一张徽章
    # 通过推送服务（pushService）发送推送消息，通知所有相关用户消息标记的情况。
    message_type = instance.msg.type
    if message_type != Message.MessageTypeEnum.TEXT:
        return
    mark_count = instance.mark_count()
    print(instance.user_id)
    print(type(instance.msg_id))
    resp = ChatMessageMarkRespSchema(
        uid=instance.user_id,
        msgId=instance.msg_id,
        markType=instance.type,
        actType=instance.st,
        markCount=instance.mark_count()
    )
    if mark_count >= 10:
        distribute_items(instance.msg.from_user, 2, 2, instance.msg.id)
    message = {
        "type": "send.message",
        "message": {
            "type": 8,
            "data": resp.dict()

        }
    }
    print(message)
    send_message_all_async.delay(message)


@receiver(send_add_msg, dispatch_uid='send_add_msg')
def send_add_msgs(sender, **kwargs):
    member_list = kwargs.get('group_members')
    room_group = kwargs.get('room_group')
    user = kwargs.get('user')
    room_user_list = list(map(lambda x: x.uid, member_list))
    chat_message_req = build_group_add_message(room_group, user, room_user_list)
    chat_message_req.send_msg(2)

@receiver(send_add_msg, dispatch_uid='send_add_msg')
def send_change_push(sender, **kwargs):
    member_list = kwargs.get('group_members')
    room_group = kwargs.get('room_group')
    for member in member_list:
        resp = WSMemberChange(
            roomId=room_group.room_id,
            uid=member.uid_id,
            changeType=1,
            activeStatus=member.uid.is_active,
            lastOptTime=member.uid.last_login,
        )
        message = {
            "type": "send.message",
            "message": {
                "type": 11,
                "data": resp.dict()

            }
        }
        ws_push_member_change.delay(message)


def build_group_add_message(room_group, user, room_user_list):
    member_name = ','.join(map(lambda x: f"'{x.name}'", room_user_list))
    body = f"\"{user.name}\"邀请{member_name}加入群聊"
    from chat.chat_schema import MessageInput

    return MessageInput(
        roomId=room_group.room_id,
        msgType=Message.MessageTypeEnum.SYSTEM,
        body=body
    )

