from ninja_extra import api_controller, http_post, http_get
from ninja_extra.permissions import IsAuthenticated
from ninja_schema import Schema

from chat.chat_schema import MessageInput
from users.user_tools.cht_jwt_uthentication import AfanJWTAuth


@api_controller("/chat", tags=["消息模块"], auth=AfanJWTAuth(), permissions=[IsAuthenticated])
class ChatController:
    # TODO 频控
    @http_post("/msg", description="发送消息")
    def send_msg(self, request, msg_input: MessageInput):
        user = request.user
        msg_input.send_msg(user)


