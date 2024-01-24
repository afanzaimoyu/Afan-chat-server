# _*_ coding: utf-8 _*_
from ninja_schema import Schema
from pydantic import Field


# @Author       :   <a href="https://github.com/afanzaimoyu">afan</a>
# @Time         :   2024/1/23
# @Description  :   None
class WSMessageRead(Schema):
    msgId: int = Field(..., description="消息id")
    readCount: int = Field(0, description="阅读人数（可能为0）")
