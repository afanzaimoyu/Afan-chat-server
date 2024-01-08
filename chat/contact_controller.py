from ninja import Query
from ninja_extra import api_controller, http_get, paginate
from ninja_extra.permissions import IsAuthenticated

from chat.chat_room_resp import ChatRoomCursorInputSchema
from contacts.utils.pagintion import CursorPagination
from users.user_tools.cht_jwt_uthentication import AfanJWTAuth2


@api_controller("/chat/public", tags=["聊天室相关接口"], auth=AfanJWTAuth2())
class ContactController:

    @http_get("/contact/page", description="会话列表")
    # @paginate(CursorPagination, mapper=Message, cursor_column="id")
    def get_room_page(self, request, cursor_input: Query[ChatRoomCursorInputSchema]):
        user = request.user
        return cursor_input.get_contact_page(user)

    @http_get("/contact/detail", description="会话详情")
    def get_contact_detail(self):
        pass

    @http_get("/contact/detail/friend", description="会话详情(联系人列表发消息用)")
    def get_contact_detail_by_friend(self):
        pass
