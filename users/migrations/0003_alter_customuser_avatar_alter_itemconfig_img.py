# Generated by Django 5.0 on 2023-12-16 14:01

from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('users', '0002_alter_customuser_avatar_itemconfig_userbackpack_and_more'),
    ]

    operations = [
        migrations.AlterField(
            model_name='customuser',
            name='avatar',
            field=models.CharField(max_length=255, null=True, verbose_name='用户头像'),
        ),
        migrations.AlterField(
            model_name='itemconfig',
            name='img',
            field=models.CharField(max_length=255, null=True, verbose_name='物品图片'),
        ),
    ]
