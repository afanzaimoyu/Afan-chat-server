"""
URL configuration for AfanChatServer project.

The `urlpatterns` list routes URLs to views. For more information please see:
    https://docs.djangoproject.com/en/4.2/topics/http/urls/
Examples:
Function views
    1. Add an import:  from my_app import views
    2. Add a URL to urlpatterns:  path('', views.home, name='home')
Class-based views
    1. Add an import:  from other_app.views import Home
    2. Add a URL to urlpatterns:  path('', Home.as_view(), name='home')
Including another URLconf
    1. Import the include() function: from django.urls import include, path
    2. Add a URL to urlpatterns:  path('blog/', include('blog.urls'))
"""
import json

import xmltodict
from django.contrib import admin
from django.http import HttpRequest
from django.urls import path
from ninja.security import HttpBearer
from ninja_extra import NinjaExtraAPI
from ninja_schema.types import DictStrAny

from users.apis.login_controller import WeChatLoginApi
from users.apis.user_controller import UserController
from users.user_tools.afan_ninja import AfanNinjaAPI
from typing import cast, Type, Optional, Any, Dict
from ninja.parser import Parser


class MyParser(Parser):
    def parse_body(self, request: HttpRequest) -> DictStrAny:
        content_type = request.headers.get("Content-Type", "").lower()

        if 'xml' in content_type:
            return cast(DictStrAny, xmltodict.parse(request.body))
        else:
            return cast(DictStrAny, json.loads(request.body))


api = AfanNinjaAPI(parser=MyParser())
api.register_controllers(
    WeChatLoginApi,
    UserController
)

urlpatterns = [
    path('admin/', admin.site.urls),
    path("api/", api.urls),
]
