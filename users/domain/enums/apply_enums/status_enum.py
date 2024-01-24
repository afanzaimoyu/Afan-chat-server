# _*_ coding: utf-8 _*_

# @Author       :   <a href="https://github.com/afanzaimoyu">afan</a>
# @Time         :   2024/1/23
# @Description  :   申请阅读状态枚举
from django.db import models


class ApplyStatusEnum (models.IntegerChoices):
    """
    申请状态枚举
    """
    WAIT_APPROVAL = 1, "待审批"
    AGREE = 2, "同意"
