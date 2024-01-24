# _*_ coding: utf-8 _*_

# @Author       :   <a href="https://github.com/afanzaimoyu">afan</a>
# @Time         :   2024/1/23
# @Description  :   申请类型枚举
from django.db import models


class ApplyTypeEnum(models.IntegerChoices):
    ADD_FRIEND = 1, "加好友"
