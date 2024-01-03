from django.db import models

from users.models import CustomUser


# Create your models here.
class UserApply(models.Model):
    class Status(models.IntegerChoices):
        PENDING = 1, '待审批'
        APPROVED = 2, '同意'

    class ReadStatus(models.IntegerChoices):
        UNREAD = 1, '未读'
        READ = 2, '已读'

    class Type(models.IntegerChoices):
        ADD_FRIEND = 1, '加好友'

    id = models.BigAutoField(primary_key=True, verbose_name='UserApply id')
    uid = models.ForeignKey(CustomUser, on_delete=models.CASCADE, related_name='applies_sent', verbose_name='申请人')
    target = models.ForeignKey(CustomUser, on_delete=models.CASCADE, related_name='applies_received',
                               verbose_name='接收人')
    type = models.IntegerField(verbose_name='申请类型', choices=Type.choices)  # 1加好友
    msg = models.CharField(max_length=64, verbose_name='申请信息')
    status = models.IntegerField(verbose_name='申请状态', choices=Status.choices)  # 1待审批 2同意
    read_status = models.IntegerField(verbose_name='阅读状态', choices=ReadStatus.choices)  # 1未读 2已读
    create_time = models.DateTimeField(auto_now_add=True, verbose_name='创建时间')
    update_time = models.DateTimeField(auto_now=True, verbose_name='修改时间')

    class Meta:
        db_table = 'user_apply'
        indexes = [
            models.Index(fields=['uid', 'target']),
            models.Index(fields=['target', 'read_status']),
            models.Index(fields=['target']),
            models.Index(fields=['create_time']),
            models.Index(fields=['update_time']),
        ]

    @staticmethod
    def is_to_read(user_apply_query):
        apply_ids = [apply['id'] for apply in user_apply_query]
        UserApply.objects.filter(id__in=apply_ids).update(read_status=UserApply.ReadStatus.READ)


class UserFriend(models.Model):
    class Delete(models.IntegerChoices):
        NORMAL = 0, '正常'
        DELETED = 1, '删除'

    id = models.BigAutoField(primary_key=True, verbose_name='UserFriend id')
    uid = models.ForeignKey(CustomUser, on_delete=models.CASCADE, related_name='friends', verbose_name='用户')
    friend = models.ForeignKey(CustomUser, on_delete=models.CASCADE, related_name='user_friends', verbose_name='好友')
    delete_status = models.IntegerField(default=Delete.NORMAL, choices=Delete.choices,
                                        verbose_name='逻辑删除')  # 0-正常, 1-删除
    create_time = models.DateTimeField(auto_now_add=True, verbose_name='创建时间')
    update_time = models.DateTimeField(auto_now=True, verbose_name='修改时间')

    class Meta:
        db_table = 'user_friend'
        indexes = [
            models.Index(fields=['uid']),
            models.Index(fields=['uid', 'friend']),
            models.Index(fields=['create_time']),
            models.Index(fields=['update_time']),
        ]
