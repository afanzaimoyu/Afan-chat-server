from abc import abstractmethod, ABC, ABCMeta

from django.db import models, transaction
from ninja_schema import Schema
from pydantic._internal import _model_construction

from chat.models import Message
from chat.msg_schema.msg_handler_factory import MsgHandlerFactory


class MessageTypeEnum(models.IntegerChoices):
    TEXT = 1, "正常消息"
    RECALL = 2, "撤回消息"
    IMG = 3, "图片"
    FILE = 4, "文件"
    SOUND = 5, "语音"
    VIDEO = 6, "视频"
    EMOJI = 7, "表情"
    SYSTEM = 8, "系统消息"


class AbsMetaMsgHandler(ABCMeta):
    def __new__(mcs, name, bases, attrs):
        sub_cls = super().__new__(mcs, name, bases, attrs)
        print(mcs, name, bases, attrs)
        MsgHandlerFactory.register(sub_cls.get_msg_type_enum(), sub_cls)
        return sub_cls

    @staticmethod
    @abstractmethod
    def get_msg_type_enum():
        raise NotImplementedError("get_msg_type_enum方法必须在子类中实现。")


class AbstractMsgHandler(metaclass=AbsMetaMsgHandler):
    """
    消息处理器策略类
    """

    @staticmethod
    @abstractmethod
    def get_msg_type_enum():
        pass
        # raise NotImplementedError("get_msg_type_enum方法必须在子类中实现。")

    @abstractmethod
    def check_msg(self, body: dict, room_id: int, uid: int):
        pass

    @transaction.atomic
    def check_and_save_msg(self, request, uid: int):
        body = self.check_msg(request.body, request.roomId, uid)
        # # 统一保存
        insert = request.save_msg(uid)
        # # 子类扩展保存
        self.save_msg(insert, body)
        return insert.id

    @abstractmethod
    def save_msg(self, message, body):
        pass

    @abstractmethod
    def show_msg(self, msg):
        pass

    @abstractmethod
    def show_reply_msg(self, msg):
        pass

    @abstractmethod
    def show_contact_msg(self, msg):
        pass
