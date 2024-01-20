from chat.chat_schema import MessageExtra, ImgMsgSchema
from chat.models import Message
from chat.msg_schema.abs_msg_handler import AbstractMsgHandler


class ImgMsgHandler(AbstractMsgHandler):
    """
    图片消息
    """

    @staticmethod
    def get_msg_type_enum():
        return Message.MessageTypeEnum.IMG

    def check_msg(self, body: dict, room_id: int, uid: int):
        return ImgMsgSchema(**body)

    def save_msg(self, message, body):
        extra = MessageExtra(**message.extra) if message.extra else MessageExtra()
        extra.imgMsg = body
        message.extra = extra.dict(exclude_none=True)
        message.save()

    def show_msg(self, msg):
        return msg.extra.get("imgMsg")

    @staticmethod
    def show_reply_msg(msg):
        return "图片"

    def show_contact_msg(self, msg):
        return "[图片]"
