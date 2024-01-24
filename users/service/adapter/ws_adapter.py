# _*_ coding: utf-8 _*_
from users.domain.enums.ws_enums.base_resp import WSBaseResp
from users.domain.enums.ws_enums.resp_type_enum import WSRespTypeEnum
from users.domain.vo.response.ws.chat_member_resp import ChatMemberResp
from users.domain.vo.response.ws.online_offline import WSOnlineOfflineNotify
from users.models import CustomUser


# @Author       :   <a href="https://github.com/afanzaimoyu">afan</a>
# @Time         :   2024/1/23
# @Description  :   None
class WSAdapter:
    @staticmethod
    def get_login_url(url: str) -> dict:
        return WSBaseResp(
            type=WSRespTypeEnum.LOGIN_URL.enum_type,
            data=WSRespTypeEnum.LOGIN_URL.data_class(loginUrl=url)
        ).dict(exclude_none=True)

    @staticmethod
    def build_invalidate_token_resp() -> dict:
        return WSBaseResp(
            type=WSRespTypeEnum.INVALIDATE_TOKEN.enum_type
        ).dict(exclude_none=True)

    @staticmethod
    def build_oline_offline_notify_resp(user) -> dict:
        return WSBaseResp(
            type=WSRespTypeEnum.ONLINE_OFFLINE_NOTIFY.enum_type,
            data=WSRespTypeEnum.ONLINE_OFFLINE_NOTIFY.data_class(
                changeList=[ChatMemberResp.from_orm(user)],
                onlineNum=CustomUser.objects.filter(is_active=1).count(),
            )
        ).dict(exclude_none=True)

    @staticmethod
    def build_login_success_resp(user) -> dict:
        return WSBaseResp(
            type=WSRespTypeEnum.LOGIN_SUCCESS.enum_type,
            data=WSRespTypeEnum.LOGIN_SUCCESS.data_class.from_orm(user)
        ).dict(exclude_none=True)

    @staticmethod
    def build_login_waiting_resp() -> dict:
        return WSBaseResp(
            type=WSRespTypeEnum.LOGIN_SCAN_SUCCESS.enum_type,
        ).dict(exclude_none=True)

