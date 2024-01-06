from django.db import models

from users.models import CustomUser


# Create your models here.
class Room(models.Model):
    class Type(models.IntegerChoices):
        GROUP_CHAT = 1, "群聊"
        ONE_ON_ONE_CHAT = 2, "单聊"

    class HotFlag(models.IntegerChoices):
        NO = 0, "否"
        YES = 1, "是"

    type = models.IntegerField(choices=Type.choices, verbose_name="房间类型")
    hot_flag = models.IntegerField(default=0, choices=HotFlag.choices, verbose_name="是否全员展示")
    active_time = models.DateTimeField(null=True, blank=True,
                                       verbose_name="群最后消息的更新时间（热点群不需要写扩散，只更新这里）")
    last_msg_id = models.BigIntegerField(null=True, verbose_name="会话中的最后一条消息id")
    ext_json = models.JSONField(null=True, blank=True, verbose_name="额外信息（根据不同类型房间有不同存储的东西）")
    create_time = models.DateTimeField(auto_now_add=True)
    update_time = models.DateTimeField(auto_now=True)

    class Meta:
        verbose_name = "房间表"
        db_table = "chat_room"
        indexes = [
            models.Index(fields=['create_time']),
            models.Index(fields=['update_time']),
        ]

    def is_hot_room(self):
        return self.hot_flag == self.HotFlag.YES

    def is_room_friend(self):
        return self.type == self.Type.ONE_ON_ONE_CHAT

    def is_room_group(self):
        return self.type == self.Type.GROUP_CHAT

    def refresh_active_time(self, msg_id, msg_time):
        self.last_msg_id = msg_id
        self.active_time = msg_time
        self.save(update_fields=['last_msg_id', "active_time"])


class RoomFriend(models.Model):
    class Status(models.IntegerChoices):
        NORMAL = 0, "正常"
        DISABLE = 1, "禁止"

    room = models.OneToOneField(Room, on_delete=models.CASCADE, verbose_name="房间id")
    uid1 = models.ForeignKey(CustomUser, on_delete=models.CASCADE, related_name='small_user', verbose_name='id小的用户')
    uid2 = models.ForeignKey(CustomUser, on_delete=models.CASCADE, related_name='big_user', verbose_name='id大的用户')
    room_key = models.CharField(max_length=64, unique=True, verbose_name="房间key由两个uid拼接，先做排序uid1_uid2")
    status = models.IntegerField(choices=Status.choices, verbose_name="房间状态 0正常 1禁用(删好友了禁用)")
    create_time = models.DateTimeField(auto_now_add=True)
    update_time = models.DateTimeField(auto_now=True)

    class Meta:
        verbose_name = "单聊房间表"
        db_table = "chat_room_friend"
        indexes = [
            models.Index(fields=['room']),
            models.Index(fields=['create_time']),
            models.Index(fields=['update_time']),
        ]


class RoomGroup(models.Model):
    class Delete(models.IntegerChoices):
        NORMAL = 0, '正常'
        DELETED = 1, '删除'

    room = models.OneToOneField(Room, on_delete=models.CASCADE, verbose_name="房间id")
    name = models.CharField(max_length=16, verbose_name="群名称")
    avatar = models.CharField(max_length=256, verbose_name="群头像")
    ext_json = models.JSONField(null=True, blank=True, verbose_name="额外信息（根据不同类型房间有不同存储的东西）")
    delete_status = models.IntegerField(default=0, choices=Delete.choices, verbose_name="逻辑删除(0-正常,1-删除)")
    create_time = models.DateTimeField(auto_now_add=True)
    update_time = models.DateTimeField(auto_now=True)

    class Meta:
        verbose_name = "群聊房间表"
        db_table = "chat_room_group"
        indexes = [
            models.Index(fields=['room']),
            models.Index(fields=['create_time']),
            models.Index(fields=['update_time']),
        ]


class GroupMember(models.Model):
    class Role(models.IntegerChoices):
        GROUP_LEADER = 1, "群主"
        ADMINISTRATOR = 2, "管理员"
        ORDINARY_MEMBERS = 3, "普通成员"

    group = models.ForeignKey(RoomGroup, on_delete=models.CASCADE, verbose_name="群组")
    uid = models.ForeignKey(CustomUser, on_delete=models.CASCADE, related_name='group_member_user',
                            verbose_name='成员uid')
    role = models.IntegerField(verbose_name="成员角色 1群主 2管理员 3普通成员")
    create_time = models.DateTimeField(auto_now_add=True)
    update_time = models.DateTimeField(auto_now=True)

    class Meta:
        verbose_name = "群成员表"
        db_table = "chat_group_member"
        indexes = [
            models.Index(fields=['group', "role"]),
            models.Index(fields=['create_time']),
            models.Index(fields=['update_time']),
        ]


class Contact(models.Model):
    uid = models.ForeignKey(CustomUser, on_delete=models.CASCADE, related_name='chat_contact_user',
                            verbose_name='uid')
    room = models.ForeignKey(Room, on_delete=models.CASCADE, verbose_name="房间id")
    read_time = models.DateTimeField(null=True, blank=True, verbose_name="阅读到的时间")
    active_time = models.DateTimeField(null=True, blank=True,
                                       verbose_name="会话内消息最后更新的时间(只有普通会话需要维护，全员会话不需要维护)")
    last_msg_id = models.BigIntegerField(null=True, verbose_name="会话最新消息id")
    create_time = models.DateTimeField(auto_now_add=True)
    update_time = models.DateTimeField(auto_now=True)

    class Meta:
        verbose_name = "会话列表"
        db_table = "chat_contact"
        unique_together = ['uid', 'room']
        indexes = [
            models.Index(fields=['room', "read_time"]),
            models.Index(fields=['create_time']),
            models.Index(fields=['update_time']),
        ]

    @staticmethod
    def refresh_or_create_active_time(room_id, member_uid_list, msg_id, active_time):
        for uid in member_uid_list:
            Contact.objects.update_or_create(room_id=room_id, uid_id=uid, last_msg_id=msg_id, active_time=active_time)


class Message(models.Model):
    class Status(models.IntegerChoices):
        NORMAL = 0, "正常"
        DELETE = 1, "删除"

    class MessageTypeEnum(models.IntegerChoices):
        TEXT = 1, "正常消息"
        RECALL = 2, "撤回消息"
        IMG = 3, "图片"
        FILE = 4, "文件"
        SOUND = 5, "语音"
        VIDEO = 6, "视频"
        EMOJI = 7, "表情"
        SYSTEM = 8, "系统消息"

    room = models.ForeignKey(Room, on_delete=models.CASCADE, verbose_name="会话表id")
    from_user = models.ForeignKey(CustomUser, on_delete=models.CASCADE, related_name='message_sender',
                                  verbose_name='消息发送者')
    content = models.CharField(max_length=1024, null=True, blank=True, verbose_name="消息内容")
    reply_msg_id = models.BigIntegerField(null=True, blank=True, verbose_name="回复的消息内容")
    status = models.IntegerField(choices=Status.choices, verbose_name="消息状态 0正常 1删除")
    gap_count = models.IntegerField(null=True, blank=True, verbose_name="与回复的消息间隔多少条")
    type = models.IntegerField(default=1, choices=MessageTypeEnum.choices, verbose_name="消息类型 1正常文本 2.撤回消息")
    extra = models.JSONField(null=True, blank=True, verbose_name="扩展信息")
    create_time = models.DateTimeField(auto_now_add=True)
    update_time = models.DateTimeField(auto_now=True)

    class Meta:
        verbose_name = "消息表"
        db_table = "chat_message"
        indexes = [
            models.Index(fields=['room']),
            models.Index(fields=['from_user']),
            models.Index(fields=['create_time']),
            models.Index(fields=['update_time']),
        ]

    def get_GapCount(self, reply_msg_id):
        return Message.objects.filter(room_id=self.room_id, id__gt=reply_msg_id, id__lt=self.id).count()


class SecureInvokeRecord(models.Model):
    class Status(models.IntegerChoices):
        NORMAL = 1, "待执行"
        DELETE = 2, "已失败"

    secure_invoke_json = models.JSONField(verbose_name='请求快照参数json')
    status = models.SmallIntegerField(verbose_name='状态', choices=Status.choices)
    next_retry_time = models.DateTimeField(verbose_name='下一次重试的时间')
    retry_times = models.IntegerField(verbose_name='已经重试的次数')
    max_retry_times = models.IntegerField(verbose_name='最大重试次数')
    fail_reason = models.TextField(verbose_name='执行失败的堆栈', blank=True, null=True)
    create_time = models.DateTimeField(auto_now_add=True, verbose_name='创建时间')
    update_time = models.DateTimeField(auto_now=True, verbose_name='修改时间')

    class Meta:
        db_table = 'secure_invoke_record'
        indexes = [
            models.Index(fields=['next_retry_time']),
        ]
        verbose_name = '本地消息表'
