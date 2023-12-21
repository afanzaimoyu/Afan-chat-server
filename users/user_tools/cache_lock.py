import time
import uuid
from functools import wraps

from django.core.cache import caches

from users.exceptions.chat import Business_Error


class CacheLock:
    def __init__(self, cache_config='default', expires=60, wait_timeout=10):
        self.cache = caches[cache_config]
        self.expires = expires
        self.wait_timeout = wait_timeout

    def get_lock(self, lock_key):
        wait_timeout = self.wait_timeout
        identifier = str(uuid.uuid4())
        while wait_timeout >= 0:
            if self.cache.add(lock_key, identifier, self.expires):
                return identifier
            wait_timeout -= 1
            time.sleep(1)
        raise Business_Error(detail="请求太频繁了", code=-3)

    def release_lock(self, lock_key, identifier):
        # 释放cache锁
        lock_value = self.cache.get(lock_key)
        if lock_value == identifier:
            self.cache.delete(lock_key)


lock = CacheLock(cache_config='item_cache')


def distribute_item(func):
    @wraps(func)
    def wrapper(*args, **kwargs):
        lock_key = "_".join(map(str, args[1:]))  # 具体的lock_key要根据调用时传的参数而定
        identifier = lock.get_lock(lock_key)
        try:
            result = func(*args,idempotent=lock_key, **kwargs)
        finally:
            lock.release_lock(lock_key, identifier)

    return wrapper
