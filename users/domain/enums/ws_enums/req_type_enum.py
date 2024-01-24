# _*_ coding: utf-8 _*_

# @Author       :   <a href="https://github.com/afanzaimoyu">afan</a>
# @Time         :   2024/1/23
# @Description  :   ws前端请求类型枚举
from django.db import models


class WSReqTypeEnum(models.IntegerChoices):
    LOGIN = 1, "登录"
    HEARTBEAT = 2, "心跳"
    AUTHORIZE = 3, "授权"
