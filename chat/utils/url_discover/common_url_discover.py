from typing import Optional
from urllib.parse import urljoin

from lxml.etree import HTML

from chat.utils.url_discover.abstract_url_discover import AbstractUrlDiscover


class CommonUrlDiscover(AbstractUrlDiscover):
    def get_title(self, document: HTML) -> Optional[str]:
        title = document.find(".//title").text
        if title:
            return title
        else:
            return None

    def get_description(self, document: HTML) -> Optional[str]:
        content = None
        description = document.xpath(".//meta[@name='description']")
        keywords = document.xpath(".//meta[@name='keywords']")
        if description:
            content = description[0].attrib.get("content")
        elif keywords:
            content = keywords[0].attrib.get("content")
        # 只保留一句话的描述
        return content[: content.find("。")] if content and content.find("。") != -1 else content

    def get_image(self, url: str, document: HTML) -> Optional[str]:
        href = None
        image = document.xpath(".//link[@type='image/x-icon']")
        # 如果没有去匹配含有icon属性的logo
        image2 = document.xpath(".//link[contains(@rel, 'icon')]")
        if image:
            href = image[0].attrib.get("href")
        elif image2:
            href = image2[0].get("href")
        # 如果url已经包含了logo
        if "favicon" in url:
            return url
        href = urljoin(url, href) if href and not href.startswith(("http", "https")) else href
        return href if self.is_connect(href) else None
