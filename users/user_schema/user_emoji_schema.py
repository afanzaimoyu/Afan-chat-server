from ninja_extra import service_resolver
from ninja_extra.controllers import RouteContext
from ninja_schema import Schema, model_validator
from pydantic import Field

from users.exceptions.chat import Business_Error
from users.models import UserEmoji


class UserEmojiResp(Schema):
    id: int = Field(..., description="表情id")
    expressionUrl: str = Field(..., alias="expression_url", description="表情链接")


class IdReq(Schema):
    id: int = Field(..., description="表情id")

    @model_validator("id")
    def validate_id(cls, value_data):
        context: RouteContext = service_resolver(RouteContext)
        cls.user = context.request.user
        if not UserEmoji.objects.filter(id=value_data, user=cls.user).exists():
            raise Business_Error("表情不存在哦~~", code=0)
        return value_data

    def delete_emoji(self):
        UserEmoji.objects.filter(id=self.id).update(delete_status=UserEmoji.Status.DELETED)


class IdResp(Schema):
    id: int = Field(..., description="表情id")


class UserEmojiReq(Schema):
    expressionUrl: str = Field(..., description="新增的表情url")

    @model_validator("expressionUrl")
    def validate_expression_url(cls, value_data):
        context: RouteContext = service_resolver(RouteContext)
        cls.user = context.request.user

        emoji_num = UserEmoji.objects.filter(user=cls.user).count()
        if emoji_num >= 30:
            raise Business_Error("最多只能添加30个表情哦~~", code=0)
        if UserEmoji.objects.filter(user=cls.user, expression_url=value_data).exists():
            raise Business_Error("表情已经存在了哦~~", code=0)

        return value_data

    def insert_emoji(self):
        return UserEmoji.objects.create(expression_url=self.expressionUrl, user=self.user)
