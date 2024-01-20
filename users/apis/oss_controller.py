from ninja import Query
from ninja_extra import api_controller, http_get
from ninja_extra.permissions import IsAuthenticated

from oss.domain.ossresp import OssResp
from oss.oss_bucket.oss_bucket_service import OssBucketFileService
from users.user_schema.oss_schema import UploadUrlReq
from users.user_tools.cht_jwt_uthentication import AfanJWTAuth


@api_controller("/oss", tags=["oss控制层"], auth=AfanJWTAuth(), permissions=[IsAuthenticated])
class OssController:
    def __init__(self, file_service: OssBucketFileService):
        self.file_service = file_service

    @http_get("/upload/url", description="获取临时上传链接", response=OssResp)
    def get_upload_url(self, request, upload_url_req: Query[UploadUrlReq]):
        return upload_url_req.get_upload_url(request.user.id, self.file_service)
