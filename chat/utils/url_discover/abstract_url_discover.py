import re
from abc import abstractmethod
from concurrent.futures import ThreadPoolExecutor
from typing import Dict, Tuple, Optional
import requests
from lxml.etree import HTML
from fake_useragent import UserAgent

from chat.utils.url_discover.domain.url_info import UrlInfo
from chat.utils.url_discover.url_discover import UrlDiscover


class AbstractUrlDiscover(UrlDiscover):
    PATTERN = re.compile(r"(https?://)?(www\.)?([\w_-]+(?:\.[\w_-]+)+)([\w@?^=%&:/~+#-]*)", re.S)

    def get_url_content_map(self, content: str) -> Dict[str, UrlInfo]:
        if not content:
            return {}

        match_list = [''.join(m) for m in re.findall(self.PATTERN, content)]
        with ThreadPoolExecutor() as executor:
            results = list(executor.map(self.get_content, match_list))
        # results = []
        # for i in match_list:
        #     j = self.get_content(i)
        #     results.append(j)

        return dict(zip(match_list, results))

    def get_content(self, url: str) -> Optional[UrlInfo]:
        print(url)
        match_url = self.assemble(url)
        document = self.get_url_document(match_url)
        if document:
            return UrlInfo(
                title=self.get_title(document),
                description=self.get_description(document),
                image=self.get_image(match_url, document)
            ).dict()

        return None

    @staticmethod
    def assemble(url: str) -> str:
        if not url.startswith("http"):
            return "http://" + url
        return url

    @staticmethod
    def get_url_document(match_url: str) -> Optional[HTML]:
        try:

            headers = {"User-Agent": UserAgent().random}
            response = requests.get(match_url, headers=headers, timeout=2)
            response.raise_for_status()
            response.encoding = "utf-8"
            return HTML(response.text)
        except requests.RequestException as e:
            print(f"Error fetching URL {match_url}: {e}")
            return None
        except Exception as e:
            print(f"-Error fetching URL {match_url}: {e}")
            return None

    @staticmethod
    def is_connect(href: str) -> bool:
        try:
            headers = {"User-Agent": UserAgent().random}
            response = requests.head(href, headers=headers, timeout=1)
            return response.status_code in {200, 302, 304} and not response.headers.get("Content-Disposition")
        except requests.RequestException:
            return False

    @abstractmethod
    def get_title(self, document: HTML) -> Optional[str]:
        raise NotImplementedError

    @abstractmethod
    def get_description(self, document: HTML) -> Optional[str]:
        raise NotImplementedError

    @abstractmethod
    def get_image(self, url: str, document: HTML) -> Optional[str]:
        raise NotImplementedError
