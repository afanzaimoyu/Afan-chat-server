import asyncio
from pprint import pprint

from asgiref.sync import async_to_sync
from channels.generic.websocket import JsonWebsocketConsumer
from django.core.cache import cache

from config.settings.base import env
from users.apis.wx_controller import WeChatOAuth
from users.models import CustomUser
from users.signals import user_online_signal, user_offline_signal
from users.user_tools.tools import generate_login_code, get_token


class ChatConsumer(JsonWebsocketConsumer):

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.heartbeat_timeout = None
    def connect(self):
        print("WebSocket 连接")
        pprint(self.scope)
        # 连接建立时，将连接加入到 "login_group"
        async_to_sync(self.channel_layer.group_add)("chat_group", self.channel_name)

        self.accept()
        print(self.channel_name)
        print(self.scope['user'])
        if self.scope['user']:
            self.login_success()
            print(2)
        loop = asyncio.new_event_loop()
        asyncio.set_event_loop(loop)
        self.heartbeat_timeout = loop.call_later(30, self.disconnect, 4000)

    def disconnect(self, code):
        print("WebSocket 断开")
        # 删除 channels 与 uid 的关联
        cache.delete(self.scope['user'])
        user_offline_signal.send(sender=self.__class__, uid=self.scope['user'])

        async_to_sync(self.channel_layer.group_discard)("chat_group", self.channel_name)

        self.close()

    def receive_json(self, content, **kwargs):
        match content.get("type"):
            case 1:
                self.handle_login_request()
            case 2:
                if self.heartbeat_timeout is not None:
                    self.heartbeat_timeout.cancel()
                self.heartbeat_timeout = asyncio.get_event_loop().call_later(30, self.disconnect, 4000)
            case 3:
                self.login_authentication()
            case _:
                pass

    def login_success(self, event=None):
        if event:
            self.scope['user'] = event["user"]
        uid = self.scope['user']
        user = CustomUser.objects.get(id=uid)
        user_token = get_token(user)
        # 保存uid 和 channels 的关系
        cache.set(uid, self.channel_name)

        # 判断用户是否是管理员或群聊管理员
        is_admin_or_group_admin = 1 if user.groups.filter(name__in=['超级管理员', '群聊管理员']).exists() else 0

        # 推送成功消息
        self.send_json({
            "type": 3,
            "data": {
                "uid": user.id,
                "name": user.name,
                "avatar": user.avatar,
                'power': is_admin_or_group_admin,
                "token": user_token.get('access'),
            }
        })
        # 用户成功上线事件

        user_online_signal.send(sender=self.__class__, user=user, ip=self.scope['client'][0])

    def handle_login_request(self):
        # 生成唯一的登录码并与通道关联
        login_code = generate_login_code(self.scope['client'][0])
        expire_seconds = env.int("expire_seconds")
        cache.set(login_code, self.channel_name, expire_seconds)

        # 请求微信 API 获取二维码
        wx_mp_qr_code_ticket = request_qr_code(login_code)
        print(type(cache.get(self.channel_name)))

        # 将生成的二维码 URL 发送回前端
        self.send_json({
            "type": 1,
            "data": {
                "loginUrl": wx_mp_qr_code_ticket
            }
        })

    def loading_auth(self, event=None):
        print("loading_auth")
        self.send_json(
            {"type": 2}
        )

    def send_message(self, event):
        self.send_json(
            event["message"]
        )

    def send_message_all(self, event=None):
        print(event, "===")
        self.send_json(
            {"type": 5, "data": event["message"]}
        )

    def login_authentication(self):
        if self.scope["user"]:
            self.send_json({
                "code": 200,
                "data": {
                    "message": "OK"
                }
            })
        else:
            self.send_json({
                "code": 4000,
                "data": {
                    "message": "令牌无效或已过期"
                }
            })


def request_qr_code(login_code):
    wechat_oauth = WeChatOAuth()
    access_token = cache.get("wx_access_token") if cache.get(
        "wx_access_token") else wechat_oauth.fetch_normal_access_token
    res = wechat_oauth.create_temporary_qrcode(access_token, login_code).get('url')
    return res
