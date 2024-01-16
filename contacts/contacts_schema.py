from typing import Optional, TypeVar, List, Any

from django.db import transaction
from django.db.models import Q
from ninja_extra import service_resolver
from ninja_extra.controllers import RouteContext
from ninja_extra.schemas.response import Url
from ninja_schema import Schema, ModelSchema, model_validator
from pydantic import Field, model_validator as pydantic_model_validator

from chat.models import Room, RoomFriend, Message
from contacts.models import UserFriend, UserApply
from users.exceptions.chat import Business_Error
from users.models import CustomUser


class CheckUserInput(Schema):
    uidlist: List[int]

    def are_friends_list(self, friend_uids):
        are_friends_list = []
        for uid in self.uidlist:
            is_friend = uid in friend_uids
            are_friends_list.append({"uid": uid, "isFriend": is_friend})
        return are_friends_list


class ApplyInput(Schema):
    target_id: int = Field(alias="targetUid")
    msg: str

    @model_validator("target_id")
    def validate_uid(cls, value_data):
        context: RouteContext = service_resolver(RouteContext)
        user = context.request.user

        if user.id == value_data:
            raise Business_Error(detail="不能添加自己", code=0)
        elif UserApply.objects.filter(uid=user.id, target_id=value_data, type=UserApply.Type.ADD_FRIEND,
                                      status=UserApply.Status.PENDING).exists():
            raise Business_Error(detail="好友申请发送过了", code=0)
        elif UserFriend.objects.filter(uid=user.id, friend_id=value_data).exists():
            raise Business_Error(detail="你们已经是好友了", code=0)

        elif UserApply.objects.filter(uid=value_data, target_id=user.id).exists():
            pass

        return value_data


class APPlyPageOut(Schema):
    applyId: int = Field(alias="id")
    type: int
    msg: str
    status: int
    uid: int = Field(alias="uid_id")


class CustomUserFriend(Schema):
    activeStatus: int = Field(alias="is_active")
    uid: int = Field(alias="id")

    @pydantic_model_validator(mode="before")
    def extract_name(cls, values):
        if values:
            friend_data = values.friend
            # print(values)
            # print(cls.__annotations__)
            # for field in cls.__annotations__:
            #     if hasattr(friend_data, field):
            #         setattr(values, field, getattr(friend_data, field))
            return friend_data


class DeleteFriendInput(Schema):
    uid: int

    @model_validator("uid")
    def validate_uid(cls, value_data):
        context: RouteContext = service_resolver(RouteContext)
        user = context.request.user

        if user.id == value_data:
            raise Business_Error(detail="不能删除自己", code=0)

        cls.queryset = UserFriend.objects.filter(Q(friend_id=value_data, uid=user) | Q(uid=value_data, friend_id=user))
        print(cls.queryset.values_list("delete_status").first()[0])

        if not cls.queryset.exists():
            raise Business_Error(detail=f"{user.id}, {value_data}没有好友关系", code=0)

        if cls.queryset.values_list("delete_status").first()[0] == UserFriend.Delete.DELETED:
            raise Business_Error(detail=f"{value_data}已经删除了", code=0)

    def delete_friend(self, user):
        # 禁用房间
        self.queryset.update(delete_status=UserFriend.Delete.DELETED)

        # assert 好友数量不对
        # 获得roomkey 逻辑删除房间
        # disable_friend_room(user.id,self.uid)


class ApproveInput(Schema):
    applyId: int

    @model_validator("applyId")
    def validate_uid(cls, value_data):
        context: RouteContext = service_resolver(RouteContext)
        user = context.request.user

        if not UserApply.objects.filter(id=value_data).exists():
            raise Business_Error(detail="不存在申请记录", code=0)
        elif UserApply.objects.filter(id=value_data, status=UserApply.Status.APPROVED).exists():
            raise Business_Error(detail="已同意好友申请", code=0)
        return value_data

    @transaction.atomic
    def agree_to_the_application(self, user):

        # 同意申请
        user_apply = UserApply.objects.get(id=self.applyId)
        user_apply.status = UserApply.Status.APPROVED
        user_apply.save()
        # 添加好友关系
        UserFriend.objects.create(uid_id=user_apply.uid_id, friend_id=user_apply.target_id)
        UserFriend.objects.create(uid_id=user_apply.target_id, friend_id=user_apply.uid_id)
        # 创建一个聊天房间
        ## assert 好友数量不对，创建失败
        ## 创建房间表数据 id大小排序，小的在前 返回key
        ## 查询key
        ## 如果存在好友就恢复房价，否则创建房间
        ## 先创建room 再创建room friend
        # room_friend = xxxx.creat_friend_room(user.id, self.uid)
        # 发送消息 ： 我们已经是好友了，开始聊天吧

        room = Room.objects.create(type=Room.Type.ONE_ON_ONE_CHAT)
        uid1, uid2 = sorted([user_apply.uid_id, user_apply.target_id])
        key = f"{uid1}_{uid2}"
        room_friend_q = RoomFriend.objects.filter(room_key=key)
        if room_friend_q.exists():
            # 恢复房间
            room_friend = room_friend_q.get()
            room_friend.status = RoomFriend.Status.NORMAL
            room_friend.save()
        else:
            RoomFriend.objects.create(room=room, uid1_id=uid1, uid2_id=uid2, status=RoomFriend.Status.NORMAL)

        from chat.chat_schema import MessageInput
        MessageInput(roomId=room.id, msgType=Message.MessageTypeEnum.TEXT,
                     body={"content": "我们已经是好友了，开始聊天吧"}).send_msg(user.id)
