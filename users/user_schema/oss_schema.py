from django.db import models
from ninja_schema import Schema
from pydantic import Field

from oss.domain.ossreq import OssReq
from oss.domain.ossresp import OssResp
from users.exceptions.chat import Business_Error


class OssSceneEnum(models.IntegerChoices):
    CHAT = 1, "/chat"
    EMOJI = 2, "/emoji"


class UploadUrlReq(Schema):
    fileName: str = Field(..., description='文件名（带后缀）')
    scene: int = Field(..., description="上传场景1.聊天室,2.表情包", le=2, ge=1)

    def get_upload_url(self, uid: int, file_service) -> OssResp:
        sceneEnum = OssSceneEnum(self.scene)
        assert sceneEnum is not None, Business_Error("上传场景不存在")
        oss_req = OssReq(
            filePath=sceneEnum.label,
            fileName=self.fileName,
            uid=uid,
        )
        return file_service.get_pre_signed_object_url(oss_req)

