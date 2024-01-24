# _*_ coding: utf-8 _*_
from datetime import datetime
from typing import List

from ninja_schema import Schema
from pydantic import Field, model_validator
from users.user_tools.tools import datetime_to_timestamp


# @Author       :   <a href="https://github.com/afanzaimoyu">afan</a>
# @Time         :   2024/1/23
# @Description  :   群成员列表的成员信息
class ChatMemberResp(Schema):
    uid: int = Field(alias="id")
    activeStatus: int = Field(alias="is_active")
    lastOptTime: int = Field(alias="last_login")

    @model_validator(mode="before")
    def extract_name(cls, values):
        values.last_login = datetime_to_timestamp(values.last_login)
        return values

