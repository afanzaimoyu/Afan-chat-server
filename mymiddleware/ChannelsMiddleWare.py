import json

import ninja_jwt.exceptions
from asgiref.sync import sync_to_async
from channels.auth import AuthMiddlewareStack
from channels.middleware import BaseMiddleware
from ninja_jwt.tokens import AccessToken

from users.models import CustomUser


class JwtAuthMiddleWare(BaseMiddleware):
    # 如果nginx反代 如何获取真实地址

    async def __call__(self, scope, receive, send):

        user = await sync_to_async(self.get_user)(scope)

        scope["user"] = user

        ip = await sync_to_async(self.get_real_ip)(scope)
        scope['ip'] = ip

        return await super().__call__(scope, receive, send)

    def get_user(self, scope):
        parts = scope.get("query_string", b"")
        print(parts)
        if parts:
            token = parts.split(b"=")[1]
            print(token)
            try:
                user_id = AccessToken(token).payload.get('user_id')
                return user_id
            except Exception as e:
                print(e)
                return None

        else:
            # 未登录
            return None

    def get_real_ip(self, scope):
        headers = dict(scope.get('headers', []))
        real_ip = headers.get(b'x-real-ip', b'').decode('utf-8')
        if not real_ip:
            x_forwarded_for = headers.get(b'x-forwarded-for', b'').decode('utf-8')
            real_ip = x_forwarded_for.split(',')[0].strip()
        return real_ip


def JwtAuthMiddleWareStack(inner):
    return JwtAuthMiddleWare(AuthMiddlewareStack(inner))
