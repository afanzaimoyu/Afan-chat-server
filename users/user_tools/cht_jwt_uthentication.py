from typing import Type, Any

from django.contrib.auth import get_user_model
from django.contrib.auth.models import AbstractUser, AnonymousUser
from django.http import HttpRequest
from django.utils.translation import gettext_lazy as _
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

    def get_user(self, validated_token) -> Type[AbstractUser]:
        """
        Attempts to find and return a user using the given validated token.
        """
        try:
            user_id = validated_token[api_settings.USER_ID_CLAIM]
        except KeyError as e:
            raise InvalidToken(
                _("Token contained no recognizable user identification")
            ) from e

        try:
            user = self.user_model.objects.get(**{api_settings.USER_ID_FIELD: user_id})
        except self.user_model.DoesNotExist as e:
            raise AuthenticationFailed(_("User not found")) from e

        if not user.is_active:
            raise AuthenticationFailed(_("User is inactive"))

        return user

    def jwt_authenticate(self, request: HttpRequest, token: str) -> Type[AbstractUser]:
        request.user = AnonymousUser()
        validated_token = self.get_validated_token(token)
        user = self.get_user(validated_token)
        request.user = user
        return user


class AfanJWTAuth(AfanJWTBaseAuthentication, HttpBearer):
    def authenticate(self, request: HttpRequest, token: str) -> Any:
        return self.jwt_authenticate(request, token)
