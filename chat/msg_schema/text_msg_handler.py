from typing import Optional, List

from ninja_extra.exceptions import NotFound
from ninja_extra.shortcuts import get_object_or_exception
from ninja_schema import Schema
from pydantic import ValidationError

from chat.chat_message_resp import TextMsgRespSchema, ReplyMsg
from chat.chat_schema import TextMsgBody, MessageExtra
from chat.models import Message
from chat.msg_schema.abs_msg_handler import AbstractMsgHandler
from chat.msg_schema.msg_handler_factory import MsgHandlerFactory
from users.exceptions.chat import Business_Error
from users.models import CustomUser


class TextMsgHandler(AbstractMsgHandler):
    """文本消息处理器"""

    def __init__(self):
        self.req_schema = TextMsgBody

    @staticmethod
    def get_msg_type_enum():
        return Message.MessageTypeEnum.TEXT

    def check_msg(self, body: dict, room_id: str, uid: int):
        try:
            req = self.req_schema(**body)
        except ValidationError as e:
            loc = ','.join(exc.get("loc")[0] for exc in e.errors())
            raise Business_Error(detail=f"{loc} 参数校验错误", code=-2)
        # 回复消息校验
        if req.replyMsgId:
            reply_msg = get_object_or_exception(klass=Message, error_message="回复消息不存在",
                                                exception=NotFound, pk=req.replyMsgId)
            if not reply_msg.room_id == room_id:
                raise Business_Error(detail=f"只能回复相同会话内的内容", code=-2)
        return req

    def save_msg(self, message: Message.objects, body: TextMsgBody):
        extra = MessageExtra()
        message.content = body.content
        message.extra = extra.dict(exclude_none=True)

        #  如果有回复消息
        if body.replyMsgId:
            gap_count = message.get_GapCount(body.replyMsgId)
            message.gap_count = gap_count
            message.reply_msg_id = body.replyMsgId
        # TODO:
        #  2.判断消息url跳转
        #  3.艾特功能
        message.save()

    def show_msg(self, msg):

        content = msg.content
        at_uid_list = msg.extra.get("atUidList") if msg.extra else None
        url_count_map = msg.extra.get("urlContentMap") if msg.extra else None
        resp = TextMsgRespSchema(content=content, atUidList=at_uid_list, urlContentMap=url_count_map)
        # TODO: 回复消息
        reply = Message.objects.filter(id=msg.reply_msg_id, status=Message.Status.NORMAL) if msg.reply_msg_id else None
        if reply and reply.exists():
            reply_message = reply.get()
            reply_message_vo = ReplyMsg()
            reply_message_vo.id = reply_message.id
            reply_message_vo.uid = reply_message.from_user_id
            reply_message_vo.type = reply_message.type
            reply_message_vo.body = MsgHandlerFactory.get_strategy_no_null(reply_message.type).show_reply_msg(
                reply_message)
            reply_user = reply_message.from_user
            reply_message_vo.username = reply_user.name
            reply_message_vo.canCallback = msg.gap_count and msg.gap_count < 100
            reply_message_vo.gapCount = msg.gap_count
            resp.reply = reply_message_vo
        return resp

    @staticmethod
    def show_reply_msg(msg):
        return msg.content

    def show_contact_msg(self, msg):
        return msg.content
