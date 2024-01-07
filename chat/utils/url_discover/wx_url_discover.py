from typing import Optional

from bs4 import BeautifulSoup

from chat.utils.url_discover.abstract_url_discover import AbstractUrlDiscover


class WxUrlDiscover(AbstractUrlDiscover):
    def get_title(self, document: BeautifulSoup) -> Optional[str]:
        return document.find(".//meta[@property='og:title']").get("content") if document.find(".//meta["
                                                                                              "@property='og:title']") else None

    def get_description(self, document: BeautifulSoup) -> Optional[str]:
        return document.find(".//meta[@property='og:description']").get("content") if document.find(".//meta[@property='og:description']") else None

    def get_image(self, url: str, document: BeautifulSoup) -> Optional[str]:
        href = document.find(".//meta[@property='og:image']").get("content") if document.find(".//meta[@property='og:image']") else None
        return href if href and self.is_connect(href) else None
