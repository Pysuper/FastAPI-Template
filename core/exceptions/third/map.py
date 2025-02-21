"""
地图服务相关的异常模块
"""
from typing import Dict, Optional

from core.exceptions.base.error_codes import ErrorCode
from core.exceptions.system.api import BusinessException


class MapServiceException(BusinessException):
    """地图服务异常基类"""

    def __init__(
        self,
        message: str,
        code: str = ErrorCode.THIRD_PARTY_ERROR,
        details: Optional[Dict] = None,
        context: Optional[Dict] = None,
    ):
        """
        初始化地图服务异常
        
        Args:
            message: 错误信息
            code: 错误码
            details: 错误详情
            context: 错误上下文
        """
        context = {"map_error": True, **(context or {})}
        super().__init__(message=message, code=code, details=details, context=context)


class AMapException(MapServiceException):
    """高德地图异常基类"""

    def __init__(
        self,
        message: str = "高德地图服务异常",
        details: Optional[Dict] = None,
        context: Optional[Dict] = None,
    ):
        context = {"amap_error": True, **(context or {})}
        super().__init__(message=message, details=details, context=context)


class BaiduMapException(MapServiceException):
    """百度地图异常基类"""

    def __init__(
        self,
        message: str = "百度地图服务异常",
        details: Optional[Dict] = None,
        context: Optional[Dict] = None,
    ):
        context = {"baidu_map_error": True, **(context or {})}
        super().__init__(message=message, details=details, context=context)


class GeocodingException(MapServiceException):
    """地理编码异常"""

    def __init__(
        self,
        message: str = "地理编码失败",
        details: Optional[Dict] = None,
        context: Optional[Dict] = None,
    ):
        context = {"geocoding_error": True, **(context or {})}
        super().__init__(message=message, details=details, context=context)


class ReverseGeocodingException(MapServiceException):
    """逆地理编码异常"""

    def __init__(
        self,
        message: str = "逆地理编码失败",
        details: Optional[Dict] = None,
        context: Optional[Dict] = None,
    ):
        context = {"reverse_geocoding_error": True, **(context or {})}
        super().__init__(message=message, details=details, context=context)


class RoutePlanningException(MapServiceException):
    """路线规划异常"""

    def __init__(
        self,
        message: str = "路线规划失败",
        details: Optional[Dict] = None,
        context: Optional[Dict] = None,
    ):
        context = {"route_error": True, **(context or {})}
        super().__init__(message=message, details=details, context=context)


class DistanceCalculationException(MapServiceException):
    """距离计算异常"""

    def __init__(
        self,
        message: str = "距离计算失败",
        details: Optional[Dict] = None,
        context: Optional[Dict] = None,
    ):
        context = {"distance_error": True, **(context or {})}
        super().__init__(message=message, details=details, context=context)


class PlaceSearchException(MapServiceException):
    """地点搜索异常"""

    def __init__(
        self,
        message: str = "地点搜索失败",
        details: Optional[Dict] = None,
        context: Optional[Dict] = None,
    ):
        context = {"place_search_error": True, **(context or {})}
        super().__init__(message=message, details=details, context=context)


class IPLocationException(MapServiceException):
    """IP定位异常"""

    def __init__(
        self,
        message: str = "IP定位失败",
        details: Optional[Dict] = None,
        context: Optional[Dict] = None,
    ):
        context = {"ip_location_error": True, **(context or {})}
        super().__init__(message=message, details=details, context=context) 