from typing import List

from django.db import transaction
from ninja_extra import service_resolver
from ninja_extra.controllers import RouteContext
from ninja_schema import Schema, model_validator
from pydantic import Field

from chat.models import RoomGroup, GroupMember, Room
from chat.signals import send_add_msg
from users.exceptions.chat import Business_Error
from users.models import CustomUser


class IdInput(Schema):
    id: int = Field(..., description="房间id/会话id")

    @model_validator("id")
    def validate_room_id(cls, value):
        query = RoomGroup.objects.filter(room_id=value)
        if query.exists():
            cls.room_group = query.get()
            return value
        else:
            raise Business_Error(detail="roomId有误", code=0)

    def get_group_detail(self, user):
        # TODO 如果是热门群聊改为从redis获取人数
        online_num = self.room_group.groupmember_set.filter(uid__is_active=1).count()

        group_role = self.get_group_role(user)
        return dict(
            avatar=self.room_group.avatar,
            roomId=self.room_group.room_id,
            groupName=self.room_group.name,
            onlineNum=online_num,
            role=group_role,
        )

    def get_member_list(self):
        if self.room_group.room.is_hot_room():
            # 全员群只展示所有用户前100
            member_list = list(
                self.room_group.groupmember_set.filter(uid__status=0).order_by('-uid__update_time')[:1000].values(
                    'uid__id', 'uid__name', 'uid__avatar'))
        else:
            member_list = list(
                self.room_group.groupmember_set.filter(uid__status=0).order_by('-uid__update_time').values(
                    'uid__id', 'uid__name', 'uid__avatar'))
        return member_list

    def get_group_role(self, user):
        member = self.room_group.groupmember_set.get(uid=user) if not user.is_anonymous else None
        if member:
            return member.role
        elif member.group.room.is_hot_room():
            return member.Role.ORDINARY_MEMBERS
        else:
            return member.Role.REMOVE


class GroupAddReq(Schema):
    uidList: List[int] = Field(..., description="邀请的id", max_items=50, min_items=1)

    @transaction.atomic
    def add_group(self):
        context: RouteContext = service_resolver(RouteContext)
        user: CustomUser = context.request.user

        room_group = self.creat_group_room(user)
        # 批量保存群成员
        group_members = list(map(lambda x: self.add_member(x, room_group), self.uidList))
        # 发送邀请加群消息  --> 触发每个人的会话
        send_add_msg.send(sender=self.__class__, room_group=room_group, group_members=group_members, user=user)

    @staticmethod
    def creat_group_room(user):
        if GroupMember.objects.filter(uid=user, role=GroupMember.Role.GROUP_LEADER).exists():
            raise Business_Error(detail="每个人只能创建一个群", code=0)

        room = Room.objects.create(type=Room.Type.GROUP_CHAT)

        room_group = RoomGroup.objects.create(room=room, name=f'{user.name}的群组', avatar=user.avatar)

        GroupMember.objects.create(role=GroupMember.Role.GROUP_LEADER, group=room_group, uid=user)

        return room_group

    @staticmethod
    def add_member(user, room_group):
        group_member, _ = GroupMember.objects.get_or_create(role=GroupMember.Role.ORDINARY_MEMBERS, group=room_group,
                                                            uid_id=user)
        return group_member
