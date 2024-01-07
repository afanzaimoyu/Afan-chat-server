from typing import Optional

from ninja_schema import Schema


class UrlInfo(Schema):
    title: Optional[str] = None
    description: Optional[str] = None
    image: Optional[str] = None
