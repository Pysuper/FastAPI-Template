import functools
import inspect
import logging
import traceback
from datetime import datetime
from typing import Any, Callable, Optional

from sqlalchemy.orm import Session

from models import SystemLog

logger = logging.getLogger(__name__)

def log_error(message: str, module: Optional[str] = None, trace: Optional[str] = None) -> None:
    """
    记录错误日志
    :param message: 错误消息
    :param module: 模块名称
    :param trace: 堆栈跟踪
    """
    try:
        # 获取调用者的模块名称
        if module is None:
            frame = inspect.currentframe()
            if frame:
                frame = frame.f_back
                if frame:
                    module = frame.f_globals.get('__name__', 'unknown')

        # 如果没有提供堆栈跟踪，获取当前堆栈
        if trace is None:
            trace = traceback.format_exc()
            if trace == 'NoneType: None\n':
                trace = None

        # 记录到日志文件
        logger.error(f"[{module}] {message}")
        if trace:
            logger.error(f"Stack trace:\n{trace}")

        # 记录到数据库
        try:
            db = SessionLocal()
            log_entry = SystemLog(
                level="ERROR",
                module=module or "unknown",
                message=message,
                trace=trace
            )
            db.add(log_entry)
            db.commit()
        except Exception as e:
            logger.error(f"Failed to save error log to database: {str(e)}")
        finally:
            db.close()

    except Exception as e:
        # 如果在记录过程中发生错误，至少尝试打印到控制台
        print(f"Failed to log error: {str(e)}")

def operation_log(operation: str = None, module: str = None, action: str = None):
    """
    操作日志装饰器
    :param operation: 操作描述（旧参数，为了向后兼容）
    :param module: 模块名称
    :param action: 操作动作
    """
    def decorator(func: Callable[..., Any]):
        @functools.wraps(func)
        async def wrapper(*args, **kwargs):
            # 获取当前用户信息
            current_user = None
            for arg in args:
                if hasattr(arg, 'get') and callable(arg.get):
                    user_id = arg.get('user_id')
                    if user_id:
                        current_user = user_id
                        break
            
            # 获取数据库会话
            db = None
            for arg in args:
                if isinstance(arg, Session):
                    db = arg
                    break
            if db is None:
                for value in kwargs.values():
                    if isinstance(value, Session):
                        db = value
                        break
            
            start_time = datetime.utcnow()
            error = None
            try:
                # 执行原始函数
                result = await func(*args, **kwargs)
                return result
            except Exception as e:
                error = e
                raise
            finally:
                try:
                    # 记录操作日志
                    if db is None:
                        db = SessionLocal()
                        should_close = True
                    else:
                        should_close = False

                    # 获取模块名称和操作描述
                    log_module = module or func.__module__
                    log_operation = operation or f"{action}"
                    if module and action:
                        log_operation = f"{action}"

                    # 构建日志消息
                    message = f"{log_operation}"
                    if current_user:
                        message = f"User {current_user} - {message}"
                    if error:
                        message = f"{message} - Failed: {str(error)}"
                    else:
                        message = f"{message} - Success"

                    # 创建日志记录
                    log_entry = SystemLog(
                        level="ERROR" if error else "INFO",
                        module=log_module,
                        message=message,
                        trace=traceback.format_exc() if error else None
                    )
                    db.add(log_entry)
                    db.commit()

                    if should_close:
                        db.close()

                except Exception as e:
                    logger.error(f"Failed to save operation log: {str(e)}")

        return wrapper
    return decorator 