# -*- coding: utf-8 -*-
import json
from json import JSONDecodeError
from urllib.parse import quote
from typing import Optional, Dict, Any, Union

from config.settings.base import env
from django.core.cache import cache
import requests


class WeChatOAuth:
    """
    微信公众号  OAuth 网页授权

    详情:
        - 授权: https://developers.weixin.qq.com/doc/offiaccount/OA_Web_Apps/Wechat_webpage_authorization.html
        - 二维码: https://developers.weixin.qq.com/doc/offiaccount/Account_Management/Generating_a_Parametric_QR_Code.html
    """

    API_BASE_URL = "https://api.weixin.qq.com/"
    OAUTH_BASE_URL = "https://open.weixin.qq.com/connect/"
    QRCODE_SHOW_URL = "https://mp.weixin.qq.com/cgi-bin/showqrcode"

    def __init__(self, app_id: str = None, secret: str = None, redirect_uri: str = None,
                 scope: str = "snsapi_base",
                 state: str = "", expire_seconds: Optional[int] = 60):
        """
        初始化 WeChatOAuth 实例

        Args:
            app_id (str): 微信公众号 app_id
            secret (str): 微信公众号 secret
            redirect_uri (str): OAuth2 redirect URI
            scope (str, optional): 微信公众号 OAuth2 scope，默认为 'snsapi_base'
            state (str, optional): 微信公众号 OAuth2 state
            expire_seconds (Optional[int]): 二维码有效时间，以秒为单位。最大不超过2592000（即30天），默认为60秒。
        """
        self.app_id = env.str("APP_ID", app_id)
        self.secret = env.str("secret", secret)
        self.redirect_uri = env.str("redirect_uri", redirect_uri)
        self.scope = env.str("scope", scope)
        self.state = env.str("state", state)
        self.expire_seconds = env.int("expire_seconds", expire_seconds)
        self._http = requests.Session()

    def _request(self, method: str, url_or_endpoint: str, **kwargs: Any) -> Union[Dict[str, Any], bytes]:
        """
        发送 HTTP 请求并处理返回结果

        Args:
            method (str): 请求方法 ('get' 或 'post' )
            url_or_endpoint (str): 请求的 URL 或端点
            **kwargs (Any): 其他请求参数

        Returns:
            dict: 解析后的 JSON 数据

        Raises:
            dict: 包含错误信息的字典，如果发生异常
        """
        exception_type = "WeChatOAuthException" if method == 'get' else "WeChatQRCodeException"

        url = f"{self.API_BASE_URL}{url_or_endpoint}" if not url_or_endpoint.startswith(
            ("http://", "https://")) else url_or_endpoint

        if isinstance(kwargs.get("data", ""), dict):
            body = json.dumps(kwargs["data"], ensure_ascii=False)
            body = body.encode('utf-8')
            kwargs["data"] = body

        res = self._http.request(method=method, url=url, **kwargs)

        try:
            res.raise_for_status()
        except requests.RequestException as e:
            raise {
                "name": exception_type,
                "errcode": None,
                "errmsg": None,
                "client": self,
                "request": e.request,
                "response": e.response,
            }

        content_type = res.headers.get('Content-Type', '')
        print(content_type)

        match content_type:
            case x if 'application/json' or 'text' in x:
                result = json.loads(res.content.decode('utf-8', "ignore"), strict=False)
            case _:
                return res.content
        print(result)


        if "errcode" in result and result["errcode"] != 0:
            errcode = result["errcode"]
            errmsg = result["errmsg"]
            raise {
                "name": exception_type,
                "errcode": errcode,
                "errmsg": errmsg,
                "client": self,
                "request": res.request,
                "response": res,
            }

        return result

    def _get(self, url: str, **kwargs: Any) -> Union[Dict[str, Any], bytes]:

        return self._request(method="get", url_or_endpoint=url, **kwargs)

    def _post(self, url: str, **kwargs: Any) -> Dict[str, Any]:

        return self._request(method="post", url_or_endpoint=url, **kwargs)

    @property
    def authorize_url(self) -> str:
        """
        获取微信公众号 OAuth 授权跳转地址

        Returns:
            str: 授权跳转地址
        """
        redirect_uri = quote(self.redirect_uri, safe=b'')
        url_parts = [
            self.OAUTH_BASE_URL,
            "oauth2/authorize?appid=",
            self.app_id,
            "&redirect_uri=",
            redirect_uri,
            "&response_type=code&scope=",
            self.scope,
        ]

        if self.state:
            url_parts.extend(["&state=", self.state])
        url_parts.append("#wechat_redirect")

        return "".join(url_parts)

    @property
    def fetch_normal_access_token(self):
        """
        获取access_token，保存到缓存
        Returns:
            access_token

        """
        res = self._get(
            "cgi-bin/token",
            params={
                "grant_type": "client_credential",
                "appid": self.app_id,
                "secret": self.secret,
            },
        )
        access_token = res.get('access_token')
        expires_in = int(res.get("expires_in"))

        cache.set("wx_access_token", access_token, expires_in)
        return access_token

    def fetch_access_token(self, code: str) -> dict:
        """
        获取 access_token

        Args:
            code (str): 授权完成跳转回来后 URL 中的 code 参数

        Returns:
            dict: 包含以下键值对的字典
                - access_token (str): 网页授权接口调用凭证，注意：此access_token与基础支持的access_token不同
                - open_id (str): 用户唯一标识，请注意，在未关注公众号时，用户访问公众号的网页，也会产生一个用户和公众号唯一的OpenID
                - refresh_token (str): 用户刷新access_token
                - expires_in (int): access_token接口调用凭证超时时间，单位（秒）

        Raises:
            WeChatOAuthException: 如果请求过程中发生异常或获取到的结果包含错误信息
        """
        res = self._get(
            "sns/oauth2/access_token",
            params={
                "appid": self.app_id,
                "secret": self.secret,
                "code": code,
                "grant_type": "authorization_code",
            },
        )

        return res

    def refresh_access_token(self, refresh_token: str) -> dict:
        """
        刷新 access_token

        Args:
            refresh_token (str): OAuth2 refresh token

        Returns:
            dict: 包含以下键值对的字典
                - access_token (str): 网页授权接口调用凭证，注意：此access_token与基础支持的access_token不同
                - open_id (str): 用户唯一标识
                - refresh_token (str): 用户刷新access_token
                - expires_in (int): access_token接口调用凭证超时时间，单位（秒）

        Raises:
            WeChatOAuthException: 如果请求过程中发生异常或获取到的结果包含错误信息
        """
        res = self._get(
            "sns/oauth2/refresh_token",
            params={
                "appid": self.app_id,
                "grant_type": "refresh_token",
                "refresh_token": refresh_token,
            },
        )

        return res

    def get_user_info(self, openid: Optional[str] = None, access_token: Optional[str] = None,
                      lang: str = "zh_CN") -> dict:
        """
        获取用户信息

        Args:
            openid (Optional[str]): 可选，微信 openid，默认获取当前授权用户信息
            access_token (Optional[str]): 可选，access_token，默认使用当前授权用户的 access_token
            lang (str): 可选，语言偏好，默认为 "zh_CN"

        Returns:
            dict: 包含用户信息的字典，具体字段如下：
                - openid (str): 用户的唯一标识
                - nickname (str): 用户昵称
                - sex (int): 用户的性别，值为1时是男性，值为2时是女性，值为0时是未知
                - province (str): 用户个人资料填写的省份
                - city (str): 普通用户个人资料填写的城市
                - country (str): 国家，如中国为CN
                - headimgurl (str): 用户头像URL，最后一个数值代表正方形头像大小（有0、46、64、96、132数值可选，0代表640*640正方形头像），用户没有头像时为空
                - privilege (List[str]): 用户特权信息，json 数组，如微信沃卡用户为（chinaunicom）
                - unionid (str): 只有在用户将公众号绑定到微信开放平台账号后，才会出现该字段

        Raises:
            WeChatOAuthException: 如果请求过程中发生异常或获取到的结果包含错误信息
        """
        openid = openid
        access_token = access_token
        return self._get(
            "sns/userinfo",
            params={"access_token": access_token, "openid": openid, "lang": lang},
        )

    def create_temporary_qrcode(self, access_token: str, scene_str: str) -> dict:
        """
        创建临时二维码

        Args:
            access_token(str): 普通 access_token
            scene_str (str): 场景值ID（字符串形式的ID），字符串类型，长度限制为1到64


        Returns:
            dict: 包含二维码信息的字典，具体字段如下：
                - ticket (str): 获取的二维码ticket，凭借此ticket可以在有效时间内换取二维码。
                - expire_seconds (int): 二维码有效时间，以秒为单位。 最大不超过2592000（即30天）。
                - url (str): 二维码图片解析后的地址，开发者可根据该地址自行生成需要的二维码图片

        Raises:
            WeChatQRCodeException: 如果请求过程中发生异常或获取到的结果包含错误信息
        """

        data = {
            "expire_seconds": self.expire_seconds,
            "action_name": "QR_STR_SCENE",
            "action_info": {"scene": {"scene_str": scene_str}},
        }

        res = self._post(
            "cgi-bin/qrcode/create",
            params={"access_token": access_token},
            json=data
        )
        return res

    def get_qrcode_image(self, ticket: str) -> bytes:
        """
        获取二维码图片

        Args:
            ticket (str): 获取的二维码ticket

        Returns:
            bytes: 二维码图片的字节数据

        Raises:
            WeChatQRCodeException: 如果请求过程中发生异常或获取到的结果包含错误信息
        """
        res = self._get(
            self.QRCODE_SHOW_URL,
            params={"ticket": ticket}
        )

        return res

    def fetch_template_text(self, open_id:str,access_token: str,auth_url:str):

        data = {
            "touser": open_id,
            "template_id": "IT2JavpghUvB59pMBnHzxiv8QkaqsL1fsXZ5Q_vmNps",
            "url":auth_url,
        }
        res = self._post(
            "cgi-bin/message/template/send",
            params={"access_token": access_token},
            json=data
        )
        return res

# if __name__ == '__main__':
# # 使用示例
# app_id = "your_app_id"
# secret = "your_secret"
# redirect_uri = "your_redirect_uri"
# scope = "snsapi_userinfo"
# state = "your_state"
# scene_id = 123
# expire_seconds = 60
#
# wechat_oauth = WeChatOAuth(app_id, secret, redirect_uri, scene_id, scope, state, expire_seconds)
#
# # 生成授权地址
# authorize_url = wechat_oauth.authorize_url
# print("Authorize URL:", authorize_url)
#
# # 获取用户授权后的 code，用于换取 access_token
# user_code = input("Enter the user code: ")
#
# # 通过 code 获取 access_token
# access_token_info = wechat_oauth.fetch_access_token(user_code)
# print("Access Token Info:", access_token_info)
#
# # 刷新 access_token
# refresh_token_info = wechat_oauth.refresh_access_token(access_token_info["refresh_token"])
# print("Refresh Token Info:", refresh_token_info)
#
# # 获取用户信息
# user_info = wechat_oauth.get_user_info()
# print("User Info:", user_info)
#
# # 创建临时二维码
# qr_ticket = wechat_oauth.create_temporary_qrcode.get('ticket')
# print("QR ticket:", qr_ticket)
#
# # 生成二维码
# qr_code = wechat_oauth.get_qrcode_image(qr_ticket)
# print("QR CODE:", qr_code)
