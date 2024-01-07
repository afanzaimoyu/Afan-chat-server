from datetime import datetime
from typing import Dict, List, Any, Optional

from django.forms import model_to_dict
from ninja_extra.schemas.response import Url
from ninja_schema import Schema

from pydantic import Field, model_validator as pydantic_model_validator


class UserInfo(Schema):
    uid: int = Field(..., alias="from_user", description="用户id")


class MessageMark(Schema):
    likeCount: int = Field(0, description="点赞数")
    userLike: int = Field(0, description="该用户是否已经点赞 0否 1是")
    dislikeCount: int = Field(0, description="举报数")
    userDislike: int = Field(0, description="该用户是否已经举报 0否 1是")


class MessageInfo(Schema):
    id: int = Field(..., description="消息id")
    roomId: int = Field(..., alias="room", description="房间id")
    sendTime: datetime = Field(..., description="消息发送时间")
    type: int = Field(..., description="消息类型 1正常文本 2.撤回消息")
    body: Dict = Field(..., description="消息内容不同的消息类型")
    messageMark: MessageMark = Field(MessageMark(), description="消息标记")


class ChatMessageRespSchema(Schema):
    fromUser: UserInfo = Field(..., description="发送者信息")
    message: MessageInfo = Field(..., description="消息详情")

    @pydantic_model_validator(mode="before")
    def assemble_resp(cls, values):
        print(values)
        message_dict = {}
        if not isinstance(values, dict):
            message_dict: dict = model_to_dict(values)
        message_dict["sendTime"] = values.create_time
        message_dict.update({"body": message_dict.get("extra")})
        if message_dict.get("content"):
            message_dict["body"]["content"] = message_dict.get("content")

        return dict(fromUser=UserInfo(**message_dict), message=message_dict)


class ChatMsgRecallRespSchema(Schema):
    msgId: int = Field(..., alias="id")
    roomId: int = Field(..., alias="room_id")
    recallUid: int = Field(..., description="撤回的用户")

    @pydantic_model_validator(mode="before")
    def assemble_resp(cls, values):
        from chat.chat_schema import MsgRecall
        extra = MsgRecall(**values.extra["recall"]).dict(exclude="recallTime")
        for k, v in extra.items():
            setattr(values, k, v)
        return values


class ReplyMsg(Schema):
    id: int = Field(None, description="消息id")
    uid: int = Field(None, description="用户uid")
    username: str = Field(None, description="用户名称")
    type: int = Field(None, description="消息类型 1正常文本 2.撤回消息")
    body: Any = None
    canCallback: int = Field(None, description="是否可消息跳转 0否 1是")
    gapCount: int = Field(None, description="跳转间隔的消息条数")


class TextMsgRespSchema(Schema):
    content: str = Field(..., description="消息内容")
    urlContentMap: Dict = Field({}, description="消息链接映射")
    atUidList: Optional[List[int]] = None
    reply: Optional[ReplyMsg] = Field(None, description="父消息，如果没有父消息，返回的是null")
