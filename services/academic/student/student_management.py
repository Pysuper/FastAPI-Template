from typing import List, Optional

from fastapi import HTTPException
from sqlalchemy.orm import Session

from core.cache import Cache
from core.logger import logger
from core.validators import StudentCreate, StudentUpdate
from models.student import Student, Behavior


class StudentService:
    def __init__(self, db: Session, cache: Cache):
        self.db = db
        self.cache = cache

    async def get_student_by_id(self, student_id: int) -> Optional[Student]:
        """获取学生信息"""
        # 尝试从缓存获取
        cache_key = f"student:{student_id}"
        cached_student = await self.cache.get(cache_key)
        if cached_student:
            return cached_student

        # 从数据库查询
        student = self.db.query(Student).filter(Student.id == student_id).first()
        if student:
            # 存入缓存
            await self.cache.set(cache_key, student, expire=3600)
        return student

    async def get_students(self, skip: int = 0, limit: int = 100) -> List[Student]:
        """获取学生列表"""
        return self.db.query(Student).offset(skip).limit(limit).all()

    async def create_student(self, student_data: StudentCreate) -> Student:
        """创建学生"""
        try:
            # 检查学号是否已存在
            existing = self.db.query(Student).filter(Student.student_id == student_data.student_id).first()
            if existing:
                raise HTTPException(status_code=400, detail="学号已存在")

            # 创建学生记录
            student = Student(**student_data.dict())
            self.db.add(student)
            self.db.commit()
            self.db.refresh(student)

            # 记录日志
            logger.info(f"Created student: {student.student_id}")

            return student
        except Exception as e:
            self.db.rollback()
            logger.error(f"Failed to create student: {str(e)}")
            raise

    async def update_student(self, student_id: int, student_data: StudentUpdate) -> Student:
        """更新学生信息"""
        try:
            student = await self.get_student_by_id(student_id)
            if not student:
                raise HTTPException(status_code=404, detail="学生不存在")

            # 更新字段
            for field, value in student_data.dict(exclude_unset=True).items():
                setattr(student, field, value)

            self.db.commit()
            self.db.refresh(student)

            # 清除缓存
            await self.cache.delete(f"student:{student_id}")

            # 记录日志
            logger.info(f"Updated student: {student.student_id}")

            return student
        except Exception as e:
            self.db.rollback()
            logger.error(f"Failed to update student: {str(e)}")
            raise

    async def delete_student(self, student_id: int) -> bool:
        """删除学生"""
        try:
            student = await self.get_student_by_id(student_id)
            if not student:
                raise HTTPException(status_code=404, detail="学生不存在")

            self.db.delete(student)
            self.db.commit()

            # 清除缓存
            await self.cache.delete(f"student:{student_id}")

            # 记录日志
            logger.info(f"Deleted student: {student.student_id}")

            return True
        except Exception as e:
            self.db.rollback()
            logger.error(f"Failed to delete student: {str(e)}")
            raise

    async def add_behavior_record(
        self, student_id: int, type: str, description: str, score: int, recorder_id: int
    ) -> Behavior:
        """添加行为记录"""
        try:
            student = await self.get_student_by_id(student_id)
            if not student:
                raise HTTPException(status_code=404, detail="学生不存在")

            behavior = Behavior(
                student_id=student_id, type=type, description=description, score=score, recorder_id=recorder_id
            )
            self.db.add(behavior)
            self.db.commit()
            self.db.refresh(behavior)

            # 记录日志
            logger.info(f"Added behavior record for student: {student.student_id}")

            return behavior
        except Exception as e:
            self.db.rollback()
            logger.error(f"Failed to add behavior record: {str(e)}")
            raise

    async def get_student_behaviors(self, student_id: int, skip: int = 0, limit: int = 100) -> List[Behavior]:
        """获取学生行为记录"""
        student = await self.get_student_by_id(student_id)
        if not student:
            raise HTTPException(status_code=404, detail="学生不存在")

        return self.db.query(Behavior).filter(Behavior.student_id == student_id).offset(skip).limit(limit).all()

    async def get_class_students(self, class_id: int) -> List[Student]:
        """获取班级学生列表"""
        return self.db.query(Student).filter(Student.class_id == class_id).all()

    async def get_parent_students(self, parent_id: int) -> List[Student]:
        """获取家长关联的学生列表"""
        return self.db.query(Student).filter(Student.parent_id == parent_id).all()
