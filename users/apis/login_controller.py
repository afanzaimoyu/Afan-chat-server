import hashlib
import json
import logging
from typing import cast, Type, Optional, Any, Dict
import xmltodict

from asgiref.sync import async_to_sync
from channels.consumer import AsyncConsumer
from channels.layers import get_channel_layer

from django.contrib.auth.models import update_last_login
from django.core.cache import cache
from django.db.transaction import on_commit
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

from django.conf import settings
from contacts.models import UserFriend

from users.apis.wx_controller import WeChatOAuth
from users.models import CustomUser, Blacklist
from users.service.login import LoginService
from users.tasks import refresh_ip_detail_async, send_message_all_async
from users.user_schema.ipinfo_schema import Ipinfo
from users.user_tools.afan_ninja import AfanNinjaAPI
from users.user_tools.tools import extract_login_code_from_event_key, get_token

env = settings.ENV
logger = logging.getLogger(__name__)


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

    @http_get('/login')
    @csrf_exempt
    def wechat_auth(self, signature, timestamp, nonce, echostr):
        wx_token = env.str("TOKEN")

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
        关注授权等一系列流程
        Args:
            openid:
            data:

        Returns:

        """
        dic = data.dict().get('xml')
        event_key = str(dic.get("EventKey"))
        if dic.get("MsgType") == "event":
            logger.info("微信事件推送形式")

            if dic.get("Event") == "subscribe":
                logger.info("用户初次关注公众号")

                login_code = extract_login_code_from_event_key(event_key)
                cache.set(openid, login_code, env.int("EXPIRE_SECONDS"))

                LoginService.send_an_authorization_link(login_code, openid)

            elif dic.get("Event") == "SCAN":
                logger.info("用户已关注公众号")
                if CustomUser.objects.filter(open_id=openid).exists():
                    user = CustomUser.objects.get(open_id=openid)
                    channel_name = cache.get(event_key)
                    on_commit(lambda: LoginService.push_login_success_message(channel_name, user.id))
                else:
                    logger.info("用户已关注公众号，但是没有授权")
                    LoginService.send_an_authorization_link(event_key, openid)

            elif dic.get("Event") == "unsubscribe":
                logger.info("用户取消关注公众号")
                try:
                    user = CustomUser.objects.get(open_id=openid)
                    user.backpacks.clear()
                    user.delete()
                except CustomUser.DoesNotExist:
                    logger.warning("用户不存在")
        else:
            logger.warning(f'微信推送未知的消息类型 {dic.get("MsgType") == "event"}')

    @http_get("/auth")
    def my_auth(self, code: str):
        logger.info("用户点击链接授权")

        data = LoginService.wx_auth.fetch_access_token(code)
        open_id = data.get("openid")
        access_token = data.get("access_token")

        # 保存用户信息
        user_info = LoginService.wx_auth.get_user_info(open_id, access_token)
        nickname = user_info.get("nickname")
        avatar = user_info.get("headimgurl")
        user = CustomUser.objects.create_user(open_id, name=nickname, avatar=avatar)
        logger.info(f'{nickname} 用户信息保存成功')

        # 获取当前连接
        login_code = cache.get(open_id)
        channel_name = cache.get(login_code)
        if not login_code and not channel_name:
            logger.warning("用户授权失败")
            raise ValidationError(detail="授权失败，请重新扫码")

        on_commit(lambda: LoginService.push_login_success_message(channel_name, user.id))

    @http_post(
        "/refresh",
        response=TokenRefreshOutputSchema,
        url_name="token_refresh",
    )
    def refresh(self, refresh_token: TokenRefreshInputSchema):
        return refresh_token.dict()

