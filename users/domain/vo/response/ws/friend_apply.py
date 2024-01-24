# _*_ coding: utf-8 _*_
from ninja_schema import Schema
from pydantic import Field


# @Author       :   <a href="https://github.com/afanzaimoyu">afan</a>
# @Time         :   2024/1/23
# @Description  :   None
class WSFriendApply(Schema):
    uid: int = Field(..., description="申请人")
    unreadCount: int = Field(..., description="申请未读数")
