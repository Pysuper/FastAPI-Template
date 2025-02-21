from datetime import datetime
from enum import Enum
from functools import wraps
from typing import Any, Callable, Dict, Optional, TypeVar

from core.config.setting import settings
from core.loge.pysuper_logging import get_logger

logger = get_logger("circuit_breaker")

T = TypeVar("T")


class CircuitState(str, Enum):
    """断路器状态"""

    CLOSED = "closed"  # 正常状态
    OPEN = "open"  # 熔断状态
    HALF_OPEN = "half_open"  # 半开状态


class CircuitBreaker:
    """断路器"""

    def __init__(
        self,
        name: str,
        failure_threshold: int = None,
        recovery_timeout: int = None,
        max_failures: int = None,
        reset_timeout: int = None,
    ):
        self.name = name
        self.failure_threshold = failure_threshold or settings.CIRCUIT_BREAKER_FAILURE_THRESHOLD
        self.recovery_timeout = recovery_timeout or settings.CIRCUIT_BREAKER_RECOVERY_TIMEOUT
        self.max_failures = max_failures or settings.CIRCUIT_BREAKER_MAX_FAILURES
        self.reset_timeout = reset_timeout or settings.CIRCUIT_BREAKER_RESET_TIMEOUT

        self._state = CircuitState.CLOSED
        self._failure_count = 0
        self._last_failure_time: Optional[datetime] = None
        self._last_success_time: Optional[datetime] = None
        self._last_state_change_time = datetime.now()

    @property
    def state(self) -> CircuitState:
        """获取当前状态"""
        return self._state

    @property
    def is_closed(self) -> bool:
        """是否处于关闭状态"""
        return self._state == CircuitState.CLOSED

    @property
    def is_open(self) -> bool:
        """是否处于开启状态"""
        return self._state == CircuitState.OPEN

    @property
    def is_half_open(self) -> bool:
        """是否处于半开状态"""
        return self._state == CircuitState.HALF_OPEN

    def _should_allow_request(self) -> bool:
        """是否允许请求"""
        now = datetime.now()

        if self._state == CircuitState.CLOSED:
            return True

        elif self._state == CircuitState.OPEN:
            # 检查是否达到恢复时间
            if (now - self._last_state_change_time).total_seconds() >= self.recovery_timeout:
                self._transition_to_half_open()
                return True
            return False

        elif self._state == CircuitState.HALF_OPEN:
            # 在半开状态下允许有限的请求通过
            return True

        return False

    def _on_success(self):
        """处理成功请求"""
        self._last_success_time = datetime.now()

        if self._state == CircuitState.HALF_OPEN:
            # 如果在半开状态下请求成功，转换为关闭状态
            self._transition_to_closed()

        # 重置失败计数
        self._failure_count = 0

    def _on_failure(self):
        """处理失败请求"""
        now = datetime.now()
        self._last_failure_time = now
        self._failure_count += 1

        # 检查是否需要开启断路器
        if self._state == CircuitState.CLOSED:
            if self._failure_count >= self.failure_threshold:
                self._transition_to_open()

        elif self._state == CircuitState.HALF_OPEN:
            # 在半开状态下如果请求失败，立即转换为开启状态
            self._transition_to_open()

    def _transition_to_open(self):
        """转换到开启状态"""
        self._state = CircuitState.OPEN
        self._last_state_change_time = datetime.now()
        logger.warning(f"Circuit breaker '{self.name}' transitioned to OPEN state")

    def _transition_to_half_open(self):
        """转换到半开状态"""
        self._state = CircuitState.HALF_OPEN
        self._last_state_change_time = datetime.now()
        logger.info(f"Circuit breaker '{self.name}' transitioned to HALF-OPEN state")

    def _transition_to_closed(self):
        """转换到关闭状态"""
        self._state = CircuitState.CLOSED
        self._last_state_change_time = datetime.now()
        self._failure_count = 0
        logger.info(f"Circuit breaker '{self.name}' transitioned to CLOSED state")

    def get_stats(self) -> dict:
        """获取统计信息"""
        return {
            "name": self.name,
            "state": self._state,
            "failure_count": self._failure_count,
            "last_failure_time": self._last_failure_time.isoformat() if self._last_failure_time else None,
            "last_success_time": self._last_success_time.isoformat() if self._last_success_time else None,
            "last_state_change_time": self._last_state_change_time.isoformat(),
            "failure_threshold": self.failure_threshold,
            "recovery_timeout": self.recovery_timeout,
            "max_failures": self.max_failures,
            "reset_timeout": self.reset_timeout,
        }


class CircuitBreakerRegistry:
    """断路器注册表"""

    def __init__(self):
        self._breakers: Dict[str, CircuitBreaker] = {}

    def get_or_create(
        self,
        name: str,
        failure_threshold: int = None,
        recovery_timeout: int = None,
        max_failures: int = None,
        reset_timeout: int = None,
    ) -> CircuitBreaker:
        """获取或创建断路器"""
        if name not in self._breakers:
            self._breakers[name] = CircuitBreaker(
                name=name,
                failure_threshold=failure_threshold,
                recovery_timeout=recovery_timeout,
                max_failures=max_failures,
                reset_timeout=reset_timeout,
            )
        return self._breakers[name]

    def get_all_stats(self) -> Dict[str, dict]:
        """获取所有断路器的统计信息"""
        return {name: breaker.get_stats() for name, breaker in self._breakers.items()}


# 创建全局断路器注册表
circuit_breaker_registry = CircuitBreakerRegistry()


def circuit_breaker(
    name: str = None,
    failure_threshold: int = None,
    recovery_timeout: int = None,
    max_failures: int = None,
    reset_timeout: int = None,
    fallback_function: Callable = None,
):
    """断路器装饰器"""

    def decorator(func: Callable[..., Any]) -> Callable[..., Any]:
        breaker_name = name or func.__name__
        breaker = circuit_breaker_registry.get_or_create(
            name=breaker_name,
            failure_threshold=failure_threshold,
            recovery_timeout=recovery_timeout,
            max_failures=max_failures,
            reset_timeout=reset_timeout,
        )

        @wraps(func)
        async def wrapper(*args, **kwargs):
            if not breaker._should_allow_request():
                if fallback_function:
                    return await fallback_function(*args, **kwargs)
                raise Exception(f"Circuit breaker '{breaker_name}' is open")

            try:
                result = await func(*args, **kwargs)
                breaker._on_success()
                return result
            except Exception as e:
                breaker._on_failure()
                if fallback_function:
                    return await fallback_function(*args, **kwargs)
                raise

        return wrapper

    return decorator


def get_circuit_breaker_stats() -> Dict[str, dict]:
    """获取所有断路器的统计信息"""
    return circuit_breaker_registry.get_all_stats()
