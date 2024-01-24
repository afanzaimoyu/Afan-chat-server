from typing import List

from ninja import Query
from ninja_extra import api_controller, http_get, http_delete, http_post, http_put
from ninja_extra.permissions import IsAuthenticated
from pydantic import Field

from chat.member_resp import MemberResp, ChatMemberListResp, IdResp, ChatMemberResp
from chat.room_member_req import IdInput, GroupAddReq, MemberAddReq, MemberDelReq, MemberExitReq, AdminAddReq, \
    AdminRevokeReq, MemberReq, IdsInput

from users.user_tools.cht_jwt_uthentication import AfanJWTAuth, AfanJWTAuth2


@api_controller("/room/public", tags=["聊天室相关公共接口"], auth=AfanJWTAuth2())
class RoomPublicController:
    @http_get("/group", description="群组详情", response=MemberResp)
    def group_detail(self, request, id_input: Query[IdsInput]):
        return id_input.get_group_detail(request.user)

    @http_get("/group/member/page", description="群成员列表",
              response=ChatMemberResp)
    def get_member_page(self, member_page: Query[MemberReq]):
        return member_page.get_member_page()


@api_controller("/room", tags=["聊天室相关接口"], auth=AfanJWTAuth(), permissions=[IsAuthenticated])
class RoomController:

    @http_get("/group/member/list", description="房间内的所有群成员列表-@专用", response=List[ChatMemberListResp])
    def get_member_list(self, id_input: Query[IdInput]):
        return id_input.get_member_list()

    @http_delete("/group/member", description="移除成员")
    def del_member(self, request, delete_input: MemberDelReq):
        delete_input.delete_member(request.user)

    @http_delete("/group/member/exit", description="退出群聊")
    def exit_group(self, request, delete_input: MemberExitReq):
        delete_input.exit_group(request.user)
        return True

    @http_post("/group", description="新增群组")
    def add_group(self, add_input: GroupAddReq):
        room_id = add_input.add_group()
        return dict(id=room_id)

    @http_post("/group/member", description="邀请好友")
    def add_member(self, request, add_input: MemberAddReq):
        add_input.add_members(request.user)

    @http_put("/group/admin", description="添加管理员")
    def add_admin(self, request, add_input: AdminAddReq):
        add_input.add_admin(request.user)
        return True

    @http_delete("/group/admin", description="撤销管理员")
    def revoke_admin(self, request, delete_input: AdminRevokeReq):
        delete_input.revoke_admin(request.user)
        return True
