# _*_ coding: utf-8 _*_

# @Author       :   flz
# @Time         :   2024/1/23
# @Description  :   ws的基本返回信息体
from typing import Optional, TypeVar

from ninja_schema import Schema

T = TypeVar("T")


class WSBaseResp(Schema):
    """
    ws推送给前端的消息
    See Also: resp_type_enum.py
    """
    type: int = None
    data: Optional[T] = None
