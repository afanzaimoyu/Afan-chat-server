from typing import Optional

from ninja_schema import Schema


class IpDetail(Schema):
    ip: str = None
    isp_id: Optional[str] = None
    isp: str = None
    city: str = None
    city_id: Optional[str] = None
    county: str = None
    county_id: Optional[str] = None
    region: str = None
    region_id: Optional[str] = None


class Ipinfo(Schema):
    createIp: Optional[str] = None
    updateIp: Optional[str] = None
    createIpDetail: Optional[IpDetail] = None
    updateIpDetail: Optional[IpDetail] = None

    def refresh_ip(self, data):
        if self.createIp == data.get("ip"):
            self.createIpDetail = IpDetail(**data)
        self.updateIpDetail = IpDetail(**data)
