# filters.py
import threading

from ahocorasick import Automaton

from chat.models import SensitiveWord


class Singleton(object):
    _instance_lock = threading.Lock()

    def __init__(self, cls):
        self._cls = cls
        self.unique_instance = None

    def __call__(self, *args, **kwargs):
        with self._instance_lock:
            if self.unique_instance is None:
                self.unique_instance = self._cls(*args, **kwargs)
        return self.unique_instance


@Singleton
class MySQLSensitiveWordFilter:
    def __init__(self):
        self.automaton = Automaton()
        self.load_words_from_mysql()

    def load_words_from_mysql(self):
        try:
            # 获取敏感词列表
            words = SensitiveWord.objects.values_list('id', 'word')

            # 将敏感词加载到 Aho-Corasick 自动机中
            for index, word in words:
                self.automaton.add_word(word, (index, word))
            self.automaton.make_automaton()

        except Exception as e:
            print(f"Error connecting to MySQL: {e}")

    def has_sensitive_word(self, text):

        for _, _ in self.automaton.iter(text):
            return True
        return False

    def filter(self, text):
        if not text:
            return text
        for end_index, matched_pattern in self.automaton.iter(text):
            print(matched_pattern)
            matched_pattern = matched_pattern[1]

            len_word = len(matched_pattern)
            end_index = end_index + 1
            start_index = end_index - len_word
            text = text.replace(text[start_index:end_index], '*' * len_word)
        return text
