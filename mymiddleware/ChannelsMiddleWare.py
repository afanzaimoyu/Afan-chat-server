import json

import ninja_jwt.exceptions
from channels.auth import AuthMiddlewareStack
from channels.middleware import BaseMiddleware
from ninja_jwt.tokens import AccessToken


class JwtAuthMiddleWare(BaseMiddleware):

    async def __call__(self, scope, receive, send):
        parts = dict(scope['headers']).get(b'authorization', b'').split()
        print(parts)

        if len(parts) == 0 or parts[0] != b"Bearer" or len(parts) != 2:
            # 未登录
            scope["user"] = None
        else:
            token = parts[1]

            try:
                user_id = AccessToken(token).payload.get('user_id')
                scope["user"] = user_id

            except ninja_jwt.exceptions.TokenError as e:
                scope["user"] = None

        return await super().__call__(scope, receive, send)


def JwtAuthMiddleWareStack(inner):
    return JwtAuthMiddleWare(AuthMiddlewareStack(inner))
