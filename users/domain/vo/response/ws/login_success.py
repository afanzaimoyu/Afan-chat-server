# _*_ coding: utf-8 _*_
from ninja_schema import Schema
from pydantic import Field, model_validator

from users.user_tools.tools import get_token


# @Author       :   <a href="https://github.com/afanzaimoyu">afan</a>
# @Time         :   2024/1/23
# @Description  :   None
class WSLoginSuccess(Schema):
    uid: int = Field(alias='id')
    avatar: str
    token: str
    name: str
    power: int = Field(..., description="用户权限 0普通用户 1超管", ge=0, le=1)

    @model_validator(mode="before")
    def build_other_info(cls, values):
        user_token = get_token(values)
        values.token = user_token.get("access")
        # 判断用户是否是管理员或群聊管理员
        values.power = 1 if values.groups.filter(name__in=['超级管理员', '群聊管理员']).exists() else 0

        return values
