from typing import Any, List

from django.db import transaction
from ninja_extra import service_resolver
from ninja_extra.controllers import RouteContext
from ninja_extra.exceptions import ParseError, ValidationError
from ninja_schema import ModelSchema, Schema, model_validator
from users.exceptions.chat import Business_Error
from users.models import CustomUser
from pydantic import model_validator as m


class UserInfoSchema(ModelSchema):
    modifyNameChance: int = -1

    @m(mode='after')
    def add_name_change(self):
        context: RouteContext = service_resolver(RouteContext)
        user = context.request.user
        self.modifyNameChance = user.get_rename_card().count()
        return self

    class Config:
        model = CustomUser
        include = ("id", "name", "sex", "avatar",)


class ModifyNameInput(Schema):
    name: str

    @model_validator("name")
    def lenth_field(cls, value_data):
        context: RouteContext = service_resolver(RouteContext)
        user = context.request.user
        if len(value_data) >= 6:
            raise ValidationError(detail="名字不要超过6个字符")
        elif CustomUser.objects.filter(name__exact=value_data).exists():
            raise Business_Error(detail="名字重复了", code=0)
        elif not user.get_rename_card().exists():
            raise Business_Error(detail="改名卡不够了，等待下次活动吧", code=0)
        return value_data

    @transaction.atomic
    def update(self, instance: Any, **kwargs: Any) -> Any:
        if not instance:
            raise Exception("Instance is required")

        data = self.dict(exclude_none=True)
        data.update(kwargs)
        for attr, value in data.items():
            setattr(instance, attr, value)
        print(instance)

        user_back = instance.get_oldest_rename_card()
        user_back.status = 1
        user_back.save()
        instance.save()

        return instance
