from typing import List

from ninja_extra import api_controller, http_get, http_post, http_delete
from ninja_extra.permissions import IsAuthenticated

from users.models import UserEmoji
from users.user_schema.user_emoji_schema import UserEmojiResp, UserEmojiReq, IdReq, IdResp
from users.user_tools.cht_jwt_uthentication import AfanJWTAuth


@api_controller("/user/emoji", tags=["用户表情包"], auth=AfanJWTAuth(), permissions=[IsAuthenticated])
class UserEmojiController:

    @http_get("/list", response=List[UserEmojiResp], description="表情包列表")
    def get_emoji_page(self, request):
        user = request.user
        return UserEmoji.objects.filter(user=user, delete_status=UserEmoji.Status.NORMAL).all()

    @http_post(description="新增表情包", response=IdResp)
    def insert_emoji(self, url: UserEmojiReq):
        return url.insert_emoji()

    @http_delete(description="删除表情包")
    def delete_emoji(self, emoji_id: IdReq):
        emoji_id.delete_emoji()
        return True
