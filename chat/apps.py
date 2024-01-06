from pathlib import Path

from django.apps import AppConfig


class ChatConfig(AppConfig):
    default_auto_field = 'django.db.models.BigAutoField'
    name = 'chat'

    def ready(self):
        import chat.signals
        self.import_msg_handler()

    @staticmethod
    def import_msg_handler():
        msg_handler_folder = Path(__package__).resolve() / "msg_schema"
        files = filter(lambda x: x.suffix == '.py' and x.stem not in ['__init__','msg_handler_factory'] , msg_handler_folder.iterdir())
        for file in files:
            __import__(f'{__package__}.{file.parent.stem}.{file.stem}', globals(), locals(), [], 0)
