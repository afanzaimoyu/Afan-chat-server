from typing import Optional

from bs4 import BeautifulSoup
from lxml.etree import HTML

from chat.utils.url_discover.abstract_url_discover import AbstractUrlDiscover
from chat.utils.url_discover.common_url_discover import CommonUrlDiscover
from chat.utils.url_discover.wx_url_discover import WxUrlDiscover


class PrioritizedUrlDiscover(AbstractUrlDiscover):
    def __init__(self):
        self.url_discovers = [WxUrlDiscover(), CommonUrlDiscover()]

    def get_title(self, document: HTML) -> Optional[str]:
        for url_discover in self.url_discovers:
            url_title = url_discover.get_title(document)
            if url_title:
                return url_title
        return None

    def get_description(self, document: HTML) -> Optional[str]:
        for url_discover in self.url_discovers:
            url_description = url_discover.get_description(document)
            if url_description:
                return url_description
        return None

    def get_image(self, url: str, document: HTML) -> Optional[str]:
        for url_discover in self.url_discovers:
            url_image = url_discover.get_image(url, document)
            if url_image:
                return url_image
        return None
