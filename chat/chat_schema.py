from datetime import datetime
from typing import Dict, Any, Generic, List, TypeVar, Optional

from django.core.cache import cache
from django.db import transaction
from ninja_extra import service_resolver
from ninja_extra.controllers import RouteContext
from ninja_extra.schemas.response import Url, T
from ninja_schema import model_validator, Schema
from pydantic import Field

from chat.models import *
from chat.msg_schema.abs_msg_handler import AbstractMsgHandler
from chat.msg_schema.msg_handler_factory import MsgHandlerFactory
from users.exceptions.chat import Business_Error


class MessageBase(Schema):
    @transaction.atomic
    def save_msg(self, uid):
        insert = Message.objects.create(from_user_id=uid, room_id=self.roomId, status=Message.Status.NORMAL)
        return insert


class MessageInput(MessageBase):
    """
    Args:
    - **roomId** 房间id
    - **msgType** 消息类型
    - **body** 消息内容 ，消息不同传值不同
    """
    roomId: int = Field(..., description="房间id")
    msgType: int
    body: Dict[str, Any]

    @model_validator("roomId")
    def validate_uid(cls, value_data):
        context: RouteContext = service_resolver(RouteContext)
        user = context.request.user

        # room = cache.get(value_data)
        room = Room.objects.filter(id=value_data).first()
        # 全员群聊
        if room.is_hot_room():
            return value_data

        if room.is_room_friend():
            room_friend = room.roomfriend
            if room_friend.status == RoomFriend.Status.DISABLE:
                raise Business_Error(detail="您已经被对方拉黑", code=0)
            if user.id not in (room_friend.uid1_id, room_friend.uid2_id):
                raise Business_Error(detail="您已经被对方拉黑", code=0)

        if room.is_room_group():
            if not room.roomgroup.groupmember_set.filter(uid=user.id).exists():
                raise Business_Error(detail="您已经被移除该群", code=0)

        return value_data

    def send_msg(self, user):
        # 找到相对于的策略类 s
        # s.checkMsg
        # s
        msgHandler: AbstractMsgHandler = MsgHandlerFactory.get_strategy_no_null(self.msgType)()
        msgHandler.check_and_save_msg(self, user.id)

        # 发布消息发送事件


class TextMsgBody(MessageBase):
    content: str
    replyMsgId: int = None
    atUidList: List = None


class MsgRecall(Schema):
    """
    撤回消息的uid
    撤回的时间点
    """
    recallUid: int
    recallTime: datetime


class BaseFileSchema(Schema):
    """
    Args:
    - **size** 大小（字节）
    - **url** 下载地址
    """
    size: int
    url: Url


class FileMsgSchema(BaseFileSchema):
    """
    文件名（带后缀）
    """
    fileName: str


class ImgMsgSchema(BaseFileSchema):
    """
    宽度（像素）
    高度（像素）
    """
    width: int
    height: int


class SoundMsgSchema(BaseFileSchema):
    """
    时长（秒）
    """
    second: int


class VideoMsgSchema(BaseFileSchema):
    """
    缩略图宽度（像素）
    缩略图高度（像素）
    缩略图大小（字节）
    缩略图下载地址
    """
    thumbWidth: int
    thumbHeight: int
    thumbSize: int
    thumbUrl: str


class EmojisMsgSchema(Schema):
    """
    Args:
    - **url** 下载地址
    """
    url: Url


class MessageExtra(MessageBase):
    """
    url跳转链接
    消息撤回详情
    艾特的uid
    文件消息
    图片消息
    语音消息
    文件消息
    表情图片信息
    """
    urlContentMap: Dict[str, Url] = {}
    recall: MsgRecall = None
    atUidList: List[int] = None
    fileMsg: FileMsgSchema = None
    imgMsg: ImgMsgSchema = None
    soundMsg: SoundMsgSchema = None
    videoMsg: VideoMsgSchema = None
    emojisMsg: EmojisMsgSchema = None
