# _*_ coding: utf-8 _*_
from typing import List

from ninja_schema import Schema
from pydantic import Field


# @Author       :   <a href="https://github.com/afanzaimoyu">afan</a>
# @Time         :   2024/1/23
# @Description  :   None
class WSMsgMarkItem(Schema):
    uid: int = Field(..., description="操作者")
    msgId: int = Field(..., description="消息id")
    markType: int = Field(..., description="标记类型 1点赞 2举报")
    actType: int = Field(..., description="动作类型 1确认 2取消")
    markCount: int = Field(..., description="被标记的数量")


class WSMsgMark(Schema):
    markList: List[WSMsgMarkItem] = Field(..., description="标记列表")
