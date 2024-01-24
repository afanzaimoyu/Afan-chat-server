# _*_ coding: utf-8 _*_
from datetime import datetime
from typing import Optional

from ninja_schema import Schema
from pydantic import Field


# @Author       :   <a href="https://github.com/afanzaimoyu">afan</a>
# @Time         :   2024/1/23
# @Description  :   None
class WSMemberChange(Schema):
    roomId: Optional[int]
    uid: Optional[int] = Field(..., description="变动的uid")
    changeType: Optional[int] = Field(..., description="变动类型1.加入2.移除")
    activeStatus: Optional[int] = Field(..., description="在线状态1.在线2.离线")
    lastOptTime: Optional[datetime]
