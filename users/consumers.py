from channels.generic.websocket import AsyncJsonWebsocketConsumer
from django.core.cache import cache

from config.settings.base import env
from users.apis.wx_api import WeChatOAuth
from users.user_tools.tools import generate_login_code




class ChatConsumer(AsyncJsonWebsocketConsumer):
    async def connect(self):
        print("WebSocket 连接")

        await self.accept()

    async def receive_json(self, content, **kwargs):
        match content.get("type"):
            case 1:
                await self.handle_login_request()
            case 2:
                await self.send_json({"data": {"message": "心跳"}})
            case 3:
                await self.send_json({"data": {"message": "登录认证"}})
            case _:
                pass

    async def disconnect(self, code):
        print("WebSocket 断开")
        cache.delete(self.channel_name)

    async def handle_login_request(self):
        # 生成唯一的登录码并与通道关联
        login_code = generate_login_code(self.scope['client'][0])
        expire_seconds = env.int("expire_seconds")
        cache.set(self.channel_name,{"uid": None, "code": login_code},expire_seconds)

        # 请求微信 API 获取二维码
        wx_mp_qr_code_ticket = request_qr_code(login_code)
        print(cache.get(self.channel_name))

        # 将生成的二维码 URL 发送回前端
        await self.send_json({"data": {"message": "请求登录二维码", "qr_code_url": wx_mp_qr_code_ticket}})


def request_qr_code(login_code):
    wechat_oauth = WeChatOAuth()
    access_token = cache.get("wx_access_token") if cache.get(
        "wx_access_token") else wechat_oauth.fetch_normal_access_token
    res = wechat_oauth.create_temporary_qrcode(access_token, login_code).get('url')
    return res
