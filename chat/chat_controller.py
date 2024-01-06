from django.http import HttpRequest
from ninja_extra import api_controller, http_post, http_get, paginate, http_put
from ninja_extra.permissions import IsAuthenticated, BasePermission
from ninja_schema import Schema

from chat.chat_message_resp import ChatMessageRespSchema
from chat.chat_schema import MessageInput, ChatMessageBaseReq
from chat.models import Message
from contacts.utils.pagintion import CursorPagination, CursorPaginationResponseSchema
from users.user_tools.cht_jwt_uthentication import AfanJWTAuth


class IsGroupChatAdministrator(BasePermission):
    """
    只允许群聊超级管理员访问
    """

    message = "抱歉，你没有权限"

    def has_permission(
            self, request: HttpRequest, controller: "ControllerBase"
    ) -> bool:
        user = request.user or request.auth  # type: ignore
        return bool(user and user.groups.filter(name__in=['超级管理员', "群聊管理员"]).exists())


@api_controller("/chat", tags=["消息模块"], auth=AfanJWTAuth(), permissions=[IsAuthenticated])
class ChatController:
    # TODO 频控
    @http_post("/msg", description="发送消息")
    def send_msg(self, request, msg_input: MessageInput):
        user = request.user
        rsp = msg_input.send_msg(user)
        return rsp

    @http_get("/public/msg/page", description="消息列表",
              response=CursorPaginationResponseSchema[ChatMessageRespSchema])
    @paginate(CursorPagination, mapper=Message, cursor_column="id")
    def get_msg_page(self, request, roomId: int):
        return {"&": {"room_id": roomId}, "~": {"type": Message.MessageTypeEnum.RECALL}}

    @http_put("/msg/recall", description="撤回消息", permissions=[IsGroupChatAdministrator])
    def recall_msg(self, request, recall_param: ChatMessageBaseReq):
        uid = request.user.id
        recall_param.recall(uid)

    @http_get("test")
    def test(self):
        reply = Message.objects.filter(id=30, status=Message.Status.NORMAL)
        print(reply.get())
