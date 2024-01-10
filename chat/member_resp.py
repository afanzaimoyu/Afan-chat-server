from datetime import datetime

from ninja_schema import Schema
from pydantic import Field


class MemberResp(Schema):
    roomId: int = Field(..., description="房间id")
    groupName: str = Field(..., description="群名称")
    avatar: str = Field(..., description="群头像")
    onlineNum: int = Field(..., description="在线人数")
    role: int = Field(..., description="成员角色 1群主 2管理员 3普通成员 4踢出群聊")


class ChatMemberListResp(Schema):
    uid: int = Field(alias='uid__id')
    name: str = Field(alias='uid__name')
    avatar: str = Field(alias='uid__avatar')


class IdResp(Schema):
    id: int

class WSMemberChange(Schema):
    roomId: int
    uid: int = Field(..., description="变动的uid")
    changeType: int = Field(..., description="变动类型1.加入2.移除")
    activeStatus: int = Field(..., description="在线状态1.在线2.离线")
    lastOptTime: datetime
