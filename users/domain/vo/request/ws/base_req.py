# _*_ coding: utf-8 _*_
from typing import Optional, TypeVar

from ninja_schema import Schema
from pydantic import Field

# @Author       :   <a href="https://github.com/afanzaimoyu">afan</a>
# @Time         :   2024/1/23
# @Description  :   websocket前端请求体
T = TypeVar('T')


class WSBaseReq(Schema):
    type: int = Field(..., description="请求类型 1.请求登录二维码，2心跳检测")
    data: Optional[T] = Field(None, description="每个请求包具体的数据，类型不同结果不同")
