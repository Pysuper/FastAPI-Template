from typing import List, Optional

from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.orm import joinedload

from core.repositories import BaseRepository
from models.school import Class, Course, CourseEnrollment, Department, Major, Student, Teacher
from schemas.school import (
    ClassCreate,
    ClassUpdate,
    CourseCreate,
    CourseUpdate,
    DepartmentCreate,
    DepartmentUpdate,
    MajorCreate,
    MajorUpdate,
    StudentCreate,
    StudentUpdate,
    TeacherCreate,
    TeacherUpdate,
)


class DepartmentRepository(BaseRepository[Department, DepartmentCreate, DepartmentUpdate]):
    """院系仓储类"""

    def __init__(self):
        super().__init__(Department)

    async def get_by_code(self, db: AsyncSession, code: str) -> Optional[Department]:
        """通过院系代码获取院系"""
        result = await db.execute(select(self.model).where(self.model.code == code))
        return result.scalar_one_or_none()

    async def get_with_relations(self, db: AsyncSession, department_id: int) -> Optional[Department]:
        """获取院系及其关联数据"""
        result = await db.execute(
            select(self.model)
            .options(joinedload(self.model.majors), joinedload(self.model.teachers))
            .where(self.model.id == department_id)
        )
        return result.scalar_one_or_none()


class MajorRepository(BaseRepository[Major, MajorCreate, MajorUpdate]):
    """专业仓储类"""

    def __init__(self):
        super().__init__(Major)

    async def get_by_code(self, db: AsyncSession, code: str) -> Optional[Major]:
        """通过专业代码获取专业"""
        result = await db.execute(select(self.model).where(self.model.code == code))
        return result.scalar_one_or_none()

    async def get_by_department(self, db: AsyncSession, department_id: int) -> List[Major]:
        """获取院系下的所有专业"""
        result = await db.execute(select(self.model).where(self.model.department_id == department_id))
        return result.scalars().all()


class ClassRepository(BaseRepository[Class, ClassCreate, ClassUpdate]):
    """班级仓储类"""

    def __init__(self):
        super().__init__(Class)

    async def get_by_code(self, db: AsyncSession, code: str) -> Optional[Class]:
        """通过班级代码获取班级"""
        result = await db.execute(select(self.model).where(self.model.code == code))
        return result.scalar_one_or_none()

    async def get_by_major(self, db: AsyncSession, major_id: int) -> List[Class]:
        """获取专业下的所有班级"""
        result = await db.execute(select(self.model).where(self.model.major_id == major_id))
        return result.scalars().all()

    async def get_by_teacher(self, db: AsyncSession, teacher_id: int) -> Optional[Class]:
        """获取教师管理的班级"""
        result = await db.execute(select(self.model).where(self.model.teacher_id == teacher_id))
        return result.scalar_one_or_none()


class TeacherRepository(BaseRepository[Teacher, TeacherCreate, TeacherUpdate]):
    """教师仓储类"""

    def __init__(self):
        super().__init__(Teacher)

    async def get_by_code(self, db: AsyncSession, code: str) -> Optional[Teacher]:
        """通过工号获取教师"""
        result = await db.execute(select(self.model).where(self.model.code == code))
        return result.scalar_one_or_none()

    async def get_by_department(self, db: AsyncSession, department_id: int) -> List[Teacher]:
        """获取院系下的所有教师"""
        result = await db.execute(select(self.model).where(self.model.department_id == department_id))
        return result.scalars().all()

    async def get_with_courses(self, db: AsyncSession, teacher_id: int) -> Optional[Teacher]:
        """获取教师及其课程"""
        result = await db.execute(
            select(self.model).options(joinedload(self.model.courses)).where(self.model.id == teacher_id)
        )
        return result.scalar_one_or_none()


class StudentRepository(BaseRepository[Student, StudentCreate, StudentUpdate]):
    """学生仓储类"""

    def __init__(self):
        super().__init__(Student)

    async def get_by_code(self, db: AsyncSession, code: str) -> Optional[Student]:
        """通过学号获取学生"""
        result = await db.execute(select(self.model).where(self.model.code == code))
        return result.scalar_one_or_none()

    async def get_by_class(self, db: AsyncSession, class_id: int) -> List[Student]:
        """获取班级下的所有学生"""
        result = await db.execute(select(self.model).where(self.model.class_id == class_id))
        return result.scalars().all()

    async def get_with_enrollments(self, db: AsyncSession, student_id: int) -> Optional[Student]:
        """获取学生及其选课记录"""
        result = await db.execute(
            select(self.model)
            .options(joinedload(self.model.enrollments).joinedload(CourseEnrollment.course))
            .where(self.model.id == student_id)
        )
        return result.scalar_one_or_none()


class CourseRepository(BaseRepository[Course, CourseCreate, CourseUpdate]):
    """课程仓储类"""

    def __init__(self):
        super().__init__(Course)

    async def get_by_code(self, db: AsyncSession, code: str) -> Optional[Course]:
        """通过课程代码获取课程"""
        result = await db.execute(select(self.model).where(self.model.code == code))
        return result.scalar_one_or_none()

    async def get_by_major(self, db: AsyncSession, major_id: int) -> List[Course]:
        """获取专业下的所有课程"""
        result = await db.execute(select(self.model).where(self.model.major_id == major_id))
        return result.scalars().all()

    async def get_by_teacher(self, db: AsyncSession, teacher_id: int) -> List[Course]:
        """获取教师的所有课程"""
        result = await db.execute(select(self.model).where(self.model.teacher_id == teacher_id))
        return result.scalars().all()

    async def get_with_enrollments(self, db: AsyncSession, course_id: int) -> Optional[Course]:
        """获取课程及其选课记录"""
        result = await db.execute(
            select(self.model)
            .options(joinedload(self.model.enrollments).joinedload(CourseEnrollment.student))
            .where(self.model.id == course_id)
        )
        return result.scalar_one_or_none()


# 创建仓储实例
department_repository = DepartmentRepository()
major_repository = MajorRepository()
class_repository = ClassRepository()
teacher_repository = TeacherRepository()
student_repository = StudentRepository()
course_repository = CourseRepository()
