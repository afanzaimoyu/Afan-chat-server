# _*_ coding: utf-8 _*_

# @Author       :   <a href="https://github.com/afanzaimoyu">afan</a>
# @Time         :   2024/1/23
# @Description  :   黑名单类型枚举
from django.db import models


class BlackTypeEnum(models.IntegerChoices):
    IP = 1
    UID = 2
