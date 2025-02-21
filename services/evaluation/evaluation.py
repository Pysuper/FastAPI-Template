from datetime import datetime
from typing import Dict, Optional

from fastapi import HTTPException, status
from sqlalchemy import and_, func, select
from sqlalchemy.ext.asyncio import AsyncSession

from core.cache.managers.manager import cache_manager
from db.metrics.pagination import PaginationParams
from models.evaluation import EvaluationIndicator, EvaluationRecord, EvaluationRule
from models.school import Course, Student, Teacher
from schemas.evaluation import (
    EvaluationIndicatorCreate,
    EvaluationIndicatorUpdate,
    EvaluationRecordCreate,
    EvaluationRecordUpdate,
    EvaluationRuleCreate,
    EvaluationRuleUpdate,
    EvaluationStatistics,
)


class EvaluationService:
    """教学评价服务类"""

    async def create_indicator(
        self,
        db: AsyncSession,
        indicator_in: EvaluationIndicatorCreate,
    ) -> EvaluationIndicator:
        """创建评价指标"""
        indicator = EvaluationIndicator(**indicator_in.dict())
        db.add(indicator)
        await db.commit()
        await db.refresh(indicator)
        return indicator

    async def update_indicator(
        self, db: AsyncSession, indicator_id: int, indicator_in: EvaluationIndicatorUpdate
    ) -> EvaluationIndicator:
        """更新评价指标"""
        indicator = await db.get(EvaluationIndicator, indicator_id)
        if not indicator:
            raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="评价指标不存在")

        # 更新字段
        for field, value in indicator_in.dict(exclude_unset=True).items():
            setattr(indicator, field, value)

        await db.commit()
        await db.refresh(indicator)
        return indicator

    async def get_indicator(self, db: AsyncSession, indicator_id: int) -> EvaluationIndicator:
        """获取评价指标"""
        indicator = await db.get(EvaluationIndicator, indicator_id)
        if not indicator:
            raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="评价指标不存在")
        return indicator

    async def get_indicators(
        self,
        db: AsyncSession,
        pagination: PaginationParams,
        type: Optional[str] = None,
        is_active: Optional[bool] = None,
    ) -> Dict:
        """获取评价指标列表"""
        query = select(EvaluationIndicator)

        if type:
            query = query.where(EvaluationIndicator.type == type)
        if is_active is not None:
            query = query.where(EvaluationIndicator.is_active == is_active)

        # 分页
        total = await db.scalar(select(func.count()).select_from(query.subquery()))
        query = query.offset(pagination.skip).limit(pagination.limit)

        result = await db.execute(query)
        indicators = result.scalars().all()

        return {"total": total, "items": indicators, "page": pagination.page, "size": pagination.limit}

    async def create_rule(self, db: AsyncSession, rule_in: EvaluationRuleCreate) -> EvaluationRule:
        """创建评价规则"""
        # 验证课程或教师是否存在
        if rule_in.course_id:
            course = await db.get(Course, rule_in.course_id)
            if not course:
                raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="课程不存在")

        if rule_in.teacher_id:
            teacher = await db.get(Teacher, rule_in.teacher_id)
            if not teacher:
                raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="教师不存在")

        rule = EvaluationRule(**rule_in.dict())
        db.add(rule)
        await db.commit()
        await db.refresh(rule)
        return rule

    async def update_rule(self, db: AsyncSession, rule_id: int, rule_in: EvaluationRuleUpdate) -> EvaluationRule:
        """更新评价规则"""
        rule = await db.get(EvaluationRule, rule_id)
        if not rule:
            raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="评价规则不存在")

        # 更新字段
        for field, value in rule_in.dict(exclude_unset=True).items():
            setattr(rule, field, value)

        await db.commit()
        await db.refresh(rule)
        return rule

    async def get_rule(self, db: AsyncSession, rule_id: int) -> EvaluationRule:
        """获取评价规则"""
        rule = await db.get(EvaluationRule, rule_id)
        if not rule:
            raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="评价规则��存在")
        return rule

    async def get_rules(
        self,
        db: AsyncSession,
        pagination: PaginationParams,
        target_type: Optional[str] = None,
        course_id: Optional[int] = None,
        teacher_id: Optional[int] = None,
        is_active: Optional[bool] = None,
    ) -> Dict:
        """获取评价规则列表"""
        query = select(EvaluationRule)

        if target_type:
            query = query.where(EvaluationRule.target_type == target_type)
        if course_id:
            query = query.where(EvaluationRule.course_id == course_id)
        if teacher_id:
            query = query.where(EvaluationRule.teacher_id == teacher_id)
        if is_active is not None:
            query = query.where(EvaluationRule.is_active == is_active)

        # 分页
        total = await db.scalar(select(func.count()).select_from(query.subquery()))
        query = query.offset(pagination.skip).limit(pagination.limit)

        result = await db.execute(query)
        rules = result.scalars().all()

        return {"total": total, "items": rules, "page": pagination.page, "size": pagination.limit}

    async def create_evaluation(self, db: AsyncSession, evaluation_in: EvaluationRecordCreate) -> EvaluationRecord:
        """创建评价记录"""
        # 验证学生、课程和教师是否存在
        student = await db.get(Student, evaluation_in.student_id)
        if not student:
            raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="学生不存在")

        course = await db.get(Course, evaluation_in.course_id)
        if not course:
            raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="课程不存在")

        teacher = await db.get(Teacher, evaluation_in.teacher_id)
        if not teacher:
            raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="教师不存在")

        # 验证评价指标是否存在
        indicator = await db.get(EvaluationIndicator, evaluation_in.indicator_id)
        if not indicator:
            raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="评价指标不存在")

        # 验证评价规则是否存在
        rule = await db.get(EvaluationRule, evaluation_in.rule_id)
        if not rule:
            raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="评价规则不存在")

        # 检查评价时间
        now = datetime.now()
        if now < rule.start_date or now > rule.end_date:
            raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail="不在评价时间范围内")

        # 检查是否已评价
        stmt = select(EvaluationRecord).where(
            and_(
                EvaluationRecord.student_id == evaluation_in.student_id,
                EvaluationRecord.course_id == evaluation_in.course_id,
                EvaluationRecord.teacher_id == evaluation_in.teacher_id,
                EvaluationRecord.indicator_id == evaluation_in.indicator_id,
                EvaluationRecord.rule_id == evaluation_in.rule_id,
            )
        )
        result = await db.execute(stmt)
        if result.scalar_one_or_none():
            raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail="已经评价过了")

        # 检查评价内容
        if rule.min_word_count > 0 and (not evaluation_in.comment or len(evaluation_in.comment) < rule.min_word_count):
            raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail=f"评价内容不能少于{rule.min_word_count}字")

        # 检查匿名设置
        if evaluation_in.is_anonymous and not rule.allow_anonymous:
            raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail="不允许匿名评价")

        evaluation = EvaluationRecord(**evaluation_in.dict())
        db.add(evaluation)
        await db.commit()
        await db.refresh(evaluation)

        # 更新缓存
        await self.update_evaluation_statistics_cache(
            db, course_id=evaluation_in.course_id, teacher_id=evaluation_in.teacher_id
        )

        return evaluation

    async def update_evaluation(
        self, db: AsyncSession, evaluation_id: int, evaluation_in: EvaluationRecordUpdate
    ) -> EvaluationRecord:
        """更新评价记录"""
        evaluation = await db.get(EvaluationRecord, evaluation_id)
        if not evaluation:
            raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="评价记录不存在")

        # 只能更新草稿状态的评价
        if evaluation.status != "draft":
            raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail="只能更新草稿状态的评价")

        # 更新字段
        for field, value in evaluation_in.dict(exclude_unset=True).items():
            setattr(evaluation, field, value)

        # 如果状态变更为已提交，设置提交时间
        if evaluation_in.status == "submitted":
            evaluation.submit_date = datetime.now()

        await db.commit()
        await db.refresh(evaluation)

        # 如果状态变更为已提交，更新缓存
        if evaluation_in.status == "submitted":
            await self.update_evaluation_statistics_cache(
                db, course_id=evaluation.course_id, teacher_id=evaluation.teacher_id
            )

        return evaluation

    async def get_evaluation(self, db: AsyncSession, evaluation_id: int) -> EvaluationRecord:
        """获取评价记录"""
        evaluation = await db.get(EvaluationRecord, evaluation_id)
        if not evaluation:
            raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="评价记录不存在")
        return evaluation

    async def get_evaluations(
        self,
        db: AsyncSession,
        pagination: PaginationParams,
        student_id: Optional[int] = None,
        course_id: Optional[int] = None,
        teacher_id: Optional[int] = None,
        indicator_id: Optional[int] = None,
        rule_id: Optional[int] = None,
        status: Optional[str] = None,
        is_anonymous: Optional[bool] = None,
    ) -> Dict:
        """获取评价记录列表"""
        query = select(EvaluationRecord)

        if student_id:
            query = query.where(EvaluationRecord.student_id == student_id)
        if course_id:
            query = query.where(EvaluationRecord.course_id == course_id)
        if teacher_id:
            query = query.where(EvaluationRecord.teacher_id == teacher_id)
        if indicator_id:
            query = query.where(EvaluationRecord.indicator_id == indicator_id)
        if rule_id:
            query = query.where(EvaluationRecord.rule_id == rule_id)
        if status:
            query = query.where(EvaluationRecord.status == status)
        if is_anonymous is not None:
            query = query.where(EvaluationRecord.is_anonymous == is_anonymous)

        # 分页
        total = await db.scalar(select(func.count()).select_from(query.subquery()))
        query = query.offset(pagination.skip).limit(pagination.limit)

        result = await db.execute(query)
        evaluations = result.scalars().all()

        return {"total": total, "items": evaluations, "page": pagination.page, "size": pagination.limit}

    async def get_evaluation_statistics(
        self, db: AsyncSession, course_id: Optional[int] = None, teacher_id: Optional[int] = None
    ) -> EvaluationStatistics:
        """获取评价统计信息"""
        # 从缓存获取统计信息
        cache_key = f"evaluation_stats:{course_id or 'all'}:{teacher_id or 'all'}"
        cached_data = await cache_manager.get(cache_key)
        if cached_data is not None:
            return EvaluationStatistics(**cached_data)

        # 构建查询
        query = select(EvaluationRecord).where(EvaluationRecord.status == "submitted")
        if course_id:
            query = query.where(EvaluationRecord.course_id == course_id)
        if teacher_id:
            query = query.where(EvaluationRecord.teacher_id == teacher_id)

        result = await db.execute(query)
        evaluations = result.scalars().all()

        # 计算统计信息
        total_count = len(evaluations)
        if total_count == 0:
            return EvaluationStatistics(
                total_count=0,
                average_score=0.0,
                score_distribution={},
                indicator_scores={},
                comment_count=0,
                anonymous_count=0,
            )

        # 计算平均分
        total_score = sum(e.score for e in evaluations)
        average_score = total_score / total_count

        # 计算分数段分布
        score_distribution = {"0-60": 0, "61-70": 0, "71-80": 0, "81-90": 0, "91-100": 0}

        for e in evaluations:
            if e.score <= 60:
                score_distribution["0-60"] += 1
            elif e.score <= 70:
                score_distribution["61-70"] += 1
            elif e.score <= 80:
                score_distribution["71-80"] += 1
            elif e.score <= 90:
                score_distribution["81-90"] += 1
            else:
                score_distribution["91-100"] += 1

        # 计算各指标平均分
        indicator_scores = {}
        for e in evaluations:
            if e.indicator.type not in indicator_scores:
                indicator_scores[e.indicator.type] = []
            indicator_scores[e.indicator.type].append(e.score)

        for type, scores in indicator_scores.items():
            indicator_scores[type] = sum(scores) / len(scores)

        # 统计评价内容和匿名评价
        comment_count = len([e for e in evaluations if e.comment])
        anonymous_count = len([e for e in evaluations if e.is_anonymous])

        stats = EvaluationStatistics(
            total_count=total_count,
            average_score=average_score,
            score_distribution=score_distribution,
            indicator_scores=indicator_scores,
            comment_count=comment_count,
            anonymous_count=anonymous_count,
        )

        # 更新缓存
        await cache_manager.set(cache_key, stats.dict(), expire=300)  # 缓存5分钟

        return stats

    async def update_evaluation_statistics_cache(
        self, db: AsyncSession, course_id: Optional[int] = None, teacher_id: Optional[int] = None
    ):
        """更新评价统计信息缓存"""
        cache_key = f"evaluation_stats:{course_id or 'all'}:{teacher_id or 'all'}"
        await cache_manager.delete(cache_key)


# 创建服务实例
evaluation_service = EvaluationService()
