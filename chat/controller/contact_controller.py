from ninja import Query
from ninja_extra import api_controller, http_get, paginate
from ninja_extra.permissions import IsAuthenticated

from chat.chat_room_resp import ChatRoomCursorInputSchema
from chat.models import Room, RoomFriend
from contacts.utils.pagintion import CursorPagination
from users.exceptions.chat import Business_Error
from users.models import CustomUser
from users.user_tools.cht_jwt_uthentication import AfanJWTAuth2


@api_controller("/chat/public", tags=["聊天室相关接口"], auth=AfanJWTAuth2())
class ContactController:

    @http_get("/contact/page", description="会话列表")
    # @paginate(CursorPagination, mapper=Message, cursor_column="id")
    def get_room_page(self, request, cursor_input: Query[ChatRoomCursorInputSchema]):
        user = request.user
        return cursor_input.get_contact_page(user)

    @http_get("/contact/detail", description="会话详情")
    def get_contact_detail(self, request, id: int):
        user = request.user
        room = None
        if user.is_anonymous:
            room = Room.objects.filter(id=id, hot_flag=Room.HotFlag.YES)
        else:
            room = Room.objects.filter(id=id)
        if not room.exists():
            raise Business_Error(detail="房间号有误", code=0)
        return ChatRoomCursorInputSchema.build_contact_resp(user=request.user, rooms=[room.get()])[0]

    @http_get("/contact/detail/friend", description="会话详情(联系人列表发消息用)")
    def get_contact_detail_by_friend(self, request, uid: int):
        my = request.user

        if my.is_anonymous:
            raise Business_Error(detail="请先登录", code=0)
        if my.id == uid:
            raise Business_Error(detail="不能和自己聊天", code=0)
        friend_room = RoomFriend.get_friend_room(my.id, uid)
        if not friend_room:
            raise Business_Error(detail="他不是你的好友", code=0)
        return ChatRoomCursorInputSchema.build_contact_resp(user=request.user, rooms=[friend_room.room])[0]
