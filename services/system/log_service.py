"""
日志服务模块
"""
from typing import List, Optional, Tuple

from sqlalchemy.orm import Session

from api.v1.endpoints.system.logs import Log, LogCreate, LogUpdate


class LogService:
    """日志服务类"""

    async def get_list(
        self, db: Session, query: Optional[str] = None, page: int = 1, size: int = 20, sort: Optional[str] = None
    ) -> Tuple[int, List[Log]]:
        """获取日志列表"""
        # 构建查询
        stmt = db.query(Log).filter(Log.is_delete == False)

        # 关键词搜索
        if query:
            stmt = stmt.filter(
                Log.title.ilike(f"%{query}%") | Log.content.ilike(f"%{query}%") | Log.module.ilike(f"%{query}%")
            )

        # 获取总数
        total = stmt.count()

        # 排序
        if sort:
            if sort.startswith("-"):
                stmt = stmt.order_by(getattr(Log, sort[1:]).desc())
            else:
                stmt = stmt.order_by(getattr(Log, sort).asc())
        else:
            stmt = stmt.order_by(Log.create_time.desc())

        # 分页
        stmt = stmt.offset((page - 1) * size).limit(size)

        # 执行查询
        items = stmt.all()

        return total, items

    async def create(self, db: Session, log: LogCreate) -> Log:
        """创建日志"""
        db_log = Log(**log.dict())
        db.add(db_log)
        db.commit()
        db.refresh(db_log)
        return db_log

    async def batch_create(self, db: Session, logs: List[LogCreate]) -> List[Log]:
        """批量创建日志"""
        db_logs = [Log(**log.dict()) for log in logs]
        db.add_all(db_logs)
        db.commit()
        for log in db_logs:
            db.refresh(log)
        return db_logs

    async def get(self, db: Session, log_id: int) -> Optional[Log]:
        """获取日志详情"""
        return db.query(Log).filter(Log.id == log_id, Log.is_delete == False).first()

    async def update(self, db: Session, log_id: int, log: LogUpdate) -> Optional[Log]:
        """更新日志"""
        db_log = await self.get(db, log_id)
        if not db_log:
            return None

        # 更新字段
        for field, value in log.dict(exclude_unset=True).items():
            setattr(db_log, field, value)

        db.add(db_log)
        db.commit()
        db.refresh(db_log)
        return db_log

    async def batch_update(self, db: Session, logs: List[LogUpdate]) -> List[Log]:
        """批量更新日志"""
        updated_logs = []
        for log in logs:
            if not hasattr(log, "id"):
                continue
            db_log = await self.update(db, log.id, log)
            if db_log:
                updated_logs.append(db_log)
        return updated_logs

    async def delete(self, db: Session, log_id: int) -> bool:
        """删除日志"""
        db_log = await self.get(db, log_id)
        if not db_log:
            return False

        db_log.is_delete = True
        db.add(db_log)
        db.commit()
        return True

    async def batch_delete(self, db: Session, log_ids: List[int]) -> bool:
        """批量删除日志"""
        db.query(Log).filter(Log.id.in_(log_ids)).update({"is_delete": True})
        db.commit()
        return True

    async def import_data(self, db: Session, file) -> bool:
        """导入日志数据"""

        return True

    async def export_data(self, db: Session, query: Optional[str] = None):
        """导出日志数据"""

        return None

    async def get_stats(self, db: Session, group_by: Optional[str] = None, start_date=None, end_date=None):
        """获取日��统计"""

        return None
