# _*_ coding: utf-8 _*_

# @Author       :   <a href="https://github.com/afanzaimoyu">afan</a>
# @Time         :   2024/1/23
# @Description  :   申请类型枚举
from django.db import models


class ItemTypeEnum(models.IntegerChoices):
    MODIFY_NAME_CARD = 1, "改名卡"
    BADGE = 2, "徽章"
