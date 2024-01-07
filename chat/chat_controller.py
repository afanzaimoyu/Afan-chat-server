import time

from django.http import HttpRequest
from django.utils import timezone
from ninja_extra import api_controller, http_post, http_get, paginate, http_put
from ninja_extra.permissions import IsAuthenticated, BasePermission
from ninja_schema import Schema

from chat.chat_message_resp import ChatMessageRespSchema
from chat.chat_schema import MessageInput, ChatMessageBaseReq
from chat.models import Message
from chat.utils.sensitive_word.sensitive_word_filter import MySQLSensitiveWordFilter
from chat.utils.url_discover.prioritized_url_discover import PrioritizedUrlDiscover
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
        pass
        # # long_str = "www.baidu.com"
        # long_str="http://www.jd.com:80"
        # # long_str="http://mallchat.cn"
        # # long_str="https://mp.weixin.qq.com/s/hwTf4bDck9_tlFpgVDeIKg"
        # # long_str="https://www.bing.com/search?q=re+%5Cw+%E5%95%8A%E5%95%8A%E5%95%8A&qs=n&form=QBRE&sp=-1&lq=0&pq=re+%5Cw+a%27a%27a&sc=7-11&sk=&cvid=1C3CE2C7A6574B9C83C3EBF9F92608E8&ghsh=0&ghacc=0&ghpl="
        # long_str = "其中包含一个URL www.baidu.com，一个带有端口号的URL http://www.jd.com:80, 一个带有路径的URL http://mallchat.cn, 还有美团技术文章https://mp.weixin.qq.com/s/hwTf4bDck9_tlFpgVDeIKg,https://www.bing.com/search?q=re+%5Cw+%E5%95%8A%E5%95%8A%E5%95%8A&qs=n&form=QBRE&sp=-1&lq=0&pq=re+%5Cw+a%27a%27a&sc=7-11&sk=&cvid=1C3CE2C7A6574B9C83C3EBF9F92608E8&ghsh=0&ghacc=0&ghpl="
        # discover = PrioritizedUrlDiscover()
        # url_content_map = discover.get_url_content_map(long_str)
        # print(url_content_map)
