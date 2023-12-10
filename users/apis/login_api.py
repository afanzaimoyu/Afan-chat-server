import hashlib

from django.http import HttpResponse
from django.views.decorators.csrf import csrf_exempt
from ninja_extra import NinjaExtraAPI, api_controller, http_get, http_post

from config.settings.base import env

api = NinjaExtraAPI()


@api_controller('/wx', tags=["Wechat Login"], permissions=[])
class WeChatLoginApi:
    @http_get('/login')
    @csrf_exempt
    def wechat_auth(self, signature, timestamp, nonce, echostr):
        wx_token = env.str("Token")

        tmp_arr = [wx_token, timestamp, nonce]
        tmp_arr.sort()
        tmp_str = ''.join(tmp_arr)
        tmp_str = hashlib.sha1(tmp_str.encode()).hexdigest()

        if tmp_str == signature:
            return HttpResponse(echostr)
        else:
            return ""

    @http_post("/login")
    def my_auth(self, openid: str, data):
        """
        TODO: 关注授权等一系列流程
        Args:
            openid:
            data:

        Returns:

        """
        pass


api.register_controllers(
    WeChatLoginApi
)
