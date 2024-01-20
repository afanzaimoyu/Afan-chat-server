from django.core.exceptions import ImproperlyConfigured
from injector import Module, inject, Binder, singleton

from config.settings.base import env
from oss.oss_bucket.minio_bucket import MinioBucketFileService
from oss.oss_bucket.oss_bucket_service import OssBucketFileService
from oss.oss_type import OssType


class FileServiceModule(Module):
    @inject
    def configure(self, binder: Binder) -> None:
        ENABLE_OSS = env.bool("ENABLE_OSS", default=False)
        Type = env.str("TYPE", default="minio")
        if not ENABLE_OSS:
            raise ImproperlyConfigured("未开启OSS服务。请在您的环境中设置 ENABLE_OSS=True。")
        match Type:
            case OssType.MINIO.label:
                binder.bind(OssBucketFileService, to=MinioBucketFileService, scope=singleton)
            case _:
                raise ImproperlyConfigured("不支持的OSS服务类型。请在您的环境中设置 TYPE=minio。")

