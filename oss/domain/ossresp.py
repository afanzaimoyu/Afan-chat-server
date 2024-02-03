from ninja_schema import Schema
from pydantic import Field, model_validator


class OssResp(Schema):
    uploadUrl: str = Field(..., title="上传地址")
    downloadUrl: str = Field(..., title="下载地址")

    @model_validator(mode="before")
    def to_https(cls, values: dict) -> dict:
        if isinstance(values, dict):
            values["uploadUrl"] = values["uploadUrl"].replace("http://", "https://")
            if values["downloadUrl"].startswith("http://"):
                values["downloadUrl"] = values["downloadUrl"].replace("http://", "https://")
            elif not values["downloadUrl"].startswith("https://"):
                values["downloadUrl"] = "https://" + values["downloadUrl"]
        return values
