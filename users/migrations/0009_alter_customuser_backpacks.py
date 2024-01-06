# Generated by Django 5.0 on 2023-12-17 13:38

from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('users', '0008_alter_customuser_backpacks'),
    ]

    operations = [
        migrations.AlterField(
            model_name='customuser',
            name='backpacks',
            field=models.ManyToManyField(related_name='back', through='users.UserBackpack', to='users.itemconfig', verbose_name='用户与物品的关联'),
        ),
    ]