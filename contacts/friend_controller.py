# from ninja.pagination import paginate
from ninja import Query
from ninja_extra import api_controller, http_get, http_post, paginate, http_put, http_delete
from ninja_extra.permissions import IsAuthenticated

from contacts.contacts_schema import CheckUserInput, ApplyInput, APPlyPageOut, CustomUserFriend, ApproveInput, \
    DeleteFriendInput
from contacts.models import UserFriend, UserApply
from contacts.utils.pagintion import NormalPagination, NormalPaginationResponseSchema, CursorPagination, \
    CursorPaginationResponseSchema
from users.user_tools.cht_jwt_uthentication import AfanJWTAuth


@api_controller("/user/friend", tags=["联系人模块"], auth=AfanJWTAuth(), permissions=[IsAuthenticated])
class ContactsController:
    @http_get("/check", description="批量判断是否是自己的好友")
    def check(self, request, uid_list: CheckUserInput):
        user = request.user
        friend_uids = UserFriend.objects.filter(uid=user.id).values_list('friend_id', flat=True)

        are_friends_list = uid_list.are_friends_list(friend_uids)

        return are_friends_list

    @http_get("/apply/page", description="好友申请列表", response=NormalPaginationResponseSchema[APPlyPageOut])
    @paginate(NormalPagination, page_size=50, wrapper_consumer=UserApply.is_to_read)
    def page(self, request):
        uid = request.user.id

        user_apply_query = UserApply.objects.filter(uid=uid).select_related('target').values(
            *[f.name for f in UserApply._meta.fields],
            'target_id', 'target__id', "target__name", "target__avatar"
        ).order_by("-create_time")

        return user_apply_query

    @http_get("/apply/unread", description="申请未读数")
    def unread(self, request):
        uid = request.user.id
        un_read_count = UserApply.objects.filter(target_id=uid, read_status=UserApply.ReadStatus.UNREAD).count()

        return {"unreadCount": un_read_count}

    @http_post("/apply", description="申请好友")
    def apply(self, request, apply_input: ApplyInput):
        uid = request.user.id
        apply_info = apply_input.dict()
        apply_info.update({'uid_id': uid, "type": UserApply.Type.ADD_FRIEND, "status": UserApply.Status.PENDING,
                           "read_status": UserApply.ReadStatus.UNREAD})
        UserApply.objects.create(**apply_info)

    @http_put("/apply", description="审批同意")
    def apply_approve(self, request, approve_input: ApproveInput):
        user = request.user
        approve_input.agree_to_the_application(user)
        return True

    @http_delete(description="删除好友")
    def delete_friend(self, request, uid: Query[DeleteFriendInput]):
        user = request.user
        uid.delete_friend(user)

        return True

    @http_get("/page", description="联系人列表", response=CursorPaginationResponseSchema[CustomUserFriend])
    @paginate(CursorPagination, mapper=UserFriend, cursor_column="id", select="friend")
    def friend_list(self, request):
        uid = request.user

        return {"&": {"uid": uid}}
