import pprint
from typing import List

from django.core.cache import cache
from django.db import connection
from django.db.models import Q
from django.http import HttpRequest
from django.shortcuts import get_object_or_404
from ninja_extra import NinjaExtraAPI, api_controller, http_get, http_put, http_post
from ninja_extra.shortcuts import get_object_or_exception
from ninja_jwt.authentication import JWTAuth
from ninja_extra.permissions import IsAuthenticated, BasePermission
from typing import TYPE_CHECKING
from users.models import ItemConfig, CustomUser, Blacklist
from users.user_schema.user_schema import UserInfoSchema, ModifyNameInput, BadgesOutSchema, WearingBadgeInput, \
    BlackInput, SummeryInfoResp, SummeryInfoReq, ItemInfoReq
from users.user_tools.afan_ninja import AfanNinjaAPI
from users.user_tools.cache_lock import distribute_item
from users.user_tools.cht_jwt_uthentication import AfanJWTAuth

if TYPE_CHECKING:
    from ninja_extra.controllers.base import ControllerBase  # pragma: no cover


class IsGroupChatSuperAdministrator(BasePermission):
    """
    只允许群聊超级管理员访问
    """

    message = "群聊管理员没有该权限"

    def has_permission(
            self, request: HttpRequest, controller: "ControllerBase"
    ) -> bool:
        user = request.user or request.auth  # type: ignore
        return bool(user and user.groups.filter(name__in=['超级管理员']).exists())


@api_controller("/user/public", tags=["User 公共接口"])
class UserPublicController:

    @http_post("/summary/userInfo/batch", description="用户聚合信息-返回的代表需要刷新的",
               response=List)
    def get_summery_user_info(self, info_input: SummeryInfoReq):
        return info_input.get_summery_user_info()

    @http_post("/badges/batch", description="徽章聚合信息-返回的代表需要刷新的",response=List)
    def get_item_info(self,info_input:ItemInfoReq):
        return info_input.get_item_info()


@api_controller("/user", tags=["User 类"], auth=AfanJWTAuth(), permissions=[IsAuthenticated])
class UserController:

    @http_get("userInfo", response=UserInfoSchema, description="获取用户信息")
    def get_user_info(self, request):
        user = request.user

        return user

    @http_put("/name", description="修改用户名")
    def modify_name(self, request, name: ModifyNameInput):
        user = request.user
        name.update(user)
        return {"message": "OK"}

    @http_get("/badges", response=List[BadgesOutSchema], description="获得徽章列表")
    def badges(self, request):
        """

        Returns:
            dick:
            - id 徽章id
            - img 徽章图标
            - describe 徽章描述
            - obtain 是否拥有
            - wearing 是否佩戴
        """
        user: CustomUser = request.user
        all_items = ItemConfig.objects.filter(item_type=2).all()
        user_item_ids = user.get_user_badges

        badges_list = []

        for item in all_items:
            badge_data = {
                'id': item.id,
                'img': item.img,
                'describe': item.describe,
                'obtain': item.id in user_item_ids,
                'wearing': item.id == user.item_id,
            }
            badges_list.append(badge_data)
        badges_list = sorted(badges_list, key=lambda x: not x['obtain'])

        return badges_list

    @http_put("/badge", description="佩戴徽章")
    def wearing_badge(self, request, item_id: WearingBadgeInput):
        # 佩戴徽章
        user = request.user
        item_id.update(user)
        return {"message": "OK"}

    @http_put("/black", description="拉黑用户", permissions=[IsGroupChatSuperAdministrator])
    def black(self, uid: BlackInput):
        uid.black_user()
        return {"message": "OK"}
