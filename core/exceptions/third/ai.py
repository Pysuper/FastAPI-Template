"""
人工智能服务相关的异常模块
"""
from typing import Dict, Optional

from core.exceptions.base.error_codes import ErrorCode
from core.exceptions.system.api import BusinessException


class AIServiceException(BusinessException):
    """AI服务异常基类"""

    def __init__(
        self,
        message: str,
        code: str = ErrorCode.THIRD_PARTY_ERROR,
        details: Optional[Dict] = None,
        context: Optional[Dict] = None,
    ):
        """
        初始化AI服务异常
        
        Args:
            message: 错误信息
            code: 错误码
            details: 错误详情
            context: 错误上下文
        """
        context = {"ai_error": True, **(context or {})}
        super().__init__(message=message, code=code, details=details, context=context)


class OCRException(AIServiceException):
    """OCR异常基类"""

    def __init__(
        self,
        message: str = "OCR服务异常",
        details: Optional[Dict] = None,
        context: Optional[Dict] = None,
    ):
        context = {"ocr_error": True, **(context or {})}
        super().__init__(message=message, details=details, context=context)


class SpeechRecognitionException(AIServiceException):
    """语音识别异常基类"""

    def __init__(
        self,
        message: str = "语音识别服务异常",
        details: Optional[Dict] = None,
        context: Optional[Dict] = None,
    ):
        context = {"speech_recognition_error": True, **(context or {})}
        super().__init__(message=message, details=details, context=context)


class TextToSpeechException(AIServiceException):
    """语音合成异常基类"""

    def __init__(
        self,
        message: str = "语音合成服务异常",
        details: Optional[Dict] = None,
        context: Optional[Dict] = None,
    ):
        context = {"tts_error": True, **(context or {})}
        super().__init__(message=message, details=details, context=context)


class FaceRecognitionException(AIServiceException):
    """人脸识别异常基类"""

    def __init__(
        self,
        message: str = "人脸识别服务异常",
        details: Optional[Dict] = None,
        context: Optional[Dict] = None,
    ):
        context = {"face_recognition_error": True, **(context or {})}
        super().__init__(message=message, details=details, context=context)


class ImageRecognitionException(AIServiceException):
    """图像识别异常基类"""

    def __init__(
        self,
        message: str = "图像识别服务异常",
        details: Optional[Dict] = None,
        context: Optional[Dict] = None,
    ):
        context = {"image_recognition_error": True, **(context or {})}
        super().__init__(message=message, details=details, context=context)


class NLPException(AIServiceException):
    """自然语言处理异常基类"""

    def __init__(
        self,
        message: str = "NLP服务异常",
        details: Optional[Dict] = None,
        context: Optional[Dict] = None,
    ):
        context = {"nlp_error": True, **(context or {})}
        super().__init__(message=message, details=details, context=context)


class TranslationException(AIServiceException):
    """机器翻译异常基类"""

    def __init__(
        self,
        message: str = "机器翻译服务异常",
        details: Optional[Dict] = None,
        context: Optional[Dict] = None,
    ):
        context = {"translation_error": True, **(context or {})}
        super().__init__(message=message, details=details, context=context)


class SentimentAnalysisException(AIServiceException):
    """情感分析异常基类"""

    def __init__(
        self,
        message: str = "情感分析服务异常",
        details: Optional[Dict] = None,
        context: Optional[Dict] = None,
    ):
        context = {"sentiment_analysis_error": True, **(context or {})}
        super().__init__(message=message, details=details, context=context)


class ChatbotException(AIServiceException):
    """聊天机器人异常基类"""

    def __init__(
        self,
        message: str = "聊天机器人服务异常",
        details: Optional[Dict] = None,
        context: Optional[Dict] = None,
    ):
        context = {"chatbot_error": True, **(context or {})}
        super().__init__(message=message, details=details, context=context) 