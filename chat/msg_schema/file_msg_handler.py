from chat.chat_schema import  MessageExtra, FileMsgSchema
from chat.models import Message
from chat.msg_schema.abs_msg_handler import AbstractMsgHandler


class FileMsgHandler(AbstractMsgHandler):
    """
    图片消息
    """

    @staticmethod
    def get_msg_type_enum():
        return Message.MessageTypeEnum.FILE

    def check_msg(self, body: dict, room_id: int, uid: int):
        return FileMsgSchema(**body)

    def save_msg(self, message, body):
        extra = MessageExtra(**message.extra) if message.extra else MessageExtra()
        extra.fileMsg = body
        message.extra = extra.dict(exclude_none=True)
        message.save()

    def show_msg(self, msg):
        return msg.extra.get("fileMsg")

    @staticmethod
    def show_reply_msg(msg):
        return f"文件: {msg.extra.get('fileMsg').get('fileName')}"

    def show_contact_msg(self, msg):
        return f"[文件]{msg.extra.get('fileMsg').get('fileName')}"
