import hashlib
import secrets
import time
import uuid
from datetime import datetime
from typing import cast, Dict

from django.contrib.auth.base_user import AbstractBaseUser
from django.contrib.auth.models import AbstractUser
from ninja_jwt.tokens import RefreshToken
from ninja_jwt.utils import token_error


def generate_login_code(ip):
    result = ""
    login_code = secrets.randbelow(10 ** 32)
    timestamp = str(int(time.time()))

    # 将 IP 地址、登录码和时间戳连接起来
    combined_info = f"{ip}{uuid.uuid4()}{login_code}{timestamp}"

    # 使用哈希算法（这里使用 SHA-256）生成固定长度的摘要
    hashed_info = hashlib.sha256(combined_info.encode()).hexdigest()[:32]

    return hashed_info


def extract_login_code_from_event_key(event_key: str) -> str:
    # 实现提取登录码的逻辑，根据实际情况修改
    return event_key.split("_")[1]


@token_error
def get_token(user: AbstractBaseUser) -> Dict:
    values = {}
    refresh = RefreshToken.for_user(user)
    refresh = cast(RefreshToken, refresh)
    values["refresh"] = str(refresh)
    values["access"] = str(refresh.access_token)
    return values


def timestamp_to_datetime(time_stamp: str):
    return datetime.fromtimestamp(int(time_stamp) / 1000)


def datetime_to_timestamp(date_time: datetime):
    return int(datetime.timestamp(date_time) * 1000)
