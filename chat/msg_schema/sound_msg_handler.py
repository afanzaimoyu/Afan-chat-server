from chat.chat_schema import MessageExtra, SoundMsgSchema
from chat.models import Message
from chat.msg_schema.abs_msg_handler import AbstractMsgHandler


class SoundMsgHandler(AbstractMsgHandler):
    """
    语音消息
    """

    @staticmethod
    def get_msg_type_enum():
        return Message.MessageTypeEnum.SOUND

    def check_msg(self, body: dict, room_id: int, uid: int):
        return SoundMsgSchema(**body)

    def save_msg(self, message, body):
        extra = MessageExtra(**message.extra) if message.extra else MessageExtra()
        extra.soundMsg = body
        message.extra = extra.dict(exclude_none=True)
        message.save()

    def show_msg(self, msg):
        return msg.extra.get("soundMsg")

    @staticmethod
    def show_reply_msg(msg):
        return "语音"

    def show_contact_msg(self, msg):
        return "[语音]"
