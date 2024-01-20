from chat.chat_schema import MessageExtra, VideoMsgSchema
from chat.models import Message
from chat.msg_schema.abs_msg_handler import AbstractMsgHandler


class VideoMsgHandler(AbstractMsgHandler):
    """
    视频消息
    """

    @staticmethod
    def get_msg_type_enum():
        return Message.MessageTypeEnum.VIDEO

    def check_msg(self, body: dict, room_id: int, uid: int):
        return VideoMsgSchema(**body)

    def save_msg(self, message, body):
        extra = MessageExtra(**message.extra) if message.extra else MessageExtra()
        extra.videoMsg = body
        message.extra = extra.dict(exclude_none=True)
        message.save()

    def show_msg(self, msg):
        return msg.extra.get("videoMsg")

    @staticmethod
    def show_reply_msg(msg):
        return "视频"

    def show_contact_msg(self, msg):
        return "[视频]"
