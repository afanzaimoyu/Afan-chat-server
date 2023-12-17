from typing import Any, Optional, Dict

from django.db.models import URLField
from ninja_extra import exceptions
from django.http import HttpRequest, HttpResponse
from ninja_extra import NinjaExtraAPI


class AfanNinjaAPI(NinjaExtraAPI):
    def create_response(
            self,
            request: HttpRequest,
            data: Any,
            *,
            status: Optional[int] = None,
            temporal_response: Optional[HttpResponse] = None,
            err_data: Any = None
    ) -> HttpResponse:
        if temporal_response:
            status = temporal_response.status_code
        assert status

        std_data = (
            err_data if err_data else
            {
                "success": False,
                "errCode": status,
                "errMsg": data,
                "data": None
            } if (400 <= status < 600) else
            {
                "success": True,
                "errCode": None,
                "errMsg": None,
                "data": data
            }
        )

        content = self.renderer.render(request, std_data, response_status=status)

        if temporal_response:
            response = temporal_response
            response.content = content
        else:
            response = HttpResponse(
                content, status=status, content_type=self.get_content_type()
            )

        return response

    def api_exception_handler(
            self, request: HttpRequest, exc: exceptions.APIException
    ) -> HttpResponse:
        headers: Dict = {}
        if isinstance(exc, exceptions.Throttled):
            headers["Retry-After"] = "%d" % float(exc.wait or 0.0)

        if isinstance(exc.detail, (list, dict)):
            errmsg = exc.detail
        else:
            errmsg = {"detail": exc.detail}
        errcode = exc.status_code

        err_data = {
            "success": False,
            "errCode": exc.get_codes(),
            "errMsg": errmsg,
            "data": None
        }

        response = self.create_response(request, data=None, status=errcode, err_data=err_data)
        for k, v in headers.items():
            response.setdefault(k, v)

        return response
