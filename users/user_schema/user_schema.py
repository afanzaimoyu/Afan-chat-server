from datetime import datetime
from typing import Any, List, Optional

from django.core.cache import cache
from django.db import transaction
from ninja_extra import service_resolver
from ninja_extra.controllers import RouteContext
from ninja_extra.exceptions import ParseError, ValidationError
from ninja_extra.shortcuts import get_object_or_exception
from ninja_schema import ModelSchema, Schema, model_validator
from users.exceptions.chat import Business_Error
from users.models import CustomUser, ItemConfig, Blacklist
from pydantic import model_validator as m, Field

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
    item_id: int = Field(alias="badgeId")

    @model_validator("item_id")
    def validate_item(cls, value_data):
        context: RouteContext = service_resolver(RouteContext)
        user = context.request.user
        if value_data == 1:
            raise Business_Error(detail="只有徽章才能佩戴", code=0)
        elif value_data not in user.get_user_badges:
            raise Business_Error(detail="您还没有这个徽章，快去获得吧", code=0)
        return value_data


class BlackInput(Schema):
    uid: int

    @model_validator("uid")
    def validate_uid(cls, value_data):
        context: RouteContext = service_resolver(RouteContext)
        user = context.request.user
        if value_data == user.id:
            raise Business_Error(detail="不能拉黑自己", code=0)
        elif Blacklist.is_blacklisted(2, value_data):
            raise Business_Error(detail="已经拉黑了", code=0)
        elif not CustomUser.objects.filter(id=value_data).exists():
            raise Business_Error(detail="用户不存在", code=0)
        return value_data

    @transaction.atomic
    def black_user(self) -> Any:
        black_user = get_object_or_exception(CustomUser, id=self.uid)
        Blacklist.objects.create(type=2, target=self.uid)
        # 拉黑ip
        create_ip = black_user.ip_info.get('createIp')
        update_ip = black_user.ip_info.get('updateIp')

        for ip in set(filter(None, [create_ip, update_ip])):
            Blacklist.objects.create(type=1, target=ip)


class SummeryInfoReq(Schema):
    class InfoReq(Schema):
        uid: int
        lastModifyTime: Optional[datetime] = Field(None, description="最后一次更新用户信息时间")

    reqList: List[InfoReq] = Field(..., description="请求列表", max_items=50)

    def get_summery_user_info(self):
        uid_list = [req.uid for req in self.reqList]
        users = CustomUser.objects.filter(id__in=uid_list)
        user_dict = {user.id: user for user in users}
        summery_info_list = []
        for req in self.reqList:
            user = user_dict.get(req.uid)
            if not user:
                continue
            print(req.lastModifyTime)
            if not req.lastModifyTime or user.update_time < req.lastModifyTime:
                user.locPlace = user.ip_info.get('updateIpDetail', {}).get('city') if user.ip_info else None
                user.needRefresh = True
                resp = SummeryInfoResp.from_orm(user).dict(exclude_none=True)
            else:
                resp = SummeryInfoResp(id=user.id, needRefresh=False).dict(exclude_none=True)
            summery_info_list.append(resp)
        return summery_info_list


class SummeryInfoResp(Schema):
    uid: int = Field(alias="id")
    name: Optional[str] = Field(None, description="昵称")
    avatar: Optional[str] = Field(None, description="头像")
    locPlace: Optional[str] = Field(None, description="地区")
    wearingItemId: Optional[int] = Field(None, alias="item_id", description="佩戴的徽章id")
    needRefresh: bool = Field(True, description="是否需要刷新")


class ItemInfoReq(Schema):
    class ItemInfo(Schema):
        itemId: int
        lastModifyTime: Optional[datetime] = Field(None, description="最近一次更新徽章信息时间")

    reqList: List[ItemInfo] = Field(..., description="请求列表", max_items=50)

    def get_item_info(self):
        item_list = [req.itemId for req in self.reqList]
        items = ItemConfig.objects.filter(id__in=item_list)
        item_dict = {item.id: item for item in items}
        summery_info_list = []
        for req in self.reqList:
            item = item_dict.get(req.itemId)
            if not item:
                continue
            if not req.lastModifyTime or item.update_time > req.lastModifyTime:
                item.last_modify_time = datetime.now()
                item.needRefresh = True
                resp = ItemInfoResp.from_orm(item).dict(exclude_none=True)
            else:
                resp = ItemInfoResp(id=item.id, needRefresh=False).dict(exclude_none=True)
            summery_info_list.append(resp)
        return summery_info_list


class ItemInfoResp(Schema):
    itemId: int = Field(alias="id")
    img: Optional[str] = Field(None, description="徽章图片")
    describe: Optional[str] = Field(None, description="徽章描述")
    needRefresh: Optional[bool] = Field(True, description="是否需要刷新")
