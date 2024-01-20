from datetime import timedelta
from pathlib import Path
from typing import Iterator
from uuid import uuid4
from django.utils import timezone
from minio import Minio
from minio.datatypes import PostPolicy, Object
from urllib3 import BaseHTTPResponse

from config.settings.base import env
from oss.domain.ossreq import OssReq
from oss.domain.ossresp import OssResp
from oss.oss_bucket.oss_bucket_service import OssBucketFileService


class MinioBucketFileService(OssBucketFileService):
    def __init__(self) -> None:
        self.endpoint = env.str('ENDPOINT', default='127.0.0.1:9000')
        self.bucket_name = env.str('BUCKET_NAME', default='afanchat')
        access_key = env.str('ACCESS_KEY')
        secret_key = env.str('SECRET_KEY')
        self.minio_client = Minio(
            endpoint=self.endpoint,
            access_key=access_key,
            secret_key=secret_key,
            secure=False,  # HTTPS
        )

    def list_buckets(self) -> list:
        """
        获取所有的bucket
        Returns:
            list of bucket
        """
        return self.minio_client.list_buckets()

    def bucket_exists(self, bucket_name: str) -> bool:
        """
        判断bucket是否存在
        Args:
            bucket_name: bucket名称

        Returns:
            bool 是否存在
        """
        return self.minio_client.bucket_exists(bucket_name)

    def make_bucket(self, bucket_name: str) -> None:
        """
        创建bucket
        Args:
            bucket_name: bucket名称
        """
        if not self.bucket_exists(bucket_name):
            return self.minio_client.make_bucket(bucket_name)

    def remove_bucket(self, bucket_name: str) -> None:
        """
        删除一个空桶 如果存储桶存在对象不为空时，删除会报错。
        Args:
            bucket_name: bucket名称
        """
        return self.minio_client.remove_bucket(bucket_name)

    def get_pre_signed_object_url(self, req: OssReq) -> OssResp:
        """
        返回临时带签名、过期时间一天、PUT请求方式的访问URL
        Args:
            req: OssReq

        Returns:

        """
        absolute_url = self.generate_auto_path(req) if req.authPath else req.filePath + '/' + req.fileName
        url = self.minio_client.presigned_put_object(
            bucket_name=self.bucket_name,
            object_name=absolute_url,
            expires=timedelta(days=1),
        )
        return OssResp(
            uploadUrl=url,
            downloadUrl=self.get_download_url(self.bucket_name, absolute_url),
        )

    def get_download_url(self, bucket_name: str, path_file: str) -> str:
        """
        获取下载地址
        Args:
            bucket_name: 桶名
            path_file: 文件路径
        Returns:
            下载地址
        """
        return f"{self.endpoint}/{bucket_name}{path_file}"

    def get_object(self, bucket_name: str, oss_file_path: str) -> BaseHTTPResponse:
        """
        get_object接口用于获取某个文件（Object）。此操作需要对此Object具有读权限。
        Args:
            bucket_name: 桶名
            oss_file_path: Oss文件路径
        Returns:
            文件内容
        """
        return self.minio_client.get_object(bucket_name, oss_file_path)

    def list_objects(self, bucket_name: str, recursive: bool) -> Iterator[Object]:
        """
        列出桶内所有文件
        Args:
            bucket_name: 桶名
            recursive: 是否递归查询

        Returns:
            文件列表
        """
        return self.minio_client.list_objects(bucket_name, recursive=recursive)

    def generate_auto_path(self, req: OssReq) -> str:
        """
        生成随机文件名，防止重复
        Args:
            req:

        Returns:
            文件名
        """
        uid = str(req.uid if req.uid else "000000")
        uuid = str(uuid4())
        suffix = Path(req.fileName).suffix
        year_and_month = timezone.now().strftime('%Y%m')
        return f"{req.filePath}/{year_and_month}/{uid}/{uuid}{suffix}"

    def get_pre_signed_post_form_data(self, bucket_name: str, file_name: str) -> dict[str, str]:
        """
        获取带签名的临时上传元数据对象，前端可获取后，直接上传到Minio
        Args:
            bucket_name: 桶名
            file_name: 文件名

        Returns:
            带签名的临时上传元数据对象
        """
        # 为存储桶创建一个上传策略，过期时间为7天
        policy = PostPolicy(bucket_name, timezone.now() + timedelta(days=7))
        # 添加Content-Type以"image/"开头，表示只能上传照片
        policy.add_starts_with_condition("Content-Type", "image/")
        # 设置一个参数key，值为上传对象的名称
        policy.add_equals_condition("key", file_name)
        # 设置上传文件的大小 64kiB to 10MiB.
        policy.add_content_length_range_condition(64 * 1024, 10 * 1024 * 1024)
        return self.minio_client.presigned_post_policy(policy)
