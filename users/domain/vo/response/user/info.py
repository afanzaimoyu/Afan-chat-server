# _*_ coding: utf-8 _*_
from ninja_schema import Schema


# @Author       :   <a href="https://github.com/afanzaimoyu">afan</a>
# @Time         :   2024/1/23
# @Description  :   None
class UserInfoResp (Schema):
    id: int
    name: str
    avatar: str
    sex: str
    modifyNameChance: int = 0