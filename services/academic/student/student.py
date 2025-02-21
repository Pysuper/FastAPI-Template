"""
学生服务模块

提供学生相关的业务逻辑处理，包括：
1. 基础的 CRUD 操作
2. 学籍管理
3. 批量处理
4. 数据导入导出
5. 统计分析
6. 关联数据处理
7. 业务规则验证
8. 数据完整性检查
"""

from datetime import date, datetime
from typing import List, Optional, Tuple

from fastapi import HTTPException, UploadFile
from models import Classes, Department, Major
from sqlalchemy import and_, delete, func, or_, select
from sqlalchemy.orm import Session, joinedload
from third.excel.read_write import read_excel, write_excel

from models.student import Student
from schemas.responses.files import ExportResponse, ImportResponse
from schemas.responses.stats import StatsResponse
from schemas.student import (
    StudentCreate,
    StudentFilter,
    StudentResponse,
    StudentUpdate,
)


class StudentService:
    """学生服务类

    提供完整的学生信息管理功能：
    1. 基础信息管理
    2. 学籍状态管理
    3. 批量数据处理
    4. 统计分析报表
    5. 数据导入导出
    6. 关联数据处理
    7. 业务规则验证
    """

    def __init__(self):
        """初始化服务"""
        self.model = Student
        self.searchable_fields = ["name", "student_id", "phone", "email", "id_card"]
        self.filterable_fields = [
            "department_id",
            "major_id",
            "class_id",
            "status",
            "is_registered",
            "education_level",
            "political_status",
            "nationality",
        ]

    async def get_list(
        self,
        db: Session,
        query: Optional[str] = None,
        page: int = 1,
        size: int = 20,
        sort: Optional[str] = None,
        filter_data: Optional[StudentFilter] = None,
    ) -> Tuple[int, List[StudentResponse]]:
        """获取学生列表

        Args:
            db: 数据库会话
            query: 搜索关键词
            page: 页码
            size: 每页数量
            sort: 排序字段
            filter_data: 过滤条件

        Returns:
            总数和学生列表

        Raises:
            HTTPException: 参数错误时抛出
        """
        try:
            # 构建基础查询
            stmt = select(Student).options(
                joinedload(Student.department),
                joinedload(Student.major),
                joinedload(Student.class_),
            )

            # 添加搜索条件
            if query:
                search_conditions = []
                for field in self.searchable_fields:
                    search_conditions.append(getattr(Student, field).ilike(f"%{query}%"))
                stmt = stmt.filter(or_(*search_conditions))

            # 添加过滤条件
            if filter_data:
                filter_conditions = []
                for field in self.filterable_fields:
                    value = getattr(filter_data, field, None)
                    if value is not None:
                        filter_conditions.append(getattr(Student, field) == value)

                # 日期范围过滤
                if filter_data.enrollment_date_start:
                    filter_conditions.append(Student.enrollment_date >= filter_data.enrollment_date_start)
                if filter_data.enrollment_date_end:
                    filter_conditions.append(Student.enrollment_date <= filter_data.enrollment_date_end)

                if filter_conditions:
                    stmt = stmt.filter(and_(*filter_conditions))

            # 添加排序
            if sort:
                if sort.startswith("-"):
                    stmt = stmt.order_by(getattr(Student, sort[1:]).desc())
                else:
                    stmt = stmt.order_by(getattr(Student, sort))
            else:
                stmt = stmt.order_by(Student.id.desc())

            # 获取总数
            total = await db.scalar(select(func.count()).select_from(stmt.subquery()))

            # 分页
            stmt = stmt.offset((page - 1) * size).limit(size)

            # 执行查询
            students = (await db.scalars(stmt)).unique().all()

            return total, [StudentResponse.model_validate(s) for s in students]
        except Exception as e:
            raise HTTPException(status_code=400, detail=f"查询学生列表失败: {str(e)}")

    async def create(self, db: Session, data: StudentCreate) -> StudentResponse:
        """创建学生

        Args:
            db: 数据库会话
            data: 创建数据

        Returns:
            创建的学生

        Raises:
            HTTPException: 创建失败时抛出
        """
        try:
            # 检查学号是否已存在
            if await self.get_by_student_id(db, data.student_id):
                raise HTTPException(status_code=400, detail="学号已存在")

            # 检查身份证号是否已存在
            if await self.get_by_id_card(db, data.id_card):
                raise HTTPException(status_code=400, detail="身份证号已存在")

            # 验证关联数据是否存在
            if not await self.validate_relations(
                db,
                department_id=data.department_id,
                major_id=data.major_id,
                class_id=data.class_id,
            ):
                raise HTTPException(status_code=400, detail="关联数据不存在")

            # 创建学生
            student = Student(**data.model_dump())
            db.add(student)
            await db.commit()
            await db.refresh(student)

            return StudentResponse.model_validate(student)
        except HTTPException:
            raise
        except Exception as e:
            await db.rollback()
            raise HTTPException(status_code=400, detail=f"创建学生失败: {str(e)}")

    async def get(self, db: Session, id: int) -> Optional[StudentResponse]:
        """获取学生详情

        Args:
            db: 数据库会话
            id: 学生ID

        Returns:
            学生详情

        Raises:
            HTTPException: 查询失败时抛出
        """
        try:
            stmt = (
                select(Student)
                .options(
                    joinedload(Student.department),
                    joinedload(Student.major),
                    joinedload(Student.class_),
                )
                .filter(Student.id == id)
            )
            student = (await db.execute(stmt)).scalar_one_or_none()

            if student:
                return StudentResponse.model_validate(student)
            return None
        except Exception as e:
            raise HTTPException(status_code=400, detail=f"获取学生详情失败: {str(e)}")

    async def update(self, db: Session, id: int, data: StudentUpdate) -> Optional[StudentResponse]:
        """更新学生

        Args:
            db: 数据库会话
            id: 学生ID
            data: 更新数据

        Returns:
            更新后的学生

        Raises:
            HTTPException: 更新失败时抛出
        """
        try:
            # 获取学生
            student = await db.get(Student, id)
            if not student:
                return None

            # 检查学号唯一性
            if (
                data.student_id
                and data.student_id != student.student_id
                and await self.get_by_student_id(db, data.student_id)
            ):
                raise HTTPException(status_code=400, detail="学号已存在")

            # 验证关联数据
            if not await self.validate_relations(
                db,
                department_id=data.department_id,
                major_id=data.major_id,
                class_id=data.class_id,
            ):
                raise HTTPException(status_code=400, detail="关联数据不存在")

            # 更新数据
            for key, value in data.model_dump(exclude_unset=True).items():
                setattr(student, key, value)

            await db.commit()
            await db.refresh(student)
            return StudentResponse.model_validate(student)
        except HTTPException:
            raise
        except Exception as e:
            await db.rollback()
            raise HTTPException(status_code=400, detail=f"更新学生失败: {str(e)}")

    async def delete(self, db: Session, id: int) -> bool:
        """删除学生

        Args:
            db: 数据库会话
            id: 学生ID

        Returns:
            是否删除成功

        Raises:
            HTTPException: 删除失败时抛出
        """
        try:
            # 检查是否存在关联数据
            if await self.has_related_records(db, id):
                raise HTTPException(status_code=400, detail="存在关联数据，无法删除")

            result = await db.execute(delete(Student).where(Student.id == id))
            await db.commit()
            return result.rowcount > 0
        except HTTPException:
            raise
        except Exception as e:
            await db.rollback()
            raise HTTPException(status_code=400, detail=f"删除学生失败: {str(e)}")

    async def batch_create(self, db: Session, items: List[StudentCreate]) -> List[StudentResponse]:
        """批量创建学生

        Args:
            db: 数据库会话
            items: 创建数据列表

        Returns:
            创建的学生列表

        Raises:
            HTTPException: 创建失败时抛出
        """
        try:
            # 检查学号唯一性
            student_ids = [item.student_id for item in items]
            if await self.check_student_ids_exist(db, student_ids):
                raise HTTPException(status_code=400, detail="存在重复的学号")

            # 检查身份证号唯一性
            id_cards = [item.id_card for item in items]
            if await self.check_id_cards_exist(db, id_cards):
                raise HTTPException(status_code=400, detail="存在重复的身份证号")

            # 验证关联数据
            for item in items:
                if not await self.validate_relations(
                    db,
                    department_id=item.department_id,
                    major_id=item.major_id,
                    class_id=item.class_id,
                ):
                    raise HTTPException(status_code=400, detail="关联数据不存在")

            # 批量创建
            students = [Student(**item.model_dump()) for item in items]
            db.add_all(students)
            await db.commit()
            for student in students:
                await db.refresh(student)

            return [StudentResponse.model_validate(s) for s in students]
        except HTTPException:
            raise
        except Exception as e:
            await db.rollback()
            raise HTTPException(status_code=400, detail=f"批量创建学生失败: {str(e)}")

    async def batch_update(self, db: Session, items: List[StudentUpdate]) -> List[StudentResponse]:
        """批量更新学生

        Args:
            db: 数据库会话
            items: 更新数据列表

        Returns:
            更新后的学生列表

        Raises:
            HTTPException: 更新失败时抛出
        """
        try:
            updated = []
            for item in items:
                student = await db.get(Student, item.id)
                if student:
                    # 检查学号唯一性
                    if (
                        item.student_id
                        and item.student_id != student.student_id
                        and await self.get_by_student_id(db, item.student_id)
                    ):
                        raise HTTPException(status_code=400, detail=f"学号 {item.student_id} 已存在")

                    # 验证关联数据
                    if not await self.validate_relations(
                        db,
                        department_id=item.department_id,
                        major_id=item.major_id,
                        class_id=item.class_id,
                    ):
                        raise HTTPException(status_code=400, detail="关联数据不存在")

                    # 更新数据
                    for key, value in item.model_dump(exclude_unset=True).items():
                        setattr(student, key, value)
                    updated.append(student)

            await db.commit()
            for student in updated:
                await db.refresh(student)
            return [StudentResponse.model_validate(s) for s in updated]
        except HTTPException:
            raise
        except Exception as e:
            await db.rollback()
            raise HTTPException(status_code=400, detail=f"批量更新学生失败: {str(e)}")

    async def batch_delete(self, db: Session, ids: List[int]) -> bool:
        """批量删除学生

        Args:
            db: 数据库会话
            ids: 学生ID列表

        Returns:
            是否全部删除成功

        Raises:
            HTTPException: 删除失败时抛出
        """
        try:
            # 检查是否存在关联数据
            for id in ids:
                if await self.has_related_records(db, id):
                    raise HTTPException(status_code=400, detail=f"学生 {id} 存在关联数据，无法删除")

            result = await db.execute(delete(Student).where(Student.id.in_(ids)))
            await db.commit()
            return result.rowcount == len(ids)
        except HTTPException:
            raise
        except Exception as e:
            await db.rollback()
            raise HTTPException(status_code=400, detail=f"批量删除学生失败: {str(e)}")

    async def import_data(self, db: Session, file: UploadFile) -> ImportResponse:
        """导入学生数据

        Args:
            db: 数据库会话
            file: 上传的文件

        Returns:
            导入结果

        Raises:
            HTTPException: 导入失败时抛出
        """
        try:
            # 读取Excel文件
            data = await read_excel(file, sheet_name="学生信息")

            total = len(data)
            success = 0
            failed = 0
            errors = []

            # 批量处理数据
            for i, row in enumerate(data, start=2):
                try:
                    # 转换为创建模型
                    student_data = StudentCreate(
                        name=row["姓名"],
                        student_id=row["学号"],
                        id_card=row["身份证号"],
                        gender=row["性别"],
                        birth_date=datetime.strptime(row["出生日期"], "%Y-%m-%d"),
                        phone=row["电话"],
                        email=row["邮箱"],
                        department_id=int(row["院系ID"]),
                        major_id=int(row["专业ID"]),
                        class_id=int(row["班级ID"]),
                        enrollment_date=datetime.strptime(row["入学日期"], "%Y-%m-%d"),
                        education_level=row["学历层次"],
                        study_length=int(row["学制"]),
                    )

                    # 创建学生
                    await self.create(db, student_data)
                    success += 1
                except Exception as e:
                    failed += 1
                    errors.append(f"第{i}行: {str(e)}")

            return ImportResponse(
                total=total,
                success=success,
                failed=failed,
                errors=errors,
            )
        except Exception as e:
            raise HTTPException(status_code=400, detail=f"导入学生数据失败: {str(e)}")

    async def export_data(
        self,
        db: Session,
        query: Optional[str] = None,
        filter_data: Optional[StudentFilter] = None,
    ) -> ExportResponse:
        """导出学生数据

        Args:
            db: 数据库会话
            query: 搜索关键词
            filter_data: 过滤条件

        Returns:
            导出结果

        Raises:
            HTTPException: 导出失败时抛出
        """
        try:
            # 获取数据
            total, students = await self.get_list(
                db,
                query=query,
                filter_data=filter_data,
                page=1,
                size=10000,  # 限制导出数量
            )

            # 转换为Excel格式
            data = []
            for student in students:
                data.append(
                    {
                        "姓名": student.name,
                        "学号": student.student_id,
                        "身份证号": student.id_card,
                        "性别": student.gender.value,
                        "出生日期": student.birth_date.strftime("%Y-%m-%d"),
                        "电话": student.phone or "",
                        "邮箱": student.email or "",
                        "院系": student.department.name if student.department else "",
                        "专业": student.major.name if student.major else "",
                        "班级": student.class_.name if student.class_ else "",
                        "入学日期": student.enrollment_date.strftime("%Y-%m-%d"),
                        "学历层次": student.education_level,
                        "学制": student.study_length,
                        "状态": student.status.value,
                        "是否注册": "是" if student.is_registered else "否",
                    }
                )

            # 生成Excel文件
            filename = f"学生信息_{datetime.now().strftime('%Y%m%d%H%M%S')}.xlsx"
            filepath = f"static/exports/{filename}"
            await write_excel(data, filepath, sheet_name="学生信息")

            return ExportResponse(
                url=f"/static/exports/{filename}",
                filename=filename,
                size=len(data),
            )
        except Exception as e:
            raise HTTPException(status_code=400, detail=f"导出学生数据失败: {str(e)}")

    async def get_stats(
        self,
        db: Session,
        group_by: Optional[str] = None,
        start_date: Optional[date] = None,
        end_date: Optional[date] = None,
        filter_data: Optional[StudentFilter] = None,
    ) -> StatsResponse:
        """获取统计数据

        Args:
            db: 数据库会话
            group_by: 分组字段
            start_date: 开始日期
            end_date: 结束日期
            filter_data: 过滤条件

        Returns:
            统计结果

        Raises:
            HTTPException: 统计失败时抛出
        """
        try:
            # 构建基础查询
            stmt = select(Student)

            # 添加过滤条件
            if filter_data:
                filter_conditions = []
                for field in self.filterable_fields:
                    value = getattr(filter_data, field, None)
                    if value is not None:
                        filter_conditions.append(getattr(Student, field) == value)

                if filter_conditions:
                    stmt = stmt.filter(and_(*filter_conditions))

            # 添加日期范围
            if start_date:
                stmt = stmt.filter(Student.enrollment_date >= start_date)
            if end_date:
                stmt = stmt.filter(Student.enrollment_date <= end_date)

            # 获取总数
            total = await db.scalar(select(func.count()).select_from(stmt.subquery()))

            # 分组统计
            groups = []
            summary = {}

            if group_by:
                group_stmt = (
                    select(getattr(Student, group_by), func.count().label("count"))
                    .select_from(stmt.subquery())
                    .group_by(getattr(Student, group_by))
                )

                results = await db.execute(group_stmt)
                for value, count in results:
                    groups.append(
                        {
                            "name": str(value),
                            "value": count,
                        }
                    )

            # 计算汇总数据
            summary = {
                "total": total,
                "active": await db.scalar(
                    select(func.count()).select_from(stmt.subquery()).filter(Student.status == "active")
                ),
                "registered": await db.scalar(
                    select(func.count()).select_from(stmt.subquery()).filter(Student.is_registered == True)
                ),
            }

            return StatsResponse(
                total=total,
                groups=groups,
                summary=summary,
            )
        except Exception as e:
            raise HTTPException(status_code=400, detail=f"获取统计数据失败: {str(e)}")

    # 辅助方法
    async def get_by_student_id(self, db: Session, student_id: str) -> Optional[Student]:
        """根据学号获取学生"""
        return await db.scalar(select(Student).filter(Student.student_id == student_id))

    async def get_by_id_card(self, db: Session, id_card: str) -> Optional[Student]:
        """根据身份证号获取学生"""
        return await db.scalar(select(Student).filter(Student.id_card == id_card))

    async def check_student_ids_exist(self, db: Session, student_ids: List[str]) -> bool:
        """检查学号是否存在"""
        count = await db.scalar(select(func.count()).select_from(Student).filter(Student.student_id.in_(student_ids)))
        return count > 0

    async def check_id_cards_exist(self, db: Session, id_cards: List[str]) -> bool:
        """检查身份证号是否存在"""
        count = await db.scalar(select(func.count()).select_from(Student).filter(Student.id_card.in_(id_cards)))
        return count > 0

    async def validate_relations(
        self,
        db: Session,
        department_id: Optional[int] = None,
        major_id: Optional[int] = None,
        class_id: Optional[int] = None,
    ) -> bool:
        """验证关联数据是否存在"""
        if department_id:
            dept = await db.get(Department, department_id)
            if not dept:
                return False

        if major_id:
            major = await db.get(Major, major_id)
            if not major:
                return False

        if class_id:
            class_ = db.get(Classes, class_id)
            if not class_:
                return False

        return True

    async def has_related_records(self, db: Session, student_id: int) -> bool:
        """检查是否存在关联数据"""
        student = await db.get(Student, student_id)
        if not student:
            return False

        # 检查选课记录
        if len(student.enrollments) > 0:
            return True

        # 检查成绩记录
        if len(student.grades) > 0:
            return True

        # 检查奖惩记录
        if len(student.rewards) > 0 or len(student.punishments) > 0:
            return True

        return False
