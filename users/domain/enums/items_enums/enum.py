# _*_ coding: utf-8 _*_

# @Author       :   <a href="https://github.com/afanzaimoyu">afan</a>
# @Time         :   2024/1/23
# @Description  :   物品枚举
from enum import Enum

from users.domain.enums.items_enums.type_enum import ItemTypeEnum


class ItemEnum(Enum):
    MODIFY_NAME_CARD = (1, ItemTypeEnum.MODIFY_NAME_CARD, "改名卡")
    LIKE_BADGE = (2, ItemTypeEnum.BADGE, "爆赞徽章")
    REG_TOP10_BADGE = (3, ItemTypeEnum.BADGE, "前十注册徽章")
    REG_TOP100_BADGE = (4, ItemTypeEnum.BADGE, "前100注册徽章")
    PLANET = (5, ItemTypeEnum.BADGE, "知识星球")
    CONTRIBUTOR = (6, ItemTypeEnum.BADGE, "代码贡献者")

    def __init__(self, value, item_type, description):
        self.value = value
        self.item_type = item_type
        self.description = description
