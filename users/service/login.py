# _*_ coding: utf-8 _*_
import logging

from asgiref.sync import async_to_sync
from channels.layers import get_channel_layer
from django.core.cache import cache

from users.apis.wx_controller import WeChatOAuth
from users.service.adapter.ws_adapter import WSAdapter

# @Author       :   <a href="https://github.com/afanzaimoyu">afan</a>
# @Time         :   2024/1/23
# @Description  :   None
logger = logging.getLogger(__name__)


class LoginService:
    wx_auth = WeChatOAuth()

    @classmethod
    def send_an_authorization_link(cls, login_code, openid):
        authorize_url = cls.wx_auth.authorize_url

        access_token = cls.wx_auth.fetch_normal_access_token

        channel_name = cache.get(login_code)
        if channel_name:
            cls.wx_auth.fetch_template_text(openid, access_token, authorize_url)
            cls.push_message_once(channel_name, WSAdapter.build_login_waiting_resp())
        else:
            # TODO 授权失败，请重新扫码的模板消息
            logger.info("授权失败，请重新扫码")

    @staticmethod
    def push_message(channel_name, message):
        try:
            print(2)
            logger.info(f"发送消息: {message}")
            channel_layer = get_channel_layer()
            async_to_sync(channel_layer.send)(channel_name, message)
        except Exception as e:
            logger.error(f"发送消息时出错: {e}")

    @classmethod
    def push_message_once(cls, login_code, data):
        message = {
            "type": "out_send_msg",
            "message": data
        }
        channel_name = cache.get(login_code)
        return cls.push_message(channel_name, message)

    @classmethod
    def push_login_success_message(cls, login_code, data):
        print(1)
        message = {
            "type": "out_login_success",
            "message": data
        }
        channel_name = cache.get(login_code)
        return cls.push_message(channel_name, message)
