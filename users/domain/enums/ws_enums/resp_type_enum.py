# _*_ coding: utf-8 _*_

# @Author       :   flz
# @Time         :   2024/1/23
# @Description  :    ws前端请求类型枚举
from enum import Enum
from typing import Type

from users.domain.vo.response.ws.black import WSBlack
from users.domain.vo.response.ws.friend_apply import WSFriendApply
from users.domain.vo.response.ws.login_success import WSLoginSuccess
from users.domain.vo.response.ws.login_url import WSLoginUrl
from users.domain.vo.response.ws.member_change import WSMemberChange
from users.domain.vo.response.ws.message import WSMessage
from users.domain.vo.response.ws.message_mark import WSMsgMark
from users.domain.vo.response.ws.msg_recall import WSMsgRecall
from users.domain.vo.response.ws.online_offline import WSOnlineOfflineNotify


class WSRespTypeEnum(Enum):
    LOGIN_URL = (1, "登录二维码返回", WSLoginUrl)
    LOGIN_SCAN_SUCCESS = (2, "用户扫描成功等待授权", None)
    LOGIN_SUCCESS = (3, "用户登录成功返回用户信息", WSLoginSuccess)
    MESSAGE = (4, "新消息", WSMessage)
    ONLINE_OFFLINE_NOTIFY = (5, "上下线通知", WSOnlineOfflineNotify)
    INVALIDATE_TOKEN = (6, "使前端的token失效，意味着前端需要重新登录", None)
    BLACK = (7, "拉黑用户", WSBlack)
    MARK = (8, "消息标记", WSMsgMark)
    RECALL = (9, "消息撤回", WSMsgRecall)
    APPLY = (10, "好友申请", WSFriendApply)
    MEMBER_CHANGE = (11, "成员变动", WSMemberChange)

    def __init__(self, enum_type: int, desc: str, data_class: Type):
        self.enum_type = enum_type
        self.desc = desc
        self.data_class = data_class
