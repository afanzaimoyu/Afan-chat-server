# _*_ coding: utf-8 _*_
from ninja_schema import Schema
from pydantic import Field


# @Author       :   <a href="https://github.com/afanzaimoyu">afan</a>
# @Time         :   2024/1/23
# @Description  :   好友校验

class FriendCheck(Schema):
    uid: int
    isFriend: bool


class FriendCheckResp(Schema):
    checkedList: list[FriendCheck]
