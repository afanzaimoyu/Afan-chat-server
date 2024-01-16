from chat.chat_schema import MsgRecall
from chat.models import Message
from chat.msg_schema.abs_msg_handler import AbstractMsgHandler
from users.models import CustomUser


class RecallMsgHandler(AbstractMsgHandler):
    """撤回文本消息处理器"""

    def __init__(self):
        self.recall_schema = MsgRecall

    @staticmethod
    def get_msg_type_enum():
        return Message.MessageTypeEnum.RECALL

    def check_msg(self, body: dict, room_id: str, uid: int):
        pass

    def save_msg(self, message: Message.objects, body):
        pass

    def show_msg(self, msg):
        recall = msg.extra.get("recall")
        user = CustomUser.objects.filter(id=recall.get("recallUid")).get()
        if user.id != msg.from_user_id:
            return f"管理员\"{user.name}\"撤回了一条成员消息"
        else:
            return f'"{user.name}撤回了一条消息"'

    @staticmethod
    def show_reply_msg(msg):
        return "原消息已被撤回"

    def show_contact_msg(self, msg):
        return "撤回了一条消息"
