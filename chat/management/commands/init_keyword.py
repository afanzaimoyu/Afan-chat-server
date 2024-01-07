from django.contrib.auth.models import Group
from django.core.management.base import BaseCommand
from django.db import IntegrityError
from pathlib import Path

from chat.models import SensitiveWord


class Command(BaseCommand):
    help = '初始化数据'

    def handle(self, *args, **options):

        keywords_file = Path(__package__).parent.resolve() / "chat" / "utils" / "sensitive_word" / "keywords"
        print(keywords_file)
        files = filter(lambda x: x.suffix == '.txt', keywords_file.iterdir())
        print(files)
        for file in files:
            print(file.name)
            with open(keywords_file / file.name, 'r', encoding='utf-8') as f:
                liens = f.readlines()
            for lien in liens:
                word = lien.strip().replace(',', '')
                try:
                    SensitiveWord.objects.update_or_create(word=word)
                except IntegrityError as exc:
                    with open(keywords_file / "err.txt ", 'a', encoding='utf-8') as f:
                        f.write(word)
                    self.stdout.write(self.style.ERROR(f'初始化数据失败，详情查看{keywords_file}/error.txt'))
        self.stdout.write(self.style.SUCCESS('初始化数据成功'))
