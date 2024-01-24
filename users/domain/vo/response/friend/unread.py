# _*_ coding: utf-8 _*_
from ninja_schema import Schema


# @Author       :   <a href="https://github.com/afanzaimoyu">afan</a>
# @Time         :   2024/1/23
# @Description  :   申请列表的未读数
class FriendUnreadResp(Schema):
    unReadCount: int
