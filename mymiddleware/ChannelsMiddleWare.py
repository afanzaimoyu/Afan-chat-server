import json

import ninja_jwt.exceptions
from asgiref.sync import sync_to_async
from channels.auth import AuthMiddlewareStack
from channels.middleware import BaseMiddleware
from ninja_jwt.tokens import AccessToken

from users.models import CustomUser


class JwtAuthMiddleWare(BaseMiddleware):
    # TODO: 如果nginx反代 如何获取真实地址

    async def __call__(self, scope, receive, send):

        user = await sync_to_async(self.get_user)(scope)

        scope["user"] = user

        return await super().__call__(scope, receive, send)

    def get_user(self, scope):
        parts = dict(scope['headers']).get(b'authorization', b'').split()
        print(parts)
        if len(parts) == 0 or parts[0] != b"Bearer" or len(parts) != 2:
            # 未登录
            return None
        else:
            token = parts[1]

            try:
                user_id = AccessToken(token).payload.get('user_id')
                return user_id

            except Exception as e:
                print(e)
                return None


def JwtAuthMiddleWareStack(inner):
    return JwtAuthMiddleWare(AuthMiddlewareStack(inner))
