from typing import Dict, Optional

from fastapi import HTTPException, status
from sqlalchemy import and_, func, select
from sqlalchemy.ext.asyncio import AsyncSession

from core.cache.manager.manager import cache_manager
from models.grade import Grade, GradeItem, GradeRule
from models.school import Course, Student, Teacher
from schemas.common import PaginationParams
from schemas.grade import GradeCreate, GradeRuleCreate, GradeRuleUpdate, GradeStatistics, GradeUpdate


class GradeService:
    """成绩服务类"""

    async def create_grade(self, db: AsyncSession, grade_in: GradeCreate) -> Grade:
        """创建成绩"""
        # 验证学生、课程和教师是否存在
        student = await db.get(Student, grade_in.student_id)
        if not student:
            raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="学生不存在")

        course = await db.get(Course, grade_in.course_id)
        if not course:
            raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="课程不存在")

        teacher = await db.get(Teacher, grade_in.teacher_id)
        if not teacher:
            raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="教师不存在")

        # 检查是否已存在成绩记录
        stmt = select(Grade).where(and_(Grade.student_id == grade_in.student_id, Grade.course_id == grade_in.course_id))
        result = await db.execute(stmt)
        if result.scalar_one_or_none():
            raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail="该学生的课程成绩已存在")

        # 创建成绩记录
        grade = Grade(
            student_id=grade_in.student_id,
            course_id=grade_in.course_id,
            teacher_id=grade_in.teacher_id,
            attendance_score=grade_in.attendance_score,
            homework_score=grade_in.homework_score,
            midterm_score=grade_in.midterm_score,
            final_score=grade_in.final_score,
            total_score=grade_in.total_score,
            status=grade_in.status,
            notes=grade_in.notes,
        )
        db.add(grade)
        await db.commit()
        await db.refresh(grade)

        # 创建成绩项目
        for item_in in grade_in.items:
            item = GradeItem(
                grade_id=grade.id,
                name=item_in.name,
                description=item_in.description,
                score=item_in.score,
                weight=item_in.weight,
                type=item_in.type,
            )
            db.add(item)

        await db.commit()
        await db.refresh(grade)
        return grade

    async def update_grade(self, db: AsyncSession, grade_id: int, grade_in: GradeUpdate) -> Grade:
        """更新成绩"""
        # 获取成绩记录
        grade = await db.get(Grade, grade_id)
        if not grade:
            raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="成绩记录不存在")

        # 只有草稿状态的成绩可以更新
        if grade.status != "draft":
            raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail="只能更新草稿状态的成绩")

        # 更新基本信息
        for field, value in grade_in.dict(exclude_unset=True).items():
            if field != "items":
                setattr(grade, field, value)

        # 更新成绩项目
        if grade_in.items:
            # 删除原有项目
            stmt = select(GradeItem).where(GradeItem.grade_id == grade_id)
            result = await db.execute(stmt)
            for item in result.scalars().all():
                await db.delete(item)

            # 创建新的项目
            for item_in in grade_in.items:
                item = GradeItem(
                    grade_id=grade.id,
                    name=item_in.name,
                    description=item_in.description,
                    score=item_in.score,
                    weight=item_in.weight,
                    type=item_in.type,
                )
                db.add(item)

        await db.commit()
        await db.refresh(grade)
        return grade

    async def get_grade(self, db: AsyncSession, grade_id: int) -> Grade:
        """获取成绩"""
        grade = await db.get(Grade, grade_id)
        if not grade:
            raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="成绩记录不存在")
        return grade

    async def get_grades(
        self,
        db: AsyncSession,
        pagination: PaginationParams,
        student_id: Optional[int] = None,
        course_id: Optional[int] = None,
        teacher_id: Optional[int] = None,
        status: Optional[str] = None,
    ) -> Dict:
        """获取成绩列表"""
        query = select(Grade)

        if student_id:
            query = query.where(Grade.student_id == student_id)
        if course_id:
            query = query.where(Grade.course_id == course_id)
        if teacher_id:
            query = query.where(Grade.teacher_id == teacher_id)
        if status:
            query = query.where(Grade.status == status)

        # 分页
        total = await db.scalar(select(func.count()).select_from(query.subquery()))
        query = query.offset(pagination.skip).limit(pagination.limit)

        result = await db.execute(query)
        grades = result.scalars().all()

        return {"total": total, "items": grades, "page": pagination.page, "size": pagination.limit}

    async def delete_grade(self, db: AsyncSession, grade_id: int) -> bool:
        """删除成绩"""
        grade = await db.get(Grade, grade_id)
        if not grade:
            raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="成绩记录不存在")

        # 只能删除草稿状态的成绩
        if grade.status != "draft":
            raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail="只能删除草稿状态的成绩")

        await db.delete(grade)
        await db.commit()
        return True

    async def publish_grade(self, db: AsyncSession, grade_id: int) -> Grade:
        """发布成绩"""
        grade = await db.get(Grade, grade_id)
        if not grade:
            raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="成绩记录不存在")

        # 只能发布草稿状态的成绩
        if grade.status != "draft":
            raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail="只能发布草稿状态的成绩")

        # 检查是否有成绩项目
        stmt = select(GradeItem).where(GradeItem.grade_id == grade_id)
        result = await db.execute(stmt)
        if not result.scalars().all():
            raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail="成绩记录没有详细内容")

        grade.status = "published"
        await db.commit()
        await db.refresh(grade)
        return grade

    async def archive_grade(self, db: AsyncSession, grade_id: int) -> Grade:
        """归档成绩"""
        grade = await db.get(Grade, grade_id)
        if not grade:
            raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="成绩记录不存在")

        # 只能归档已发布状态的成绩
        if grade.status != "published":
            raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail="只能归档已发布状态的成绩")

        grade.status = "archived"
        await db.commit()
        await db.refresh(grade)
        return grade

    async def create_grade_rule(self, db: AsyncSession, rule_in: GradeRuleCreate) -> GradeRule:
        """创建成绩规则"""
        # 验证课程是否存在
        course = await db.get(Course, rule_in.course_id)
        if not course:
            raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="课程不存在")

        # 检查是否已存在规则
        stmt = select(GradeRule).where(GradeRule.course_id == rule_in.course_id)
        result = await db.execute(stmt)
        if result.scalar_one_or_none():
            raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail="课程已存在成绩规则")

        # 验证权重总和是否为1
        total_weight = (
            rule_in.attendance_weight + rule_in.homework_weight + rule_in.midterm_weight + rule_in.final_weight
        )
        if abs(total_weight - 1.0) > 0.0001:  # 使用小数点比较
            raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail="成绩权重总和必须为1")

        rule = GradeRule(
            course_id=rule_in.course_id,
            name=rule_in.name,
            description=rule_in.description,
            attendance_weight=rule_in.attendance_weight,
            homework_weight=rule_in.homework_weight,
            midterm_weight=rule_in.midterm_weight,
            final_weight=rule_in.final_weight,
            pass_score=rule_in.pass_score,
            is_active=rule_in.is_active,
        )

        db.add(rule)
        await db.commit()
        await db.refresh(rule)
        return rule

    async def update_grade_rule(self, db: AsyncSession, rule_id: int, rule_in: GradeRuleUpdate) -> GradeRule:
        """更新成绩规则"""
        rule = await db.get(GradeRule, rule_id)
        if not rule:
            raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="成绩规则不存在")

        # 验证权重总和是否为1
        total_weight = (
            rule_in.attendance_weight + rule_in.homework_weight + rule_in.midterm_weight + rule_in.final_weight
        )
        if abs(total_weight - 1.0) > 0.0001:  # 使用小数点比较
            raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail="成绩权重总和必须为1")

        # 更新字段
        for field, value in rule_in.dict(exclude_unset=True).items():
            setattr(rule, field, value)

        await db.commit()
        await db.refresh(rule)
        return rule

    async def get_grade_statistics(self, db: AsyncSession, course_id: int) -> GradeStatistics:
        """获取成绩统计信息"""
        # 从缓存获取统计信息
        cache_key = f"grade_stats:{course_id}"
        cached_data = await cache_manager.get(cache_key)
        if cached_data is not None:
            return GradeStatistics(**cached_data)

        # 获取成绩规则
        stmt = select(GradeRule).where(GradeRule.course_id == course_id)
        result = await db.execute(stmt)
        rule = result.scalar_one_or_none()
        if not rule:
            raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="课程没有成绩规则")

        # 获取所有已发布的成绩
        stmt = select(Grade).where(and_(Grade.course_id == course_id, Grade.status == "published"))
        result = await db.execute(stmt)
        grades = result.scalars().all()

        if not grades:
            raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="没有已发布的成绩记录")

        # 计算统计信息
        total = len(grades)
        pass_count = len([g for g in grades if g.total_score >= rule.pass_score])
        fail_count = total - pass_count
        highest_score = max(g.total_score for g in grades)
        lowest_score = min(g.total_score for g in grades)
        average_score = sum(g.total_score for g in grades) / total

        # 计算分数段分布
        score_ranges = {"90-100": 0, "80-89": 0, "70-79": 0, "60-69": 0, "0-59": 0}
        for grade in grades:
            score = grade.total_score
            if score >= 90:
                score_ranges["90-100"] += 1
            elif score >= 80:
                score_ranges["80-89"] += 1
            elif score >= 70:
                score_ranges["70-79"] += 1
            elif score >= 60:
                score_ranges["60-69"] += 1
            else:
                score_ranges["0-59"] += 1

        stats = GradeStatistics(
            total=total,
            pass_count=pass_count,
            fail_count=fail_count,
            highest_score=highest_score,
            lowest_score=lowest_score,
            average_score=average_score,
            score_distribution=score_ranges,
        )

        # 更新缓存
        await cache_manager.set(cache_key, stats.dict(), expire=300)  # 缓存5分钟

        return stats


# 创建服务实例
grade_service = GradeService()
