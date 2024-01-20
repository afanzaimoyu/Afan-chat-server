from ninja_schema import Schema
from pydantic import Field


class OssResp(Schema):
    uploadUrl: str = Field(..., title="上传地址")
    downloadUrl: str = Field(..., title="下载地址")

