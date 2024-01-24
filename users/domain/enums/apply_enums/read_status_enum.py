# _*_ coding: utf-8 _*_

# @Author       :   <a href="https://github.com/afanzaimoyu">afan</a>
# @Time         :   2024/1/23
# @Description  :   申请阅读状态枚举
from django.db import models


class ApplyReadStatusEnum  (models.IntegerChoices):
    """
    申请阅读状态枚举
    """
    UNREAD = 1, "未读"
    READ = 2, "已读"
