from django.contrib.auth.models import Group
from django.core.management.base import BaseCommand
from django.db import IntegrityError

from chat.models import Room, RoomGroup
from users.models import ItemConfig,CustomUser


class Command(BaseCommand):
    help = '初始化数据'

    def handle(self, *args, **options):
        try:
            # 初始化group
            group_data = [
                {"id": 1, "name": '超级管理员'}, {"id": 2, "name": '群聊管理员'}, {"id": 3, "name": '群聊成员'}]
            for group in group_data:
                Group.objects.create(**group)

            # 初始化item
            item_data = [
                {'id': 1, 'item_type': 1, 'img': None,
                 'describe': '用户可以使用改名卡，更改自己的名字,afanchat名称全局唯一，快抢订你的专属昵称吧'},
                {'id': 2, 'item_type': 2, 'img': 'https://cdn-icons-png.flaticon.com/128/1533/1533913.png',
                 'describe': '爆赞徽章，单条消息被点赞超过10次，即可获得'},
                {'id': 3, 'item_type': 2, 'img': 'https://cdn-icons-png.flaticon.com/512/6198/6198527.png',
                 'describe': '前10名注册的用户才能获得的专属徽章'},
                {'id': 4, 'item_type': 2, 'img': 'https://cdn-icons-png.flaticon.com/512/10232/10232583.png',
                 'describe': '抹茶聊天前100名注册的用户才能获得的专属徽章'},
                {'id': 5, 'item_type': 2, 'img': 'https://minio.mallchat.cn/mallchat/%E8%B4%A1%E7%8C%AE%E8%80%85.png',
                 'describe': '项目contributor专属徽章'}
            ]
            for item in item_data:
                ItemConfig.objects.create(**item)

            CustomUser.objects.create(id=1, name='系统消息',
                                avatar='http://mms1.baidu.com/it/u=1979830414,2984779047&fm=253&app=138&f=JPEG&fmt=auto&q=75?w=500&h=500')
            Room.objects.create(id=1, type=1, hot_flag=1)
            RoomGroup.objects.create(id=1, room_id=1, name='抹茶全员群',
                                     avatar='https://mallchat.cn/assets/logo-e81cd252.jpeg')

            self.stdout.write(self.style.SUCCESS('初始化数据成功'))
        except IntegrityError as exc:
            self.stdout.write(self.style.ERROR(f'初始化数据失败，错误信息：{exc}'))
