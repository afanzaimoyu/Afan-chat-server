from collections import OrderedDict
from datetime import datetime
from typing import Optional, List, TypeVar, Any, Union

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
    activeTime: Optional[int] = Field(None, description="房间最后活跃时间(用来排序)")
    name: Optional[str] = Field(None, description="会话名称")
    avatar: Optional[str] = Field(None, description="会话头像")
    unreadCount: int = Field(None, description="未读数")


class RoomBaseInfo(Schema):
    roomId: int = Field(None, description="房间id")
    name: str = Field(None, description="会话名称")
    avatar: str = Field(None, description="会话头像")
    type: int = Field(None, description="房间类型 1群聊 2单聊", ge=1, le=2)
    hot_Flag: Optional[int] = Field(0, description="是否全员展示的会话 0否 1是", ge=0, le=1)
    activeTime: Optional[int] = Field(None, description="房间最后活跃时间(用来排序)")
    lastMsgId: Optional[int] = Field(None, description="最后一条消息id")


class PageSizeOutputBase(Schema):
    cursor: Union[Optional[str], Optional[int]] = None
    isLast: bool = True
    list: List[T] = None


class ChatRoomCursorInputSchema(Schema):
    cursor: Union[Optional[str], Optional[int]] = 0
    pageSize: int = Field(..., lt=200)

    def paginate_queryset(self, queryset=None, cursor_column='id'):

        if queryset.exists():
            # 获取实际返回的记录
            records = list(queryset[:self.pageSize + 1])

            # 取出前 n 条记录供展示
            display_records = records[:self.pageSize]

            # 计算下一页的游标
            next_cursor = str(getattr(records[-1], cursor_column)) if len(records) == self.pageSize + 1 else None

            # 是否最后一页判断
            isLast = len(records) != self.pageSize + 1
            return OrderedDict(
                [
                    ("list", display_records),
                    ("isLast", isLast),
                    ("cursor", next_cursor),
                ]
            )

    def get_contact_page(self, user):
        # 查出用户要展示的会话列表
        if user.id:
            # 用户基础会话
            queryset = user.chat_contact_user.filter(id__gte=self.cursor).order_by("-active_time")[:self.pageSize + 1]
            contact_page = self.paginate_queryset(queryset)
            contact_page = contact_page if contact_page else {}

            base_room = [contact.room for contact in contact_page.get('list')] if contact_page != {} else []

            # 热门房间
            q2 = Room.objects.filter(id__gte=self.cursor, id__lte=self.pageSize, hot_flag=Room.HotFlag.YES).order_by(
                "-active_time")
            hot_room_page = self.paginate_queryset(q2)

            base_room = base_room + hot_room_page.get('list', [])
            # 基础会话和热门房间合并
            # if contact_page:
            #     contact_page['list'] = base_room
            # else:
            #     contact_page = hot_room_page
            all_contact_page = dict(
                list=base_room,
                isLast=contact_page.get('isLast', True) and hot_room_page.get('isLast', True),
                cursor=max(contact_page.get('cursor', 0), hot_room_page.get('cursor', 0))
                if contact_page.get('cursor') and hot_room_page.get('cursor') else None
            )

            page = PageSizeOutputBase(**all_contact_page)

        else:
            # 未登录的用户，只能查看全局房间
            queryset = Room.objects.filter(id__gte=self.cursor, hot_flag=Room.HotFlag.YES).order_by("-active_time")[
                       :self.pageSize + 1]
            room_cursor_page = self.paginate_queryset(queryset)
            page = PageSizeOutputBase(**room_cursor_page)
        if page.list:
            # 最后组装会话信息（名称，头像，未读数等）
            result = self.build_contact_resp(user, page.list)
            page.list = result
        return page

    @classmethod
    def build_contact_resp(cls, user, rooms: List[Any]):
        result = list()
        # 表情和头像
        room_base_info_list = cls.get_room_base_info_list(rooms, user)

        # 最后一条消息
        # 消息未读数
        room_ids = [room_base_info.roomId for room_base_info in room_base_info_list]
        un_read_count_map = cls.get_un_read_count_map(user, room_ids)

        for room_base_info in room_base_info_list:
            resp = ChatRoomRespSchema(
                **room_base_info.dict(exclude='lastMsgId')
            )
            message = Message.objects.get(id=room_base_info.lastMsgId) if room_base_info.lastMsgId else None
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
            if contact and contact.read_time:
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
                activeTime=int(datetime.timestamp(room.active_time)) if room.active_time else None
            )
            if room.is_room_group():
                room_base_info.name = room.roomgroup.name
                room_base_info.avatar = room.roomgroup.avatar
            elif room.is_room_friend():
                friend = room.roomfriend.get_friend(user.id)
                if friend:
                    room_base_info.name = friend.name
                    room_base_info.avatar = friend.avatar
            result.append(room_base_info)
        return result
