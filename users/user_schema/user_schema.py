from typing import Any, List

from django.db import transaction
from ninja_extra import service_resolver
from ninja_extra.controllers import RouteContext
from ninja_extra.exceptions import ParseError, ValidationError
from ninja_schema import ModelSchema, Schema, model_validator
from users.exceptions.chat import Business_Error
from users.models import CustomUser, ItemConfig
from pydantic import model_validator as m

from users.user_tools.cache_lock import distribute_item


class UserSchemaMix(Schema):
    @transaction.atomic
    def update(self, instance: Any, **kwargs: Any) -> Any:
        if not instance:
            raise Exception("Instance is required")

        data = self.dict(exclude_none=True)
        data.update(kwargs)
        for attr, value in data.items():
            setattr(instance, attr, value)
        instance.save()

        return instance

    @distribute_item
    @transaction.atomic
    def distribute_items(self, user_instance, item_id, idempotent_enum, business_id, idempotent=None):
        """
        发放物品功能
            如需默认佩戴，子类继承该方法进行修改
        Args:
            user_instance: 用户实例
            item_id: 要发放的物品id
            idempotent_enum: 幂等类型  1:UID  2:消息id
            business_id: 业务唯一标识
            idempotent: 幂等键 ！！无需传入，装饰器自动组装！！

        Returns:

        """
        # 检查是否已发放过
        if user_instance.userbackpack_set.filter(idempotent=idempotent).exists():
            return
        # 检查物品是否存在
        if not ItemConfig.objects.filter(id=item_id).exists():
            return
        # 检查用户是否已经有相同的徽章
        if item_id in user_instance.get_user_badges:
            return
        # 发放物品
        user_instance.backpacks.add(item_id,through_defaults={"idempotent":idempotent,})
        return user_instance


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


class ModifyNameInput(UserSchemaMix):
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

        updated_instance = super().update(instance, **kwargs)

        user_back = updated_instance.get_oldest_rename_card()
        if user_back:
            user_back.status = 1
            user_back.save()
        return updated_instance


class BadgesOutSchema(Schema):
    id: int
    img: str
    describe: str
    obtain: int
    wearing: int


class WearingBadgeInput(UserSchemaMix):
    item_id: int

    @model_validator("item_id")
    def validate_item(cls, value_data):
        context: RouteContext = service_resolver(RouteContext)
        user = context.request.user
        if value_data == 1:
            raise Business_Error(detail="只有徽章才能佩戴", code=0)
        elif value_data not in user.get_user_badges:
            raise Business_Error(detail="您还没有这个徽章，快去获得吧", code=0)
        return value_data
