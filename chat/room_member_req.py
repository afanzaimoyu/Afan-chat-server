from collections import OrderedDict
from datetime import datetime, timezone
from typing import List

from django.db import transaction
from django.db.models import Q, Subquery
from ninja_extra import service_resolver
from ninja_extra.controllers import RouteContext
from ninja_schema import Schema, model_validator
from pydantic import Field

from chat.chat_room_resp import ChatRoomCursorInputSchema
from chat.models import RoomGroup, GroupMember, Room
from chat.signals import send_add_msg, send_delete_msg
from users.exceptions.chat import Business_Error
from users.models import CustomUser


class IdsInput(Schema):
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
        if self.room_group.room.is_hot_room():
            online_num = CustomUser.objects.filter(is_active=1).count()
            group_role = GroupMember.Role.ORDINARY_MEMBERS
        else:
            online_num = self.room_group.groupmember_set.filter(uid__is_active=1).count()

            group_role = self.get_group_role(user)
        return dict(
            avatar=self.room_group.avatar,
            roomId=self.room_group.room_id,
            groupName=self.room_group.name,
            onlineNum=online_num,
            role=group_role,
        )

    def get_group_role(self, user):
        member = self.room_group.groupmember_set.get(uid=user) if not user.is_anonymous else None
        if member:
            return member.role
        else:
            return member.Role.REMOVE


class IdInput(Schema):
    roomId: int = Field(..., description="房间id/会话id")

    @model_validator("roomId")
    def validate_room_id(cls, value):
        query = RoomGroup.objects.filter(room_id=value)
        if query.exists():
            cls.room_group = query.get()
            return value
        else:
            raise Business_Error(detail="roomId有误", code=0)

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
        return room_group.room_id

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


class MemberAddReq(GroupAddReq):
    roomId: int

    @model_validator("roomId")
    def validate_room_id(cls, value):
        context: RouteContext = service_resolver(RouteContext)
        user: CustomUser = context.request.user

        query = RoomGroup.objects.filter(room_id=value)
        if query.exists():
            room_group = query.get()
            if room_group.room.is_hot_room():
                raise Business_Error(detail="全员群无需邀请好友", code=0)
            elif not room_group.groupmember_set.filter(uid_id=user.id).exists():
                raise Business_Error(detail="您不是群成员", code=0)
            cls.room_group = room_group
            return value
        else:
            raise Business_Error(detail="roomId有误", code=0)

    @transaction.atomic
    def add_members(self, user):
        group_members = list(map(lambda x: self.add_member(x, self.room_group), self.uidList))

        send_add_msg.send(sender=self.__class__, room_group=self.room_group, group_members=group_members, user=user)


class MemberDelReq(Schema):
    roomId: int
    uid: int

    def validate_room_id(self, user):

        query = RoomGroup.objects.filter(room_id=self.roomId)
        if query.exists():
            room_group = query.get()
            if not room_group.groupmember_set.filter(uid=user, role__in=[GroupMember.Role.GROUP_LEADER,
                                                                         GroupMember.Role.ADMINISTRATOR]).exists():
                raise Business_Error(detail="您不是群管理", code=0)
            elif not room_group.groupmember_set.filter(uid_id=self.uid).exists():
                raise Business_Error(detail="用户已经移除", code=0)
            return room_group
        else:
            raise Business_Error(detail="roomId有误", code=0)

    @transaction.atomic
    def delete_member(self, user):
        room_group = self.validate_room_id(user)
        room_group.groupmember_set.get(uid_id=self.uid).delete()
        # 发送移除时间告诉群成员
        member_uid_list = list(room_group.groupmember_set.all().values_list('uid_id', flat=True))

        send_delete_msg.send(sender=self.__class__, room_group=room_group, member_uid_list=member_uid_list,
                             uid=self.uid)


class MemberExitReq(Schema):
    roomId: int

    def validate_room_id(self, user):
        query = RoomGroup.objects.filter(room_id=self.roomId)
        if query.exists():
            room_group = query.get()
            if room_group.room.is_hot_room():
                raise Business_Error(detail="全员群不能退出", code=0)
            elif not room_group.groupmember_set.filter(uid_id=user.id).exists():
                raise Business_Error(detail="用户不在群中", code=0)
            return room_group
        else:
            raise Business_Error(detail="群聊不存在", code=0)

    @transaction.atomic
    def exit_group(self, user):
        room_group = self.validate_room_id(user)
        if room_group.groupmember_set.get(uid_id=user.id).role == GroupMember.Role.GROUP_LEADER:
            # 删除房间(room room_group,contact,group_member,message)
            room_group.room.delete()
        else:
            # 删除会话 删除群成员
            room_group.room.contact_set.filter(uid_id=user.id).delete()
            room_group.groupmember_set.filter(uid_id=user.id).delete()
            # 发送移除事件告知群成员
            member_uid_list = list(room_group.groupmember_set.all().values_list('uid_id', flat=True))

            send_delete_msg.send(sender=self.__class__, room_group=room_group, member_uid_list=member_uid_list,
                                 uid=user.id)


class AdminAddReq(Schema):
    roomId: int
    uidList: List[int] = Field(..., min_items=1, max_items=3)

    def validate_room_id(self, user):
        query = RoomGroup.objects.filter(room_id=self.roomId)
        if query.exists():
            room_group = query.get()
            if room_group.groupmember_set.get(uid_id=user.id).role != GroupMember.Role.GROUP_LEADER:
                raise Business_Error(detail="没有操作权限", code=0)
            elif len(
                room_group.groupmember_set.filter(uid_id__in=self.uidList).values_list('uid_id', flat=True)) != len(
                self.uidList):
                raise Business_Error(detail="用户不在群中", code=0)
            return room_group
        else:
            raise Business_Error(detail="群聊不存在", code=0)

    @transaction.atomic
    def add_admin(self, user):
        room_group = self.validate_room_id(user)
        if room_group.groupmember_set.filter(role=GroupMember.Role.ADMINISTRATOR).count() <= 5:
            for uid in self.uidList:
                room_group.groupmember_set.update_or_create(uid_id=uid, role=GroupMember.Role.ADMINISTRATOR)


class AdminRevokeReq(AdminAddReq):

    @transaction.atomic
    def revoke_admin(self, user):
        room_group = self.validate_room_id(user)

        room_group.groupmember_set.filter(uid_id__in=self.uidList).update(role=GroupMember.Role.ORDINARY_MEMBERS)


class MemberReq(ChatRoomCursorInputSchema):
    roomId: int

    def validate_room_id(self):
        query = RoomGroup.objects.filter(room_id=self.roomId)
        if query.exists():
            room_group = query.get()
            return room_group
        else:
            raise Business_Error(detail="群聊不存在", code=0)

    def get_member_page(self):
        room_group = self.validate_room_id()

        if room_group.room.is_hot_room():
            users_page = self.get_hot_room_users_page()
        else:
            users_page = self.get_normal_room_users_page(room_group)
        return users_page

    def get_cursor_pair(self):
        if self.cursor and self.cursor != '0':
            cursor_parts = self.cursor.split('_')
            is_online = int(cursor_parts[0])
            time_str = datetime.fromtimestamp(float(cursor_parts[1]), tz=timezone.utc)
            print(time_str)
            return is_online, time_str

    def get_hot_room_users_page(self):
        # 如果是首次查询
        if self.cursor == '0':
            users_page = self.get_hot_group_users_first_query()
        else:
            is_online, time_str = self.get_cursor_pair()
            users_page = self.get_hot_group_users_query(is_online, time_str)

        return users_page

    def get_normal_room_users_page(self, room_group):
        if self.cursor == '0':
            users_page = self.get_normal_group_users_first_query(room_group)
        else:
            is_online, time_str = self.get_cursor_pair()
            users_page = self.get_normal_group_users_query(room_group, is_online, time_str)
        return users_page

    def get_normal_group_users_first_query(self, room_group):
        subquery = room_group.groupmember_set.filter(uid__is_active=1).order_by('-uid__last_login').values(
            'uid__last_login')[:1]
        records = room_group.groupmember_set.filter(uid__last_login__lte=Subquery(subquery),
                                                    uid__is_active=1).order_by(
            '-uid__last_login')[:self.pageSize + 1].values('uid__id', 'uid__last_login', 'uid__is_active', 'role')

        records_list = list(records) if records.exists() else []
        if len(records) < self.pageSize + 1 and records_list[-1].get('uid__is_active') != 2:
            offline_records = room_group.groupmember_set.filter(
                uid__last_login__lte=records_list[-1].get('uid__last_login'),
                uid__is_active=2).order_by(
                '-uid__last_login')[
                              :self.pageSize - len(records) + 1].values('uid__id', 'uid__last_login', 'uid__is_active', 'role')
            records_list.extend(list(offline_records))
        return self.build_queryset(records_list, 'uid__is_active', 'uid__last_login')

    def get_normal_group_users_query(self, room_group, is_online, time_str):
        records = room_group.groupmember_set.filter(uid__last_login__lte=time_str,
                                                    uid__is_active=is_online).order_by('-uid__last_login')[
                  :self.pageSize + 1].values('uid__id', 'uid__last_login', 'uid__is_active', 'role')
        records_list = list(records) if records.exists() else []
        if len(records) < self.pageSize + 1 and is_online != 2:
            offline_records = room_group.groupmember_set.filter(uid__last_login__lte=time_str,
                                                                uid__is_active=2).order_by(
                '-uid__last_login')[
                              :self.pageSize - len(records) + 1].values('uid__id', 'uid__last_login', 'uid__is_active', 'role')
            records_list.extend(list(offline_records))
        return self.build_queryset(records_list, 'uid__is_active', 'uid__last_login')

    def get_hot_group_users_query(self, is_online, time_str):
        records = CustomUser.objects.filter(last_login__lte=time_str, is_active=is_online).order_by('-last_login')[
                  :self.pageSize + 1].values('last_login', 'is_active', 'id', 'is_superuser')
        records_list = list(records) if records.exists() else []
        if len(records) < self.pageSize + 1 and is_online != 2:
            offline_records = CustomUser.objects.filter(last_login__lte=time_str, is_active=2).order_by(
                '-last_login')[
                              :self.pageSize - len(records) + 1].values('last_login', 'is_active', 'id', 'is_superuser')
            records_list.extend(list(offline_records))
        return self.build_queryset(records_list, 'is_active', 'last_login')

    def get_hot_group_users_first_query(self):
        subquery = CustomUser.objects.filter(is_active=1).order_by('-last_login').values('last_login')[:1]
        records = CustomUser.objects.filter(last_login__lte=Subquery(subquery), is_active=1).order_by(
            '-last_login')[:self.pageSize + 1].values('last_login', 'is_active', 'id', 'is_superuser')
        records_list = list(records) if records.exists() else []
        records_list = list(records)
        if len(records) < self.pageSize + 1 and records_list[-1].get('is_active') != 2:
            offline_records = CustomUser.objects.filter(last_login__lte=records_list[-1].get('last_login'),
                                                        is_active=2).order_by(
                '-last_login')[
                              :self.pageSize - len(records) + 1].values('last_login', 'is_active', 'id', 'is_superuser')
            records_list.extend(list(offline_records))
        return self.build_queryset(records_list, 'is_active', 'last_login')

    def build_queryset(self, records, is_active, cursor_column='id'):

        # 计算下一页的游标
        next_cursor = str(records[-1].get(is_active)) + '_' + str(records[-1].get(cursor_column).timestamp()) if len(
            records) == self.pageSize + 1 else None
        # 是否最后一页判断
        isLast = len(records) != self.pageSize + 1
        return OrderedDict(
            [
                ("list", records[:self.pageSize]),
                ("isLast", isLast),
                ("cursor", next_cursor),
            ]
        )
