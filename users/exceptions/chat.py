from ninja_extra import status
from ninja_extra.exceptions import APIException
from django.utils.translation import gettext_lazy as _
from typing import Any, Dict, List, Optional, Type, Union, no_type_check


class Business_Error(APIException):
    status_code = status.HTTP_200_OK
    default_detail = _("Malformed request.")
    default_code = "parse_error"
