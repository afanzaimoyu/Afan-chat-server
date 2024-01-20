from typing import Optional

from ninja_schema import Schema
from pydantic import Field


class OssReq(Schema):
    """
    上传url请求入参
    """
    filePath: str = Field(..., title="文件存储路径")
    fileName: str = Field(..., title="文件名")
    uid: Optional[int] = Field(title="用户id")
    authPath: bool = Field(True, title="自动生成地址")
