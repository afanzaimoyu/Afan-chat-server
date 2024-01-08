from typing import Type, Any, Optional, cast

from django.contrib.auth import get_user_model
from django.contrib.auth.models import AbstractUser, AnonymousUser
from django.core.cache import cache
from django.http import HttpRequest
from django.utils.translation import gettext_lazy as _
from ninja_extra.conf import settings
from ninja_extra.security import HttpBearer
from ninja_jwt.exceptions import TokenError, InvalidToken, AuthenticationFailed
from ninja_jwt.settings import api_settings
from ninja_jwt.tokens import Token


class AfanJWTBaseAuthentication:
    def __init__(self) -> None:
        super().__init__()
        self.user_model = get_user_model()

    @classmethod
    def get_validated_token(cls, raw_token) -> Type[Token]:
        """
        Validates an encoded JSON web token and returns a validated token
        wrapper object.
        """
        messages = []
        for AuthToken in api_settings.AUTH_TOKEN_CLASSES:
            try:
                return AuthToken(raw_token)
            except TokenError as e:
                messages.append(
                    {
                        "token_class": AuthToken.__name__,
                        "token_type": AuthToken.token_type,
                        "message": e.args[0],
                    }
                )

        raise InvalidToken(
            {
                "messages": messages,
            }
        )

    def get_user(self, validated_token, ip_address) -> Type[AbstractUser]:
        """
        Attempts to find and return a user using the given validated token.
        """
        try:
            user_id = validated_token[api_settings.USER_ID_CLAIM]
        except KeyError as e:
            raise InvalidToken(
                _("Token contained no recognizable user identification")
            ) from e

        black_list = cache.get("black_ipx", [])
        if any(str(item) in black_list for item in (user_id, ip_address)):
            raise AuthenticationFailed(_("Have been blocked"))

        try:
            user = self.user_model.objects.get(**{api_settings.USER_ID_FIELD: user_id})
        except self.user_model.DoesNotExist as e:
            raise AuthenticationFailed(_("User not found")) from e

        if not user.is_active:
            raise AuthenticationFailed(_("user is inactive"))

        return user

    def get_ident(self, request: HttpRequest) -> Optional[str]:
        """
        Identify the machine making the request by parsing HTTP_X_FORWARDED_FOR
        if present and number of proxies is > 0. If not use all of
        HTTP_X_FORWARDED_FOR if it is available, if not use REMOTE_ADDR.
        """
        xff = request.META.get("HTTP_X_FORWARDED_FOR")
        remote_addr = request.META.get("REMOTE_ADDR")
        num_proxies = settings.NUM_PROXIES

        if num_proxies is not None:
            if num_proxies == 0 or xff is None:
                return remote_addr
            addrs = xff.split(",")
            client_addr = addrs[-min(num_proxies, len(addrs))]
            return cast(str, client_addr.strip())

        return "".join(xff.split()) if xff else remote_addr

    def jwt_authenticate(self, request: HttpRequest, token: str) -> Type[AbstractUser]:
        request.user = AnonymousUser()
        ip_address = self.get_ident(request)
        validated_token = self.get_validated_token(token)
        user = self.get_user(validated_token, ip_address)
        request.user = user
        return user


class AfanJWTAuth(AfanJWTBaseAuthentication, HttpBearer):
    def authenticate(self, request: HttpRequest, token: str) -> Any:
        return self.jwt_authenticate(request, token)


class AfanJWTAuth2(AfanJWTBaseAuthentication, HttpBearer):
    def __call__(self, request: HttpRequest) -> Optional[Any]:
        headers = request.headers
        auth_value = headers.get(self.header)
        if not auth_value:
            return self.authenticate(request, None)
        parts = auth_value.split(" ")

        if parts[0].lower() != self.openapi_scheme:
            return self.authenticate(request, None)
        token = " ".join(parts[1:])
        return self.authenticate(request, token)

    def authenticate(self, request: HttpRequest, token: Optional[str]) -> Any:
        try:
            return self.jwt_authenticate(request, token)
        except Exception as e:
            return AnonymousUser()
