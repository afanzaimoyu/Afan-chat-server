# _*_ coding: utf-8 _*_
from enum import Enum


# @Author       :   <a href="https://github.com/afanzaimoyu">afan</a>
# @Time         :   2024/1/23
# @Description  :   场景枚举


class OssSceneEnum(Enum):
    CHAT = (1, "聊天", "/chat")
    EMOJI = (2, "表情包", "/emoji")

    def __init__(self, code, name, path):
        self.code = code
        self.name = name
        self.path = path
