from typing import Optional, List

from ninja_schema import Schema
from pydantic import ValidationError

from chat.chat_schema import TextMsgBody, MessageExtra
from chat.models import Message
from chat.msg_schema.abs_msg_handler import AbstractMsgHandler, MessageTypeEnum
from users.exceptions.chat import Business_Error


class TextMsgHandler(AbstractMsgHandler):
    """文本消息处理器"""

    def __init__(self):
        self.req_schema = TextMsgBody

    @staticmethod
    def get_msg_type_enum():
        return MessageTypeEnum.TEXT

    def check_msg(self, body: dict, room_id: str, uid: int):
        try:
            return self.req_schema(**body)
        except ValidationError as e:
            loc = ','.join(exc.get("loc")[0] for exc in e.errors())
            raise Business_Error(detail=f"{loc} 参数校验错误", code=-2)

    def save_msg(self, message: Message.objects, body: TextMsgBody):
        extra = MessageExtra()
        message.content = body.content
        message.extra = extra.dict(exclude_none=True)
        message.save()
        # TODO:
        #  1. 如果有回复消息
        #  2.判断消息url跳转
        #  3.艾特功能

    def show_msg(self, msg):
        # TODO: 回复消息
        pass

    def show_reply_msg(self, msg):
        return msg.content

    def show_contact_msg(self, msg):
        return msg.content
