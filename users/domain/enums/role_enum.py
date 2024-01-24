# _*_ coding: utf-8 _*_

# @Author       :   <a href="https://github.com/afanzaimoyu">afan</a>
# @Time         :   2024/1/23
# @Description  :   角色枚举
from django.db import models


class RoleEnum(models.IntegerChoices):
    ADMIN = 1, "超级管理员"
    CHAT_MANAGER = 2, "群聊管理"
