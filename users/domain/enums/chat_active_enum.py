# _*_ coding: utf-8 _*_

# @Author       :   <a href="https://github.com/afanzaimoyu">afan</a>
# @Time         :   2024/1/23
# @Description  :   在线状态枚举
from django.db import models


class ChatActiveEnum(models.IntegerChoices):
    ONLINE = 1, "在线"
    OFFLINE = 2, "离线"
