from chat.models import Message
from chat.msg_schema.abs_msg_handler import AbstractMsgHandler


class SystemMsgHandler(AbstractMsgHandler):
    """
    系统消息
    """

    @staticmethod
    def get_msg_type_enum():
        return Message.MessageTypeEnum.SYSTEM

    def check_msg(self, body: dict, room_id: int, uid: int):
        return body

    def save_msg(self, message, body):
        message.content = body
        message.type = self.get_msg_type_enum()
        message.save()

    def show_msg(self, msg):
        return msg.content

    @staticmethod
    def show_reply_msg(msg):
        return msg.content

    def show_contact_msg(self, msg):
        return msg.content
