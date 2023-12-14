import hashlib
import json
from typing import cast

import xmltodict
from asgiref.sync import async_to_sync
from channels.layers import get_channel_layer
from django.core.cache import cache
from django.http import HttpResponse, HttpRequest
from django.shortcuts import get_object_or_404
from django.views.decorators.csrf import csrf_exempt
from ninja import Schema
from ninja.parser import Parser
from ninja.types import DictStrAny
from ninja_extra import NinjaExtraAPI, api_controller, http_get, http_post

from config.settings.base import env
from users.apis.wx_api import WeChatOAuth
from users.models import CustomUser
from users.user_tools.tools import extract_login_code_from_event_key


class MyParser(Parser):
    def parse_body(self, request: HttpRequest) -> DictStrAny:
        content_type = request.headers.get("Content-Type", "").lower()

        if 'xml' in content_type:
            return cast(DictStrAny, xmltodict.parse(request.body))
        else:
            return cast(DictStrAny, json.loads(request.body))


api = NinjaExtraAPI(parser=MyParser())


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

        channel_layer = get_channel_layer()

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

                print('get_channel_layer',channel_layer)
                message = {
                    "type":"type.message",
                    "message":{
                        "type":"2"
                    }
                }
                async_to_sync(channel_layer.send)(channel_name,message)
                print("发送成功", res)

            elif dic.get("Event") == "SCAN":
                # 用户已关注
                user = get_object_or_404(CustomUser, open_id=openid)

                channel_name = cache.get(event_key)
                message = {
                    "type": "type.message",
                    "message": {
                        "type": "3",
                        "data": {
                            "uid": user.id,
                            "nickname": user.name,
                            "avatar": user.avatar
                        }

                    }
                }
                async_to_sync(channel_layer.send)(channel_name, message)

            elif dic.get("Event") == "unsubscribe":
                # 取消关注
                user = get_object_or_404(CustomUser, open_id=openid)
                user.delete()



    @http_get("/auth")
    def my_auth(self, code: str):
        # 授权
        data = self.wx_auth.fetch_access_token(code)
        open_id = data.get("openid")
        access_token = data.get("access_token")

        #保存用户信息
        user_info = self.wx_auth.get_user_info(open_id, access_token)
        nickname = user_info.get("nickname")
        avatar = user_info.get("headimgurl")
        user_id = CustomUser.objects.create_user(open_id,name=nickname,avatar=avatar)
        print('用户信息保存成功')

        #发送成功信号
        login_code = cache.get(open_id)
        channel_name = cache.get(login_code)
        channel_layer = get_channel_layer()
        message = {
            "type": "type.message",
            "message": {
                "type": "3",
                "data":{
                    "uid":user_id,
                    "nickname":nickname,
                    "avatar":avatar
                }

            }
        }
        async_to_sync(channel_layer.send)(channel_name, message)


api.register_controllers(
    WeChatLoginApi
)
