from celery import shared_task
from celery import shared_task
import requests
from users.models import CustomUser
from users.user_schema.ipinfo_schema import Ipinfo

"""
celery -A config.celery_app worker -l INFO -Q single_process_queue --concurrency=1
Celery -A config.celery_app -b "redis://127.0.0.1:6379/1" flower --address=127.0.0.1 --port=5555
Celery -A config.celery_app worker -l info -P eventlet
"""


def retry_on_failure(self, countdown=2, exc=None):
    try:
        raise self.retry(exc=exc, countdown=countdown)
    except self.MaxRetriesExceededError:
        print(f"Max retries exceeded for task {self.request.id}")


@shared_task(bind=True, max_retries=5, rate_limit='1/s', queue='single_process_queue')
def refresh_ip_detail_async(self, uid):
    user = CustomUser.objects.get(id=uid)
    user_ipinfo = user.ip_info
    if not user_ipinfo:
        return
    # 根据updateip和updateipdetail判断是否需要更新，
    # 如果updateipdetail中的ip和updateip中的ip相同，则不需要更新，不同或者updateipdetail为空，则需要更新

    if user_ipinfo.get("updateIp") == user_ipinfo.get("updateIpDetail",{}).get("ip"):
        return
    # 获取详细
    ipinfo = Ipinfo(**user_ipinfo)

    url = f"https://ip.taobao.com/outGetIpInfo?ip={ipinfo.updateIp}&accessKey=alibaba-inc"
    try:
        response = requests.get(url)
        response.raise_for_status()
        data = response.json()
        if data.get('data'):
            ipinfo.refresh_ip(data.get('data'))
            user.ip_info = ipinfo.dict()
            user.save(update_fields=['ip_info'])
            print(f"更新用户{user.id}的ip信息成功")
        else:  # 请求超过最大QPS
            retry_on_failure(self)
    except requests.exceptions.RequestException as exc:
        # 如果请求失败，等待2秒后重试
        retry_on_failure(self, countdown=2, exc=exc)
    # 数据保存失败，等待2秒后重试
