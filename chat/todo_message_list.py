from collections import OrderedDict
from typing import Union, Optional

from django.db.models import Q
from ninja_schema import Schema
from pydantic import Field

from chat.chat_message_resp import ChatMessageRespSchema
from chat.models import Message
from chat.msg_schema.abs_msg_handler import AbstractMsgHandler
from chat.msg_schema.msg_handler_factory import MsgHandlerFactory


class MessagePageInput(Schema):
    cursor: Union[Optional[int], Optional[str]] = 0
    pageSize: int = Field(100, lt=200)
    roomId: int

    def paginate_queryset(self):
        if not self.cursor:
            queryset = Message.objects.filter(
                Q(room_id=self.roomId) & ~Q(type=Message.MessageTypeEnum.RECALL)).order_by(
                '-create_time')[:self.pageSize + 1]
        else:
            queryset = Message.objects.filter(
                Q(room_id=self.roomId, pk__lte=self.cursor) & ~Q(type=Message.MessageTypeEnum.RECALL)).order_by(
                '-create_time')[:self.pageSize + 1]
        print(queryset.query)
        if queryset:
            # 获取实际返回的记录
            records = list(queryset[:self.pageSize + 1])

            # 取出前 n 条记录供展示
            display_records = records[:self.pageSize]

            # 计算下一页的游标
            next_cursor = str(getattr(records[-1], 'id')) if len(records) == self.pageSize + 1 else None

            # 是否最后一页判断
            isLast = len(records) != self.pageSize + 1
            return OrderedDict(
                [
                    ("list", reversed(display_records)),
                    ("isLast", isLast),
                    ("cursor", next_cursor),
                ]
            )

    def get_resp(self):
        resp = self.paginate_queryset()
        resp_list = []
        for message in resp.get('list', []):
            if not message:
                continue
            msgHandler: AbstractMsgHandler = MsgHandlerFactory.get_strategy_no_null(message.type)()
            body = msgHandler.show_msg(message)
            resp_list.append(ChatMessageRespSchema.get_resp(body, message).dict(exclude_none=True))
        resp['list'] = resp_list
        return resp
