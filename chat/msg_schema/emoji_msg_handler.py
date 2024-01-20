from chat.chat_schema import EmojisMsgSchema, MessageExtra
from chat.models import Message
from chat.msg_schema.abs_msg_handler import AbstractMsgHandler


class EmojiMsgHandler(AbstractMsgHandler):
    """
    表情消息
    """

    @staticmethod
    def get_msg_type_enum():
        return Message.MessageTypeEnum.EMOJI

    def check_msg(self, body: dict, room_id: int, uid: int):
        return EmojisMsgSchema(**body)

    def save_msg(self, message, body):
        extra = MessageExtra(**message.extra) if message.extra else MessageExtra()
        extra.emojisMsg = body
        message.extra = extra.dict(exclude_none=True)
        message.save()

    def show_msg(self, msg):
        return msg.extra.get("emojisMsg")

    @staticmethod
    def show_reply_msg(msg):
        return "表情"

    def show_contact_msg(self, msg):
        return "[表情包]"
