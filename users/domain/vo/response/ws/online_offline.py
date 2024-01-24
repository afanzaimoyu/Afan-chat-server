# _*_ coding: utf-8 _*_
from typing import List

from ninja_schema import Schema

from users.domain.vo.response.ws.chat_member_resp import ChatMemberResp


# @Author       :   <a href="https://github.com/afanzaimoyu">afan</a>
# @Time         :   2024/1/23
# @Description  :   用户上下线变动的推送类
class WSOnlineOfflineNotify(Schema):
    changeList: List[ChatMemberResp] = []
    onlineNum: int
