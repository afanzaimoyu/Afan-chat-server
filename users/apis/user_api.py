import pprint

from django.db import connection
from django.db.models import Q
from django.shortcuts import get_object_or_404
from ninja_extra import NinjaExtraAPI, api_controller, http_get, http_put
from ninja_extra.shortcuts import get_object_or_exception
from ninja_jwt.authentication import JWTAuth
from ninja_extra.permissions import IsAuthenticated

from users.models import ItemConfig, CustomUser
from users.user_schema.user_schema import UserInfoSchema, ModifyNameInput
from users.user_tools.afan_ninja import AfanNinjaAPI
from users.user_tools.cht_jwt_uthentication import AfanJWTAuth

capi = AfanNinjaAPI(urls_namespace="User api")


@api_controller("/user", tags=["User 类"], auth=AfanJWTAuth(), permissions=[IsAuthenticated])
class UserController:

    @http_get("userinfo", response=UserInfoSchema, description="获取用户信息")
    def get_user_info(self, request):
        user = request.user
        return user

    @http_put("/name", description="修改用户名")
    def modify_name(self, request, name: ModifyNameInput):
        user = request.user
        name.update(user)
        return {"message": "OK"}

    @http_get("/badges", description="获得徽章列表")
    def badges(self):
        """

        Returns:
            dick:
            - id 徽章id
            - img 徽章图标
            - describe 徽章描述
            - obtain 是否拥有
            - wearing 是否佩戴

        """
        # TODO:查询所有徽章
        # TODO:查询用户拥有的徽章
        # TODO: 查询用户佩戴的徽章
        pass
    @http_put("/badge",description="佩戴徽章")
    def badge(self):
        # TODO: 佩戴徽章
        pass


capi.register_controllers(
    UserController
)
