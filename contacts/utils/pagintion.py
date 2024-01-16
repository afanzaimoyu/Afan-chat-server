from collections import OrderedDict
from functools import wraps
from typing import Optional, List, Tuple, Generic, TypeVar, Union
from django.db.models import Model, Q
from django.http import HttpRequest
from ninja import Schema
from ninja.constants import NOT_SET
from ninja.types import DictStrAny
from ninja_extra.shortcuts import add_ninja_contribute_args
from pydantic import Field
from typing import Callable, Type, Any

from ninja.pagination import paginate, PaginationBase
from ninja import Schema

T = TypeVar("T")


class NormalPaginationOutput(Schema):
    pageNO: int
    pageSize: int
    totalRecords: int
    isLast: bool
    list: List[T]


class NormalPaginationResponseSchema(NormalPaginationOutput, Generic[T]):
    list: List[T]


class NormalPagination(PaginationBase):
    # only `skip` param, defaults to 5 per page
    class Input(Schema):
        pageNo: int = Field(1, ge=1)

    def __init__(
            self, page_size: int = 10, wrapper_consumer: Callable = None, **kwargs: Any
    ) -> None:
        self.page_size = page_size
        self.wrapper_consumer = wrapper_consumer
        super().__init__(**kwargs)

    items_attribute: str = "list"

    def paginate_queryset(self, queryset, pagination: Input, **params):
        totalRecords = queryset.count()
        result_list = queryset[(pagination.pageNo - 1) * self.page_size: pagination.pageNo * self.page_size]

        if self.wrapper_consumer:
            self.wrapper_consumer(result_list)
        return OrderedDict(
            [
                ("list", list(result_list)),
                ("totalRecords", totalRecords),
                ("pageSize", self.page_size),
                ("pageNO", pagination.pageNo + 1 if len(result_list) == self.page_size else 1),
                ("isLast", pagination.pageNo * self.page_size >= totalRecords),
            ]
        )


class PageSizeInputBase(Schema):
    cursor: Optional[int] = 0
    pageSize: int = Field(100, lt=200)


class PageSizeOutputBase(Schema):
    cursor: Optional[str] = None
    isLast: bool = True
    list: List[T]


class CursorPaginationResponseSchema(PageSizeOutputBase, Generic[T]):
    list: List[T] = None


class CursorPagination(PaginationBase):
    class Input(Schema):
        cursor: Union[Optional[int], Optional[str]] = 0
        pageSize: int = Field(100, lt=200)

    def __init__(
            self, mapper: Type[Model], cursor_column: str, select: str = None,order=None, **kwargs: Any
    ) -> None:
        """

        Args:
            mapper: 你的数据库操作类
            cursor_column: 提供的扩展点，业务方可以在 SQL 中拼接一些查询条件
            select: 多表联查字段
            **kwargs:
        """
        self.mapper = mapper
        self.cursor_column = cursor_column
        self.select = select
        self.order = order
        super().__init__(**kwargs)

    items_attribute: str = "list"

    def paginate_queryset(self, wrapper_consumer, pagination: Input, **params):
        cursor = int(pagination.cursor) if pagination.cursor else 0
        page_size = pagination.pageSize

        query_and = {self.cursor_column + '__gt': cursor}
        query_not = {}
        query_or = {}

        # 扩展点，业务方可以在 SQL 中拼接一些查询条件
        for k, v in wrapper_consumer.items():
            match k:
                case '&':
                    query_and.update(v)
                case "~":
                    query_not = v
                case "|":
                    query_or = v
        # 获取满足条件的记录
        if self.select:
            queryset = self.mapper.objects.filter(Q(**query_and) & ~Q(**query_not) | Q(**query_or)).select_related(
                self.select).order_by(self.order)[
                       :page_size + 1]
        else:
            queryset = self.mapper.objects.filter(Q(**query_and) & ~Q(**query_not) | Q(**query_or)).order_by(
                self.order)[:page_size + 1]
        print(queryset.query)
        if queryset:
            # 获取实际返回的记录
            records = list(queryset[:page_size + 1])

            # 取出前 n 条记录供展示
            display_records = records[:page_size]

            # 计算下一页的游标
            next_cursor = str(getattr(records[-1], self.cursor_column)) if len(records) == page_size + 1 else None

            # 是否最后一页判断
            isLast = len(records) != page_size + 1
            return OrderedDict(
                [
                    ("list", display_records),
                    ("isLast", isLast),
                    ("cursor", next_cursor),
                ]
            )
