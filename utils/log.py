import inspect
import logging
import sys

from loguru import logger


class InterceptTimedRotatingFileHandler(logging.Handler):
    """
    自定义反射时间回滚日志记录器
    """

    def __init__(self, filename, formatter=None, when='WO', interval=1, backupCount=10, encoding="utf-8", delay=False,
                 utc=False,
                 atTime=None, logging_levels="all"):
        super(InterceptTimedRotatingFileHandler, self).__init__()

        filename = str(filename.resolve())
        when = when.lower()

        # 2.🎖️需要本地用不同的文件名做为不同日志的筛选器
        self.logger_ = logger.bind(sime=filename)
        self.filename = filename

        key_map = {'h': 'hour', 'w': 'week', 's': 'second', 'm': 'minute', 'd': 'day'}

        # 根据输入文件格式及时间回滚设立文件名称
        rotation = f"{interval} {key_map[when]}"
        retention = f"{backupCount} {key_map[when]}"
        time_format = "{time:%Y-%m-%d_%H-%M-%S}"

        # 根据时间回滚设置（when 参数）构建了不同的时间格式
        match when:
            case "s":
                time_format = "{time:%Y-%m-%d_%H-%M-%S}"
            case "m":
                time_format = "{time:%Y-%m-%d_%H-%M}"
            case "h":
                time_format = "{time:%Y-%m-%d_%H}"
            case "d":
                time_format = "{time:%Y-%m-%d}"
            case "w":
                time_format = "{time:%Y-%m-%d}"

        level_keys = ["info"]

        # 3.🎖️构建一个筛选器
        levels = {
            "debug": lambda x: "DEBUG" == x['level'].name.upper() and x['extra'].get('sime') == filename,
            "error": lambda x: "ERROR" == x['level'].name.upper() and x['extra'].get('sime') == filename,
            "info": lambda x: "INFO" == x['level'].name.upper() and x['extra'].get('sime') == filename,
            "warning": lambda x: "WARNING" == x['level'].name.upper() and x['extra'].get('sime') == filename
        }

        # 4. 🎖️根据输出构建筛选器
        if isinstance(logging_levels, str):
            if logging_levels.lower() == "all":
                level_keys = levels.keys()
            elif logging_levels.lower() in levels:
                level_keys = [logging_levels]
        elif isinstance(logging_levels, (list, tuple)):
            level_keys = logging_levels

        for k, f in {_: levels[_] for _ in level_keys}.items():

            # 5.🎖️为防止重复添加sink，而重复写入日志，需要判断是否已经装载了对应sink，防止其使用秘技：反复横跳。
            filename_fmt = filename.replace(".log", f"_{time_format}_{k}.log")
            # noinspection PyUnresolvedReferences,PyProtectedMember
            file_key = {_._name: han_id for han_id, _ in self.logger_._core.handlers.items()}
            filename_fmt_key = f"'{filename_fmt}'"
            if filename_fmt_key in file_key:
                continue

            self.logger_.add(
                filename_fmt,
                retention=retention,
                encoding=encoding,
                level=self.level,
                rotation=rotation,
                compression="tar.gz",  # 日志归档自行压缩文件
                delay=delay,
                enqueue=True,
                filter=f
            )

    def emit(self, record: logging.LogRecord):
        try:
            level = self.logger_.level(record.levelname).name
        except ValueError:
            level = record.levelno
        # noinspection PyUnresolvedReferences,PyProtectedMember
        frame, depth = sys._getframe(6), 6
        # 6.🎖️把当前帧的栈深度回到发生异常的堆栈深度，不然就是当前帧发生异常而无法回溯
        while frame and (depth == 0 or frame.f_code.co_filename == logging.__file__):
            frame = frame.f_back
            depth += 1
        self.logger_.opt(depth=depth, exception=record.exc_info).log(level, record.getMessage())


class LoguruStreamHandler(logging.Handler):
    def __init__(self, filename, logging_levels=None):
        super(LoguruStreamHandler, self).__init__()

        self.logging_levels = logging_levels or []

        self.filename = str(filename.resolve())
        self.logger_ = logger.bind(sime=self.filename)
        level_keys = ["info"]

        # 3.🎖️构建一个筛选器
        levels = {
            "debug": lambda x: "DEBUG" == x['level'].name.upper() and x['extra'].get('sime') == filename,
            "error": lambda x: "ERROR" == x['level'].name.upper() and x['extra'].get('sime') == filename,
            "info": lambda x: "INFO" == x['level'].name.upper() and x['extra'].get('sime') == filename,
            "warning": lambda x: "WARNING" == x['level'].name.upper() and x['extra'].get('sime') == filename
        }

        # 4. 🎖️根据输出构建筛选器
        if isinstance(logging_levels, str):
            if logging_levels.lower() == "all":
                level_keys = levels.keys()
            elif logging_levels.lower() in levels:
                level_keys = [logging_levels]
        elif isinstance(logging_levels, (list, tuple)):
            level_keys = logging_levels

        for k, f in {_: levels[_] for _ in level_keys}.items():

            # 5.🎖️为防止重复添加sink，而重复写入日志，需要判断是否已经装载了对应sink，防止其使用秘技：反复横跳。
            # noinspection PyUnresolvedReferences,PyProtectedMember
            file_key = {_._name: han_id for han_id, _ in self.logger_._core.handlers.items()}
            if self.filename in file_key:
                continue
        # noinspection PyUnresolvedReferences,PyProtectedMember
        # if not any(self.filename in handler._name for handler in self.logger_._core.handlers.values()):
            self.logger_.add(
                sink=self,
                level=self.level,
                enqueue=True,
                filter=f
            )

    def emit(self, record: logging.LogRecord) -> None:
        try:
            level = self.logger_.level(record.levelname).name
        except ValueError:
            level = record.levelno
        # noinspection PyUnresolvedReferences,PyProtectedMember
        frame, depth = sys._getframe(6), 6
        # 6.🎖️把当前帧的栈深度回到发生异常的堆栈深度，不然就是当前帧发生异常而无法回溯
        while frame and (depth == 0 or frame.f_code.co_filename == logging.__file__):
            frame = frame.f_back
            depth += 1
        self.logger_.opt(depth=depth, exception=record.exc_info).log(level, record.getMessage())
