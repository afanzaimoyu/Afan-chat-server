# _*_ coding: utf-8 _*_
from ninja_schema import Schema
from pydantic import Field


# @Author       :   <a href="https://github.com/afanzaimoyu">afan</a>
# @Time         :   2024/1/23
# @Description  :   表情包反参
class UserEmojiResp(Schema):
    id: int = Field(..., description="表情id")
    expressionUrl: str = Field(..., alias="expression_url", description="表情链接")

