import hashlib
import json
from typing import cast, Type, Optional, Any, Dict
import xmltodict

from asgiref.sync import async_to_sync
from channels.consumer import AsyncConsumer
from channels.layers import get_channel_layer

from django.contrib.auth.models import update_last_login
from django.core.cache import cache
from django.http import HttpResponse, HttpRequest
from django.shortcuts import get_object_or_404
from django.views.decorators.csrf import csrf_exempt

from ninja import Schema
from ninja.parser import Parser
from ninja.schema import DjangoGetter
from ninja.types import DictStrAny

from ninja_extra import NinjaExtraAPI, api_controller, http_get, http_post
from ninja_extra.exceptions import ValidationError

from ninja_jwt import exceptions
from ninja_jwt.tokens import AccessToken, RefreshToken
from ninja_jwt.utils import token_error

from pydantic import model_validator

from config.settings.base import env
from contacts.models import UserFriend

from users.apis.wx_controller import WeChatOAuth
from users.models import CustomUser, Blacklist
from users.tasks import refresh_ip_detail_async, send_message_all_async
from users.user_schema.ipinfo_schema import Ipinfo
from users.user_tools.afan_ninja import AfanNinjaAPI
from users.user_tools.tools import extract_login_code_from_event_key, get_token


class TokenRefreshInputSchema(Schema):
    refresh: str

    @model_validator(mode="before")
    def validate_schema(cls, values: DjangoGetter) -> dict:
        values = values._obj

        if isinstance(values, dict):
            if not values.get("refresh"):
                raise exceptions.ValidationError({"refresh": "token is required"})
        return values


class TokenRefreshOutputSchema(Schema):
    access: str

    @model_validator(mode="before")
    @token_error
    def validate_schema(cls, values: DjangoGetter) -> Any:
        values = values._obj
        if isinstance(values, dict):
            if not values.get("refresh"):
                raise exceptions.ValidationError(
                    {"refresh": "refresh token is required"}
                )
            refresh = RefreshToken(values["refresh"])
            data = {"access": str(refresh.access_token)}
            values.update(data)
        return values


class WxData(Schema):
    xml: dict


@api_controller('/wx', tags=["Wechat Login"], permissions=[])
class WeChatLoginApi:
    wx_auth = WeChatOAuth()

    @http_get('/login')
    @csrf_exempt
    def wechat_auth(self, signature, timestamp, nonce, echostr):
        wx_token = env.str("Token")

        tmp_arr = [wx_token, timestamp, nonce]
        tmp_arr.sort()
        tmp_str = ''.join(tmp_arr)
        tmp_str = hashlib.sha1(tmp_str.encode()).hexdigest()

        if tmp_str == signature:
            return HttpResponse(echostr)
        else:
            return ""

    @http_post("/login")
    def concern(self, openid: str, data: WxData):
        """
        TODO: 关注授权等一系列流程
        Args:
            openid:
            data:

        Returns:

        """
        print('3', data)
        dic = data.dict().get('xml')
        print(dic)
        event_key = str(dic.get("EventKey"))
        print('ek---', event_key)

        if dic.get("MsgType") == "event":

            if dic.get("Event") == "subscribe":
                # 用户未关注
                login_code = extract_login_code_from_event_key(event_key)
                cache.set(openid, login_code, env.int("expire_seconds"))

                authorize_url = self.wx_auth.authorize_url
                print(authorize_url)
                access_token = cache.get("wx_access_token")
                res = self.wx_auth.fetch_template_text(openid, access_token, authorize_url)

                # 推送消息给用户（通过连接进行推送）
                channel_name = cache.get(login_code)
                communicates_with_websockets(channel_name, "loading_auth")
                print("发送成功", res)

            elif dic.get("Event") == "SCAN":
                # 用户已关注
                user = get_object_or_404(CustomUser, open_id=openid)

                channel_name = cache.get(event_key)
                communicates_with_websockets(channel_name, "login_success", user.id)

            elif dic.get("Event") == "unsubscribe":

                user = get_object_or_404(CustomUser, open_id=openid)
                user.backpacks.clear()
                user.delete()
                print("取消关注")

    @http_get("/auth")
    def my_auth(self, code: str):
        # 授权
        data = self.wx_auth.fetch_access_token(code)
        open_id = data.get("openid")
        access_token = data.get("access_token")

        # 保存用户信息
        user_info = self.wx_auth.get_user_info(open_id, access_token)
        nickname = user_info.get("nickname")
        avatar = user_info.get("headimgurl")
        user = CustomUser.objects.create_user(open_id, name=nickname, avatar=avatar)
        print('用户信息保存成功')

        # 获取当前连接
        login_code = cache.get(open_id)
        channel_name = cache.get(login_code)
        if not login_code and not channel_name:
            raise ValidationError(detail="授权失败，请重新扫码")

        communicates_with_websockets(channel_name, "login_success", user.id)

    @http_post(
        "/refresh",
        response=TokenRefreshOutputSchema,
        url_name="token_refresh",
    )
    def refresh(self, refresh_token: TokenRefreshInputSchema):
        return refresh_token.dict()

    @http_get("test")
    def test(self):
        current_user = CustomUser.objects.get(id=5)
        friendships =list( UserFriend.objects.filter(uid=current_user.id)[:2])
        # print(str(friendships.query))

        # 通过 friendships 获取所有好友的 uid
        friend_uids = [frend.friend_uid for frend in friendships]
        print(friend_uids)

        # 使用好友的 uid 查询好友的详细信息
        friends = CustomUser.objects.filter(id__in=friend_uids)
        for friend in friends:
            print(friend.name)




def communicates_with_websockets(channel_name, event_type, user=None):
    channel_layer = get_channel_layer()
    message = None
    if event_type == "loading_auth":
        message = {
            "type": "loading.auth",
        }
    elif event_type == "login_success":
        message = {
            "type": "login.success",
            "user": user
        }
    try:
        async_to_sync(channel_layer.send)(channel_name, message)
    except Exception as e:
        print(f"Error sending message: {e}")

    # 用户成功上线事件
