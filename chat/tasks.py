# from celery import shared_task
#
#
# @shared_task(ignore_result=True)
# def send_new_message(message):
#     # TODO 优化任务过多的问题    任务队列满了，就不再发送任务
#     # TODO 发送失败，查询是channels layer 的原因 换channels-redis也许可以
#     # 参考 : https://stackoverflow.com/questions/57595453/getting-django-channel-access-in-celery-task
#     try:
#         print("发送消息")
#         channel_layer = get_channel_layer()
#         async_to_sync(channel_layer.group_send)("chat_group", message)
#     except Exception as e:
#         print("error", e)