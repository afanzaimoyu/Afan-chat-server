# _*_ coding: utf-8 _*_
from ninja_schema import Schema
from pydantic import Field


# @Author       :   <a href="https://github.com/afanzaimoyu">afan</a>
# @Time         :   2024/1/23
# @Description  :   徽章信息
class BadgeResp(Schema):
    id: int
    img: str
    describe: str
    obtain: int = Field(..., description="是否拥有 0否 1是")
    wearing: int = Field(..., description="是否佩戴 0否 1是")
