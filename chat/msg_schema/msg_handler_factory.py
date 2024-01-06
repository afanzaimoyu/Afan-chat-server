from users.exceptions.chat import Business_Error


class MsgHandlerFactory:
    """
    消息工厂类
    """
    STRATEGY_MAP = {}

    @staticmethod
    def register(code, strategy):
        MsgHandlerFactory.STRATEGY_MAP[code] = strategy

    @staticmethod
    def get_strategy_no_null(code: int):
        strategy = MsgHandlerFactory.STRATEGY_MAP.get(code)
        if not strategy: raise Business_Error(detail=f"{code}参数校验失败", code=-2)
        return strategy
