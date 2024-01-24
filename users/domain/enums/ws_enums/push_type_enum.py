# _*_ coding: utf-8 _*_

# @Author       :   <a href="https://github.com/afanzaimoyu">afan</a>
# @Time         :   2024/1/23
# @Description  :

from django.db import models


class WSPushTypeEnum(models.IntegerChoices):
    USER = 1, "个人"
    ALL = 2, "全部连接用户"
