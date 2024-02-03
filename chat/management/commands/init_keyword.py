from django.conf import settings
from django.contrib.auth.models import Group
from django.core.management.base import BaseCommand
from django.db import IntegrityError
from pathlib import Path

from django.utils import timezone

from chat.models import SensitiveWord


class Command(BaseCommand):
    help = '初始化数据'

    def handle(self, *args, **options):
        start = timezone.now()

        keywords_file = Path(__package__).parent.resolve() / "chat" / "utils" / "sensitive_word" / "keywords"
        print(keywords_file)
        files = filter(lambda x: x.suffix == '.txt', keywords_file.iterdir())
        print(files)

        existing_sensitive_words = list(SensitiveWord.objects.values_list('word', flat=True))
        # old = list()
        sensitive_words_need_insert = set()

        for file in files:
            print(file.name)
            with open(keywords_file / file.name, 'r', encoding='utf-8') as f:
                liens = f.readlines()

            for lien in liens:
                word = lien.strip().replace(',', '')
                # old.append(word)
                # 检查数据库中是否已经存在相同的敏感词
                if word not in existing_sensitive_words:
                    sensitive_words_need_insert.add(word)

        # duplicates = [item for item in old if old.count(item) > 1]
        try:
            SensitiveWord.objects.bulk_create([SensitiveWord(word=word) for word in sensitive_words_need_insert])
            self.stdout.write(self.style.SUCCESS(f'初始化数据成功, 数据量：{len(sensitive_words_need_insert)}条'))
        except IntegrityError as exc:
            with open(settings.LOG_ROOT / "error.txt ", 'a', encoding='utf-8') as f:
                f.write(f'{exc}\n')
            self.stdout.write(self.style.ERROR(f'初始化数据失败，详情查看{settings.LOG_ROOT}/error.txt'))
        end = timezone.now()
        self.stdout.write(self.style.SUCCESS(f'初始化数据耗时：{end - start}'))
