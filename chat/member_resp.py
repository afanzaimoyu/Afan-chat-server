from datetime import datetime
from typing import List, Optional

from ninja_schema import Schema
from pydantic import Field

from chat.chat_room_resp import PageSizeOutputBase
from pydantic import Field, model_validator as pydantic_model_validator


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
    roomId: Optional[int]
    uid: Optional[int] = Field(..., description="变动的uid")
    changeType: Optional[int] = Field(..., description="变动类型1.加入2.移除")
    activeStatus: Optional[int] = Field(..., description="在线状态1.在线2.离线")
    lastOptTime: Optional[datetime]


class ChatMemberRespBase(Schema):
    uid: int = Field(alias="id")
    activeStatus: int = Field(alias="is_active")
    lastOptTime: str = Field(alias="last_login")
    roleId: int = Field(alias="role")

    @pydantic_model_validator(mode="before")
    def extract_name(cls, values: dict):
        new_data = {}
        for key, value in values.items():
            if isinstance(value, datetime):
                new_data[key.replace('uid__', '')] = str(value.timestamp())
            elif key == 'is_superuser':
                new_data['role'] = value if value else 3
            else:
                new_data[key.replace('uid__', '')] = value
        return new_data


class ChatMemberResp(PageSizeOutputBase):
    list: List[ChatMemberRespBase] = None
