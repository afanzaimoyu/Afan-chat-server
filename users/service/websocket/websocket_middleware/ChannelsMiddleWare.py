import logging

from asgiref.sync import sync_to_async
from channels.auth import AuthMiddlewareStack
from channels.middleware import BaseMiddleware
from channels.routing import URLRouter
from channels.security.websocket import AllowedHostsOriginValidator
from ninja_jwt.tokens import AccessToken
from typing import Union

logger = logging.getLogger(__name__)


class WSMiddleWare(BaseMiddleware):

    async def __call__(self, scope, receive, send):
        token = await self.get_token(scope)

        scope["token"] = token

        ip = await self.get_real_ip(scope)
        scope['ip'] = ip

        return await super().__call__(scope, receive, send)

    @staticmethod
    async def get_token(scope: dict) -> Union[bytes, None]:
        parts = scope.get("query_string", b"")
        if parts:
            return parts.split(b"=")[1]
        else:
            # 未登录
            return None

    @staticmethod
    async def get_real_ip(scope: dict) -> str:
        """
        获取真实ip
        Args:
            scope: websocket scope
        Returns:
            ip
        """
        headers = dict(scope.get('headers', []))
        # real_ip = headers.get(b'x-real-ip', b'').decode('utf-8')
        # if not real_ip:
        x_forwarded_for = headers.get(b'x-forwarded-for', b'').decode('utf-8')
        real_ip = x_forwarded_for.split(',')[0].strip()
        return real_ip


def WSMiddleWareStack(inner):
    return AllowedHostsOriginValidator(WSMiddleWare(URLRouter(inner)))
