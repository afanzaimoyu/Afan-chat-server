# Generated by Django 5.0 on 2023-12-16 15:21

from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('users', '0003_alter_customuser_avatar_alter_itemconfig_img'),
    ]

    operations = [
        migrations.AlterField(
            model_name='customuser',
            name='last_login',
            field=models.DateTimeField(blank=True, null=True, verbose_name='最后上下线时间'),
        ),
    ]
