"""
@Project ：Speedy
@File    ：locks.py
@Author  ：PySuper
@Date    ：2024-12-28 18:33
@Desc    ：数据库锁机制实现模块

提供了数据库锁的具体实现，包括:
    - 锁超时处理
    - 死锁检测
    - 锁管理器
    - 分布式锁
    - 乐观锁
    - 悲观锁
    - 行级锁
    - 表级锁
    - 共享锁
    - 排他锁
    
代码示例：
    ```python
    # 使用分布式锁
    async with lock_manager.lock(LockType.DISTRIBUTED, "resource_key") as lock:
        if lock.is_acquired:
            # 执行需要锁保护的操作
            pass
    
    # 使用乐观锁
    async with lock_manager.lock(
        LockType.OPTIMISTIC,
        str(record_id),
        session=session,
        model=UserModel
    ) as lock:
        # 执行更新操作
        if await lock.validate_and_update():
            # 更新成功
            pass
    
    # 使用悲观锁
    async with lock_manager.lock(
        LockType.PESSIMISTIC,
        str(record_id),
        session=session,
        model=UserModel
    ) as lock:
        # 执行需要锁保护的操作
        pass
    ```
    
    ```python
    # 设置默认超时时间
    lock_manager.set_default_timeout(30.0)
    
    # 配置死锁检测间隔
    await lock_manager.start_deadlock_detection(interval=1.0)
    
    # 自定义锁参数
    async with lock_manager.lock(
        lock_type=LockType.DISTRIBUTED,
        resource="custom_resource",
        timeout=60.0,
        retry_count=5,
        retry_delay=0.2
    ) as lock:
        pass
    ```
"""

import asyncio
import logging
import time
from contextlib import asynccontextmanager
from dataclasses import dataclass
from enum import Enum, auto
from typing import Any, AsyncGenerator, Dict, List, Optional, Set, Type, TypeVar

from sqlalchemy import Table, select, text
from sqlalchemy.ext.asyncio import AsyncSession

from core.cache.manager import cache_manager

logger = logging.getLogger(__name__)

# 类型变量
T = TypeVar("T")
Model = TypeVar("Model")


class LockError(Exception):
    """锁错误基类"""

    pass


class LockTimeoutError(LockError):
    """锁超时错误"""

    pass


class LockAcquisitionError(LockError):
    """锁获取错误"""

    pass


class LockReleaseError(LockError):
    """锁释放错误"""

    pass


class DeadlockError(LockError):
    """死锁错误"""

    pass


class LockWaitTimeout(LockError):
    """锁等待超时错误"""

    pass


class LockType(Enum):
    """锁类型"""

    SHARED = auto()  # 共享锁
    EXCLUSIVE = auto()  # 排他锁
    ROW = auto()  # 行级锁
    TABLE = auto()  # 表级锁
    OPTIMISTIC = auto()  # 乐观锁
    PESSIMISTIC = auto()  # 悲观锁
    DISTRIBUTED = auto()  # 分布式锁


@dataclass
class LockInfo:
    """锁信息"""

    type: LockType  # 锁类型
    resource: str  # 资源标识
    owner: str  # 锁持有者
    acquired_at: float  # 获取时间
    timeout: float  # 超时时间
    expires_at: float  # 过期时间
    is_released: bool = False  # 是否已释放


class BaseLock:
    """锁基类"""

    def __init__(self, resource: str, timeout: float = 30.0):
        """
        初始化锁
        :param resource: 资源标识
        :param timeout: 超时时间(秒)
        """
        self.resource = resource
        self.timeout = timeout
        self._owner: Optional[str] = None
        self._acquired_at: Optional[float] = None
        self._expires_at: Optional[float] = None

    @property
    def is_acquired(self) -> bool:
        """是否已获取锁"""
        return bool(self._owner and self._acquired_at and time.time() < self._expires_at)

    @property
    def is_expired(self) -> bool:
        """是否已过期"""
        return bool(self._expires_at and time.time() >= self._expires_at)

    async def acquire(self) -> bool:
        """
        获取锁
        :return: 是否成功获取
        :raises LockAcquisitionError: 获取锁失败
        """
        raise NotImplementedError

    async def release(self) -> None:
        """
        释放锁
        :raises LockReleaseError: 释放锁失败
        """
        raise NotImplementedError


class DistributedLock(BaseLock):
    """
    分布式锁
    基于Redis实现的分布式锁
    """

    def __init__(self, resource: str, timeout: float = 30.0, retry_count: int = 3, retry_delay: float = 0.1):
        """
        初始化分布式锁
        :param resource: 资源标识
        :param timeout: 超时时间(秒)
        :param retry_count: 重试次数
        :param retry_delay: 重试延迟(秒)
        """
        super().__init__(resource, timeout)
        self.retry_count = retry_count
        self.retry_delay = retry_delay
        self._lock_key = f"lock:{self.resource}"

    async def acquire(self) -> bool:
        """
        获取分布式锁
        :return: 是否成功获取
        :raises LockAcquisitionError: 获取锁失败
        """
        for i in range(self.retry_count):
            try:
                now = time.time()
                self._owner = str(id(self))
                self._acquired_at = now
                self._expires_at = now + self.timeout

                success = await cache_manager.set(self._lock_key, self._owner, expire=int(self.timeout), nx=True)

                if success:
                    return True

                if i < self.retry_count - 1:
                    await asyncio.sleep(self.retry_delay)

            except Exception as e:
                raise LockAcquisitionError(f"获取分布式锁失败: {str(e)}")

        return False

    async def release(self) -> None:
        """
        释放分布式锁
        :raises LockReleaseError: 释放锁失败
        """
        try:
            if self._owner:
                # 确保只能由锁的持有者释放
                current_owner = await cache_manager.get(self._lock_key)
                if current_owner == self._owner:
                    await cache_manager.delete(self._lock_key)
                    self._owner = None
                    self._acquired_at = None
                    self._expires_at = None
        except Exception as e:
            raise LockReleaseError(f"释放分布式锁失败: {str(e)}")


class OptimisticLock(BaseLock):
    """
    乐观锁
    基于版本号的乐观锁实现
    """

    def __init__(self, resource: str, session: AsyncSession, model: Type[Model], version_field: str = "version"):
        """
        初始化乐观锁
        :param resource: 资源标识
        :param session: 数据库会话
        :param model: 模型类
        :param version_field: 版本字段名
        """
        super().__init__(resource)
        self.session = session
        self.model = model
        self.version_field = version_field
        self._current_version: Optional[int] = None

    async def acquire(self) -> bool:
        """
        获取乐观锁(实际上只是获取当前版本号)
        :return: 是否成功获取
        :raises LockAcquisitionError: 获取锁失败
        """
        try:
            result = await self.session.execute(
                select(getattr(self.model, self.version_field)).where(self.model.id == self.resource)
            )
            self._current_version = result.scalar_one_or_none()
            return True
        except Exception as e:
            raise LockAcquisitionError(f"获取乐观锁失败: {str(e)}")

    async def validate_and_update(self) -> bool:
        """
        验证并更新版本号
        :return: 是否更新成功
        """
        try:
            if self._current_version is None:
                return False

            result = await self.session.execute(
                self.model.__table__.update()
                .where(self.model.id == self.resource, getattr(self.model, self.version_field) == self._current_version)
                .values({self.version_field: self._current_version + 1})
            )

            return result.rowcount > 0
        except Exception as e:
            raise LockError(f"乐观锁更新失败: {str(e)}")

    async def release(self) -> None:
        """释放乐观锁(实际上不需要做任何事)"""
        self._current_version = None


class PessimisticLock(BaseLock):
    """
    悲观锁
    基于SELECT FOR UPDATE的悲观锁实现
    """

    def __init__(self, resource: str, session: AsyncSession, model: Type[Model], skip_locked: bool = False):
        """
        初始化悲观锁
        :param resource: 资源标识
        :param session: 数据库会话
        :param model: 模型类
        :param skip_locked: 是否跳过已锁定的行
        """
        super().__init__(resource)
        self.session = session
        self.model = model
        self.skip_locked = skip_locked
        self._locked = False

    async def acquire(self) -> bool:
        """
        获取悲观锁
        :return: 是否成功获取
        :raises LockAcquisitionError: 获取锁失败
        """
        try:
            query = (
                select(self.model).where(self.model.id == self.resource).with_for_update(skip_locked=self.skip_locked)
            )

            result = await self.session.execute(query)
            row = result.scalar_one_or_none()

            if row:
                self._locked = True
                return True
            return False

        except Exception as e:
            raise LockAcquisitionError(f"获取悲观锁失败: {str(e)}")

    async def release(self) -> None:
        """
        释放悲观锁(通过提交或回滚事务)
        :raises LockReleaseError: 释放锁失败
        """
        try:
            if self._locked:
                await self.session.commit()
                self._locked = False
        except Exception as e:
            raise LockReleaseError(f"释放悲观锁失败: {str(e)}")


class RowLock(BaseLock):
    """
    行级锁
    提供了行级别的锁定机制
    """

    def __init__(
        self, resource: str, session: AsyncSession, model: Type[Model], lock_type: LockType = LockType.EXCLUSIVE
    ):
        """
        初始化行级锁
        :param resource: 资源标识(行ID)
        :param session: 数据库会话
        :param model: 模型类
        :param lock_type: 锁类型
        """
        super().__init__(resource)
        self.session = session
        self.model = model
        self.lock_type = lock_type
        self._locked = False

    async def acquire(self) -> bool:
        """
        获取行级锁
        :return: 是否成功获取
        :raises LockAcquisitionError: 获取锁失败
        """
        try:
            query = select(self.model).where(self.model.id == self.resource)

            if self.lock_type == LockType.SHARED:
                query = query.with_for_update(read=True)
            else:
                query = query.with_for_update()

            result = await self.session.execute(query)
            row = result.scalar_one_or_none()

            if row:
                self._locked = True
                return True
            return False

        except Exception as e:
            raise LockAcquisitionError(f"获取行级锁失败: {str(e)}")

    async def release(self) -> None:
        """
        释放行级锁
        :raises LockReleaseError: 释放锁失败
        """
        try:
            if self._locked:
                await self.session.commit()
                self._locked = False
        except Exception as e:
            raise LockReleaseError(f"释放行级锁失败: {str(e)}")


class TableLock(BaseLock):
    """
    表级锁
    提供了表级别的锁定机制
    """

    def __init__(self, resource: str, session: AsyncSession, table: Table, lock_type: LockType = LockType.EXCLUSIVE):
        """
        初始化表级锁
        :param resource: 资源标识(表名)
        :param session: 数据库会话
        :param table: 表对象
        :param lock_type: 锁类型
        """
        super().__init__(resource)
        self.session = session
        self.table = table
        self.lock_type = lock_type
        self._locked = False

    async def acquire(self) -> bool:
        """
        获取表级锁
        :return: 是否成功获取
        :raises LockAcquisitionError: 获取锁失败
        """
        try:
            mode = "SHARE" if self.lock_type == LockType.SHARED else "EXCLUSIVE"
            sql = text(f"LOCK TABLE {self.table.name} IN {mode} MODE")

            await self.session.execute(sql)
            self._locked = True
            return True

        except Exception as e:
            raise LockAcquisitionError(f"获取表级锁失败: {str(e)}")

    async def release(self) -> None:
        """
        释放表级锁
        :raises LockReleaseError: 释放锁失败
        """
        try:
            if self._locked:
                await self.session.execute(text("UNLOCK TABLES"))
                await self.session.commit()
                self._locked = False
        except Exception as e:
            raise LockReleaseError(f"释放表级锁失败: {str(e)}")


class SharedLock(BaseLock):
    """
    共享锁
    允许多个事务同时读取数据
    """

    def __init__(self, resource: str, session: AsyncSession, model: Type[Model]):
        """
        初始化共享锁
        :param resource: 资源标识
        :param session: 数据库会话
        :param model: 模型类
        """
        super().__init__(resource)
        self.session = session
        self.model = model
        self._locked = False

    async def acquire(self) -> bool:
        """
        获取共享锁
        :return: 是否成功获取
        :raises LockAcquisitionError: 获取锁失败
        """
        try:
            query = select(self.model).where(self.model.id == self.resource).with_for_update(read=True)

            result = await self.session.execute(query)
            row = result.scalar_one_or_none()

            if row:
                self._locked = True
                return True
            return False

        except Exception as e:
            raise LockAcquisitionError(f"获取共享锁失败: {str(e)}")

    async def release(self) -> None:
        """
        释放共享锁
        :raises LockReleaseError: 释放锁失败
        """
        try:
            if self._locked:
                await self.session.commit()
                self._locked = False
        except Exception as e:
            raise LockReleaseError(f"释放共享锁失败: {str(e)}")


class ExclusiveLock(BaseLock):
    """
    排他锁
    确保同一时间只有一个事务可以修改数据
    """

    def __init__(self, resource: str, session: AsyncSession, model: Type[Model]):
        """
        初始化排他锁
        :param resource: 资源标识
        :param session: 数据库会话
        :param model: 模型类
        """
        super().__init__(resource)
        self.session = session
        self.model = model
        self._locked = False

    async def acquire(self) -> bool:
        """
        获取排他锁
        :return: 是否成功获取
        :raises LockAcquisitionError: 获取锁失败
        """
        try:
            query = select(self.model).where(self.model.id == self.resource).with_for_update()

            result = await self.session.execute(query)
            row = result.scalar_one_or_none()

            if row:
                self._locked = True
                return True
            return False

        except Exception as e:
            raise LockAcquisitionError(f"获取排他锁失败: {str(e)}")

    async def release(self) -> None:
        """
        释放排他锁
        :raises LockReleaseError: 释放锁失败
        """
        try:
            if self._locked:
                await self.session.commit()
                self._locked = False
        except Exception as e:
            raise LockReleaseError(f"释放排他锁失败: {str(e)}")


@dataclass
class DeadlockInfo:
    """死锁信息"""

    resource: str  # 资源标识
    waiting_for: str  # 等待的资源
    held_by: str  # 持有资源的锁
    wait_start_time: float  # 等待开始时间
    timeout: float  # 超时时间


class DeadlockDetector:
    """死锁检测器"""

    def __init__(self):
        self._wait_for_graph: Dict[str, Set[str]] = {}  # 等待图
        self._resource_holders: Dict[str, str] = {}  # 资源持有者
        self._wait_start_times: Dict[str, float] = {}  # 等待开始时间
        self._lock = asyncio.Lock()

    async def add_wait(self, waiter: str, waiting_for: str, holder: str) -> None:
        """
        添加等待关系
        :param waiter: 等待者
        :param waiting_for: 等待的资源
        :param holder: 持有者
        """
        async with self._lock:
            if waiter not in self._wait_for_graph:
                self._wait_for_graph[waiter] = set()
            self._wait_for_graph[waiter].add(waiting_for)
            self._resource_holders[waiting_for] = holder
            self._wait_start_times[waiter] = time.time()

    async def remove_wait(self, waiter: str) -> None:
        """
        移除等待关系
        :param waiter: 等待者
        """
        async with self._lock:
            if waiter in self._wait_for_graph:
                del self._wait_for_graph[waiter]
            if waiter in self._wait_start_times:
                del self._wait_start_times[waiter]

    def _detect_cycle(self, start: str, visited: Set[str], path: Set[str]) -> Optional[List[str]]:
        """
        检测等待图中的环
        :param start: 起始节点
        :param visited: 已访问节点
        :param path: 当前路径
        :return: 环路径
        """
        if start in path:
            return [start]

        if start in visited:
            return None

        visited.add(start)
        path.add(start)

        if start in self._wait_for_graph:
            for next_node in self._wait_for_graph[start]:
                if next_node in self._resource_holders:
                    next_holder = self._resource_holders[next_node]
                    cycle = self._detect_cycle(next_holder, visited, path)
                    if cycle:
                        cycle.insert(0, start)
                        return cycle

        path.remove(start)
        return None

    async def check_deadlock(self) -> Optional[List[DeadlockInfo]]:
        """
        检查死锁
        :return: 死锁信息列表
        """
        async with self._lock:
            deadlocks = []
            visited = set()

            for node in self._wait_for_graph:
                if node not in visited:
                    cycle = self._detect_cycle(node, visited, set())
                    if cycle:
                        # 构建死锁信息
                        for i in range(len(cycle)):
                            current = cycle[i]
                            next_idx = (i + 1) % len(cycle)
                            next_node = cycle[next_idx]

                            for resource in self._wait_for_graph[current]:
                                if self._resource_holders[resource] == next_node:
                                    deadlocks.append(
                                        DeadlockInfo(
                                            resource=resource,
                                            waiting_for=resource,
                                            held_by=next_node,
                                            wait_start_time=self._wait_start_times[current],
                                            timeout=30.0,  # 默认超时时间
                                        )
                                    )

            return deadlocks if deadlocks else None


class LockManager:
    """
    锁管理器
    统一管理各种类型的锁
    """

    def __init__(self):
        """初始化锁管理器"""
        self._locks: Dict[str, LockInfo] = {}
        self._lock = asyncio.Lock()
        self._deadlock_detector = DeadlockDetector()
        self._lock_wait_timeout = 30.0  # 默认锁等待超时时间(秒)

    async def create_lock(
        self,
        lock_type: LockType,
        resource: str,
        session: Optional[AsyncSession] = None,
        model: Optional[Type[Model]] = None,
        table: Optional[Table] = None,
        timeout: float = None,
        **kwargs: Any,
    ) -> BaseLock:
        """
        创建锁
        :param lock_type: 锁类型
        :param resource: 资源标识
        :param session: 数据库会话
        :param model: 模型类
        :param table: 表对象
        :param timeout: 超时时间
        :param kwargs: 其他参数
        :return: 锁对象
        :raises ValueError: 参数错误
        """
        if timeout is None:
            timeout = self._lock_wait_timeout

        if lock_type == LockType.DISTRIBUTED:
            return DistributedLock(resource, **kwargs)

        if not session:
            raise ValueError("数据库会话不能为空")

        if lock_type == LockType.OPTIMISTIC:
            if not model:
                raise ValueError("模型类不能为空")
            return OptimisticLock(resource, session, model, **kwargs)

        if lock_type == LockType.PESSIMISTIC:
            if not model:
                raise ValueError("模型类不能为空")
            return PessimisticLock(resource, session, model, **kwargs)

        if lock_type == LockType.ROW:
            if not model:
                raise ValueError("模型类不能为空")
            return RowLock(resource, session, model, **kwargs)

        if lock_type == LockType.TABLE:
            if not table:
                raise ValueError("表对象不能为空")
            return TableLock(resource, session, table, **kwargs)

        if lock_type == LockType.SHARED:
            if not model:
                raise ValueError("模型类不能为空")
            return SharedLock(resource, session, model, **kwargs)

        if lock_type == LockType.EXCLUSIVE:
            if not model:
                raise ValueError("模型类不能为空")
            return ExclusiveLock(resource, session, model, **kwargs)

        raise ValueError(f"不支持的锁类型: {lock_type}")

    async def acquire_lock(self, lock_type: LockType, resource: str, timeout: float = None, **kwargs: Any) -> BaseLock:
        """
        获取锁
        :param lock_type: 锁类型
        :param resource: 资源标识
        :param timeout: 超时时间
        :param kwargs: 其他参数
        :return: 锁对象
        :raises LockAcquisitionError: 获取锁失败
        :raises LockWaitTimeout: 等待超时
        :raises DeadlockError: 检测到死锁
        """
        if timeout is None:
            timeout = self._lock_wait_timeout

        start_time = time.time()
        lock_id = str(id(resource))

        while True:
            try:
                async with self._lock:
                    # 检查资源是否已被锁定
                    if resource in self._locks:
                        current_holder = self._locks[resource].owner
                        # 添加等待关系用于死锁检测
                        await self._deadlock_detector.add_wait(lock_id, resource, current_holder)

                        # 检查死锁
                        deadlocks = await self._deadlock_detector.check_deadlock()
                        if deadlocks:
                            await self._deadlock_detector.remove_wait(lock_id)
                            raise DeadlockError(f"检测到死锁: {deadlocks}")

                        # 检查超时
                        if time.time() - start_time > timeout:
                            await self._deadlock_detector.remove_wait(lock_id)
                            raise LockWaitTimeout(f"等待锁超时: {resource}")

                        # 等待一段时间后重试
                        await asyncio.sleep(0.1)
                        continue

                    # 尝试获取锁
                    lock = await self.create_lock(lock_type, resource, timeout=timeout, **kwargs)

                    if await lock.acquire():
                        self._locks[resource] = LockInfo(
                            type=lock_type,
                            resource=resource,
                            owner=lock_id,
                            acquired_at=time.time(),
                            timeout=timeout,
                            expires_at=time.time() + timeout,
                        )
                        await self._deadlock_detector.remove_wait(lock_id)
                        return lock

            except (DeadlockError, LockWaitTimeout) as e:
                raise e
            except Exception as e:
                await self._deadlock_detector.remove_wait(lock_id)
                raise LockAcquisitionError(f"获取锁失败: {str(e)}")

    async def release_lock(self, lock: BaseLock) -> None:
        """
        释放锁
        :param lock: 锁对象
        :raises LockReleaseError: 释放锁失败
        """
        try:
            async with self._lock:
                await lock.release()
                if lock.resource in self._locks:
                    self._locks[lock.resource].is_released = True
                    del self._locks[lock.resource]

        except Exception as e:
            raise LockReleaseError(f"释放锁失败: {str(e)}")

    @asynccontextmanager
    async def lock(
        self, lock_type: LockType, resource: str, timeout: float = None, **kwargs: Any
    ) -> AsyncGenerator[BaseLock, None]:
        """
        锁上下文管理器
        :param lock_type: 锁类型
        :param resource: 资源标识
        :param timeout: 超时时间
        :param kwargs: 其他参数
        :yield: 锁对象
        :raises LockAcquisitionError: 获取锁失败
        :raises LockWaitTimeout: 等待超时
        :raises DeadlockError: 检测到死锁
        """
        lock = await self.acquire_lock(lock_type, resource, timeout=timeout, **kwargs)
        try:
            yield lock
        finally:
            await self.release_lock(lock)

    def get_lock_info(self, resource: str) -> Optional[LockInfo]:
        """
        获取锁信息
        :param resource: 资源标识
        :return: 锁信息
        """
        return self._locks.get(resource)

    def get_active_locks(self) -> List[LockInfo]:
        """
        获取所有活动的锁
        :return: 锁信息列表
        """
        return [
            lock_info
            for lock_info in self._locks.values()
            if not lock_info.is_released and time.time() < lock_info.expires_at
        ]

    async def cleanup_expired_locks(self) -> None:
        """清理过期的锁"""
        async with self._lock:
            now = time.time()
            expired = [resource for resource, lock_info in self._locks.items() if now >= lock_info.expires_at]
            for resource in expired:
                del self._locks[resource]

    def set_default_timeout(self, timeout: float) -> None:
        """
        设置默认超时时间
        :param timeout: 超时时间(秒)
        """
        self._lock_wait_timeout = timeout

    async def start_deadlock_detection(self, interval: float = 1.0) -> None:
        """
        启动死锁检测
        :param interval: 检测间隔(秒)
        """
        while True:
            try:
                deadlocks = await self._deadlock_detector.check_deadlock()
                if deadlocks:
                    logger.warning(f"检测到死锁: {deadlocks}")
                    # 这里可以添加死锁处理逻辑，比如选择牺牲者
                await asyncio.sleep(interval)
            except Exception as e:
                logger.error(f"死锁检测失败: {str(e)}")


# 创建锁管理器实例
lock_manager = LockManager()

# 导出
__all__ = [
    "LockManager",
    "DistributedLock",
    "OptimisticLock",
    "PessimisticLock",
    "RowLock",
    "TableLock",
    "SharedLock",
    "ExclusiveLock",
    "LockError",
    "LockTimeoutError",
    "LockAcquisitionError",
    "LockReleaseError",
    "DeadlockError",
    "LockWaitTimeout",
    "LockType",
    "lock_manager",
]
