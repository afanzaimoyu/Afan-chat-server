import hashlib
import random
import secrets
import string
import time
import uuid


def generate_login_code(ip):
    result = ""
    login_code = secrets.randbelow(10 ** 32)
    timestamp = str(int(time.time()))

    # 将 IP 地址、登录码和时间戳连接起来
    combined_info = f"{ip}{uuid.uuid4()}{login_code}{timestamp}"

    # 使用哈希算法（这里使用 SHA-256）生成固定长度的摘要
    hashed_info = hashlib.sha256(combined_info.encode()).hexdigest()

    final_login_code = hashed_info[:32]
    for char in final_login_code:
        if char.isalpha():  # 检查是否是字母
            # 将字母转换为对应的 ASCII 值，并追加到结果字符串
            result += str(ord(char))
        else:
            # 非字母字符保持不变
            result += char
    print(final_login_code)
    result = int(result[:32])

    return result
