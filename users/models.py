from django.db import models
from django.contrib.auth.models import AbstractBaseUser, BaseUserManager, PermissionsMixin


class CustomUserManager(BaseUserManager):
    def create_user(self, open_id,  **extra_fields):
        if not open_id:
            raise ValueError('必须设置 OpenID 字段')
        user = self.model(
            open_id=open_id,
            **extra_fields
        )
        user.save(using=self._db)
        return user.id

    def create_superuser(self, open_id, password=None, **extra_fields):
        extra_fields.setdefault('is_staff', True)
        extra_fields.setdefault('is_superuser', True)
        return self.create_user(open_id, password=password, **extra_fields)


class CustomUser(AbstractBaseUser, PermissionsMixin):
    password = None

    id = models.BigAutoField(primary_key=True)
    open_id = models.CharField(max_length=32, unique=True, verbose_name='微信openid用户标识')
    name = models.CharField(max_length=20, null=True, verbose_name='用户昵称')
    avatar = models.CharField(max_length=255, null=True, verbose_name='用户头像')
    sex = models.IntegerField(choices=[(1, '男性'), (2, '女性')], null=True, verbose_name='性别')
    is_active = models.IntegerField(default=2, verbose_name='在线状态', choices=[(1, '在线'), (2, '离线')])

    last_login = models.DateTimeField(auto_now=True, verbose_name='最后上下线时间')
    ip_info = models.JSONField(null=True, verbose_name='ip信息')
    item_id = models.BigIntegerField(null=True, verbose_name='佩戴的徽章id')
    status = models.IntegerField(default=0, verbose_name='使用状态', choices=[(0, '正常'), (1, '拉黑')])
    create_time = models.DateTimeField(auto_now_add=True, verbose_name='创建时间')
    update_time = models.DateTimeField(auto_now=True, verbose_name='修改时间')

    objects = CustomUserManager()

    USERNAME_FIELD = 'open_id'
    REQUIRED_FIELDS = []

    def __str__(self):
        return self.open_id
