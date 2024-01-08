from collections import OrderedDict
from datetime import datetime
from typing import Optional, List, TypeVar, Any

from django.db.models import Q
from ninja_schema import Schema
from pydantic import Field

from chat.models import Room, Contact, Message
from chat.msg_schema.abs_msg_handler import AbstractMsgHandler
from chat.msg_schema.msg_handler_factory import MsgHandlerFactory
from users.models import CustomUser

T = TypeVar("T")


class ChatRoomRespSchema(Schema):
    roomId: int = Field(None, description="房间id")
    type: int = Field(None, description="房间类型 1群聊 2单聊", ge=1, le=2)
    hot_Flag: int = Field(None, description="是否全员展示的会话 0否 1是", ge=0, le=1)
    text: str = Field(None, description="最新消息")
    activeTime: datetime = Field(None, description="房间最后活跃时间(用来排序)")
    name: str = Field(None, description="会话名称")
    avatar: str = Field(None, description="会话头像")
    unreadCount: int = Field(None, description="未读数")


class RoomBaseInfo(Schema):
    roomId: int = Field(None, description="房间id")
    name: str = Field(None, description="会话名称")
    avatar: str = Field(None, description="会话头像")
    type: int = Field(None, description="房间类型 1群聊 2单聊", ge=1, le=2)
    hot_Flag: int = Field(None, description="是否全员展示的会话 0否 1是", ge=0, le=1)
    activeTime: datetime = Field(None, description="房间最后活跃时间(用来排序)")
    lastMsgId: int = Field(None, description="最后一条消息id")


class PageSizeOutputBase(Schema):
    cursor: Optional[str] = None
    is_last: bool = True
    list: List[T] = None


class ChatRoomCursorInputSchema(Schema):
    cursor: Optional[int] = 0
    pagesize: int = Field(..., lt=200)

    def paginate_queryset(self, queryset=None):

        if queryset.exists():
            # 获取实际返回的记录
            records = list(queryset[:self.pagesize + 1])

            # 取出前 n 条记录供展示
            display_records = records[:self.pagesize]

            # 计算下一页的游标
            next_cursor = str(getattr(records[-1], self.cursor_column)) if len(records) == self.pagesize + 1 else None

            # 是否最后一页判断
            is_last = len(records) != self.pagesize + 1
            return OrderedDict(
                [
                    ("list", display_records),
                    ("is_last", is_last),
                    ("cursor", next_cursor),
                ]
            )

    def get_contact_page(self, user):
        # 查出用户要展示的会话列表
        if user.id:
            # 用户基础会话
            user = CustomUser.objects.get(id=5)
            queryset = user.chat_contact_user.filter(id__gt=self.cursor).order_by("active_time")[:self.pagesize + 1]
            contact_page = self.paginate_queryset(queryset)

            base_room = [contact.room for contact in contact_page.get('list')] if contact_page else []

            # 热门房间
            q2 = Room.objects.filter(id__gt=self.cursor, id__lt=self.pagesize, hot_flag=Room.HotFlag.YES).order_by(
                "active_time")
            hot_room_page = self.paginate_queryset(q2)

            base_room.append(hot_room_page)
            # 基础会话和热门房间合并
            if contact_page:
                contact_page['list'] = base_room
            else:
                contact_page = hot_room_page
            page = PageSizeOutputBase(**contact_page)

        else:
            # 未登录的用户，只能查看全局房间
            queryset = Room.objects.filter(id__gt=self.cursor, hot_flag=Room.HotFlag.YES).order_by("active_time")[
                       :self.pagesize + 1]
            room_cursor_page = self.paginate_queryset(queryset)
            page = PageSizeOutputBase(**room_cursor_page)
        if page.list:
            # 最后组装会话信息（名称，头像，未读数等）
            result = self.build_contact_resp(user, page.list)
            page.list = result
        return page

    def build_contact_resp(self, user, rooms: List[Any]):
        result = list()
        # 表情和头像
        room_base_info_list = self.get_room_base_info_list(rooms, user)

        # 最后一条消息
        # 消息未读数
        room_ids = [room_base_info.roomId for room_base_info in room_base_info_list]
        un_read_count_map = self.get_un_read_count_map(user, room_ids)

        for room_base_info in room_base_info_list:
            resp = ChatRoomRespSchema(
                **room_base_info.dict(exclude='lastMsgId')
            )
            message = Message.objects.get(id=room_base_info.lastMsgId)
            if message:
                msgHandler: AbstractMsgHandler = MsgHandlerFactory.get_strategy_no_null(message.type)()
                resp.text = f'{message.from_user.name}:{msgHandler.show_contact_msg(message)}'
            resp.unreadCount = un_read_count_map.get(room_base_info.roomId, 0)
            result.append(resp)

        if result:
            sorted(result, key=lambda x: x.activeTime, reverse=True)
        return result

    @staticmethod
    def get_un_read_count_map(user, room_ids):
        resp = dict()
        if not user.id:
            return resp
        contacts = list(user.chat_contact_user.filter(room_id__in=room_ids))
        for contact in contacts:
            resp.update({
                contact.room_id: contact.room.message_set.filter(create_time__gt=contact.read_time).count()
            })
        return resp

    @staticmethod
    def get_room_base_info_list(rooms: List[Any], user):
        result = []
        # 根据好友和群组进行分组
        for room in rooms:
            room_base_info = RoomBaseInfo(
                roomId=room.id,
                type=room.type,
                hot_Flag=room.hot_flag,
                lastMsgId=room.last_msg_id,
                activeTime=room.active_time
            )
            if room.is_room_group():
                room_base_info.name = room.roomgroup.name
                room_base_info.avatar = room.roomgroup.avatar
            elif room.is_room_friend():
                room_base_info.name = room.roomfriend.get_friend(user.id).name
                room_base_info.avatar = room.roomfriend.get_friend(user.id).avatar
            result.append(room_base_info)
        return result
