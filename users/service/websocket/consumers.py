import asyncio
import logging

from asgiref.sync import async_to_sync
from channels.generic.websocket import JsonWebsocketConsumer
from django.conf import settings
from django.core.cache import cache
from ninja_jwt.tokens import AccessToken

from users.domain.enums.ws_enums.req_type_enum import WSReqTypeEnum
from users.domain.vo.request.ws.base_req import WSBaseReq
from users.models import CustomUser
from users.service.adapter.ws_adapter import WSAdapter
from users.signals import user_online_signal, user_offline_signal
from users.user_tools.tools import get_token, generate_login_code, request_qr_code

logger = logging.getLogger(__name__)


class ChatConsumer(JsonWebsocketConsumer):

    def connect(self):
        logger.info("WebSocket 连接")
        # 连接建立时，将连接加入到 "login_group"
        async_to_sync(self.channel_layer.group_add)("chat_group", self.channel_name)
        self.scope['uid'] = None
        self.accept()
        if self.scope['ip'] is None:
            self.disconnect(4000)

        if self.scope['token']:
            self.authorize()

    def disconnect(self, code):
        logger.info("WebSocket 断开")
        # 删除 channels 与 uid 的关联

        if cache.delete(self.scope['uid']) and self.scope['uid']:
            user_offline_signal.send(sender=self.__class__, uid=self.scope['uid'])
        async_to_sync(self.channel_layer.group_discard)("chat_group", self.channel_name)

        self.close()

    def receive_json(self, content, **kwargs):
        try:
            ws_base_req = WSBaseReq(**content)
        except Exception:
            logger.warning(f"未知的消息类型, 前端传递的消息为: {content}")
            return self.disconnect(404)

        match ws_base_req.type:
            case WSReqTypeEnum.LOGIN:
                self.handle_login_request()
            case WSReqTypeEnum.HEARTBEAT:
                pass
            case _:
                logger.info("未知的消息类型")

    def authorize(self):
        logger.info('校验token')
        try:
            user_id = AccessToken(self.scope.get('token')).payload.get('user_id')
            self.scope['uid'] = user_id
            return self.login_success()
        except Exception as e:
            logger.info(e)
            self.send_msg(WSAdapter.build_invalidate_token_resp())

    def handle_login_request(self):
        logger.info('请求登录二维码')
        # 生成唯一的登录码并与通道关联
        login_code = generate_login_code(self.scope['ip'])
        expire_seconds = settings.ENV.int("EXPIRE_SECONDS")
        cache.set(login_code, self.channel_name, expire_seconds)

        # 请求微信 API 获取二维码
        wx_mp_qr_code_ticket = request_qr_code(login_code)

        # 将生成的二维码 URL 发送回前端
        self.send_msg(WSAdapter.get_login_url(wx_mp_qr_code_ticket))

    def out_login_success(self, event):
        self.scope['uid'] = event['message']
        self.login_success()

    def login_success(self, user=None):
        logger.info(f"{self.scope['uid']}登陆成功")
        user = CustomUser.objects.get(id=self.scope.get('uid'))

        # 保存uid 和 channels 的关系
        cache.set(self.scope.get('uid'), self.channel_name)

        # 推送成功消息
        self.send_json(WSAdapter.build_login_success_resp(user))
        # 用户成功上线事件

        user_online_signal.send(sender=self.__class__, user=user, ip=self.scope['ip'])

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
        # TODO 待删除
        print(event, "===")
        self.send_json(
            {"type": 5, "data": event["message"]}
        )

    def out_send_msg(self, event):
        self.send_msg(event["message"])

    def send_msg(self, resp):
        logger.info(f'向前端发送消息: {resp}')
        self.send_json(resp)
