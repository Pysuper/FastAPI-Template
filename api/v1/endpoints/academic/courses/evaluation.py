from typing import List, Optional

from fastapi import APIRouter, Depends, Query, Path, Body, UploadFile, File, HTTPException
from oss2.exceptions import status
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.orm import Session

from db.metrics.pagination import PageResponse
from core.dependencies.auth import get_current_active_user, get_current_user
from core.dependencies import async_db
from exceptions.database.query import QueryResultException
from models.user import User
from schemas.base.pagination import PaginationParams
from schemas.base.response import Response
from core.services.evaluation import evaluation_service
from schemas.evaluation import (
    CourseEvaluationCreate,
    CourseEvaluationUpdate,
    CourseEvaluationStatusUpdate,
    CourseEvaluationScoreUpdate,
    CourseEvaluationCommentUpdate,
    CourseEvaluationResponse,
)
from schemas.evaluation import (
    EvaluationIndicatorInDB,
    EvaluationIndicatorCreate,
    EvaluationIndicatorUpdate,
    EvaluationRuleInDB,
    EvaluationRuleCreate,
    EvaluationRuleUpdate,
    EvaluationRecordInDB,
    EvaluationRecordCreate,
    EvaluationRecordUpdate,
    EvaluationStatistics,
)

router = APIRouter(prefix="/courses/{course_id}/evaluations", tags=["课程评价"])


def CourseEvaluationService(db):
    pass


@router.get("/", response_model=PageResponse[CourseEvaluationResponse], summary="获取评价列表")
async def get_evaluations(
    course_id: int = Path(..., description="课程ID"),
    semester: str = Query(None, description="学期"),
    status: str = Query(None, description="状态"),
    student_id: int = Query(None, description="学生ID"),
    class_id: int = Query(None, description="班级ID"),
    major_id: int = Query(None, description="专业ID"),
    department_id: int = Query(None, description="院系ID"),
    start_time: str = Query(None, description="开始时间"),
    end_time: str = Query(None, description="结束时间"),
    page: int = Query(1, ge=1, description="页码"),
    size: int = Query(20, ge=1, le=100, description="每页数量"),
    sort: str = Query(None, description="排序字段"),
    order: str = Query("desc", description="排序方向"),
    db: Session = Depends(async_db),
    current_user: User = Depends(get_current_active_user),
):
    """获取评价列表"""
    service = CourseEvaluationService(db)
    total, items = service.get_evaluations(
        course_id=course_id,
        semester=semester,
        status=status,
        student_id=student_id,
        class_id=class_id,
        major_id=major_id,
        department_id=department_id,
        start_time=start_time,
        end_time=end_time,
        page=page,
        size=size,
        sort=sort,
        order=order,
    )
    return PageResponse(total=total, items=items, page=page, size=size)


@router.post("/", response_model=Response, summary="创建评价")
async def create_evaluation(
    course_id: int = Path(..., description="课程ID"),
    data: CourseEvaluationCreate = Body(...),
    db: Session = Depends(async_db),
    current_user: User = Depends(get_current_active_user),
):
    """创建评价"""
    service = CourseEvaluationService(db)
    evaluation = service.create_evaluation(course_id, data)
    return Response(data={"id": evaluation.id})


@router.get("/{id}", response_model=Response, summary="获取评价详情")
async def get_evaluation(
    course_id: int = Path(..., description="课程ID"),
    id: int = Path(..., description="评价ID"),
    db: Session = Depends(async_db),
    current_user: User = Depends(get_current_active_user),
):
    """获取评价详情"""
    service = CourseEvaluationService(db)
    evaluation = service.get_evaluation(course_id, id)
    if not evaluation:
        raise QueryResultException("评价不存在")
    return Response(data=evaluation)


@router.put("/{id}", response_model=Response, summary="更新评价")
async def update_evaluation(
    course_id: int = Path(..., description="课程ID"),
    id: int = Path(..., description="评价ID"),
    data: CourseEvaluationUpdate = Body(...),
    db: Session = Depends(async_db),
    current_user: User = Depends(get_current_active_user),
):
    """更新评价"""
    service = CourseEvaluationService(db)
    evaluation = service.update_evaluation(course_id, id, data)
    return Response()


@router.delete("/{id}", response_model=Response, summary="删除评价")
async def delete_evaluation(
    course_id: int = Path(..., description="课程ID"),
    id: int = Path(..., description="评价ID"),
    db: Session = Depends(async_db),
    current_user: User = Depends(get_current_active_user),
):
    """删除评价"""
    service = CourseEvaluationService(db)
    service.delete_evaluation(course_id, id)
    return Response()


@router.put("/{id}/status", response_model=Response, summary="更新评价状态")
async def update_evaluation_status(
    course_id: int = Path(..., description="课程ID"),
    id: int = Path(..., description="评价ID"),
    data: CourseEvaluationStatusUpdate = Body(...),
    db: Session = Depends(async_db),
    current_user: User = Depends(get_current_active_user),
):
    """更新评价状态"""
    service = CourseEvaluationService(db)
    service.update_evaluation_status(course_id, id, data.status)
    return Response()


@router.put("/{id}/score", response_model=Response, summary="更新评价分数")
async def update_evaluation_score(
    course_id: int = Path(..., description="课程ID"),
    id: int = Path(..., description="评价ID"),
    data: CourseEvaluationScoreUpdate = Body(...),
    db: Session = Depends(async_db),
    current_user: User = Depends(get_current_active_user),
):
    """更新评价分数"""
    service = CourseEvaluationService(db)
    service.update_evaluation_score(course_id, id, data.score)
    return Response()


@router.put("/{id}/comment", response_model=Response, summary="更新评价评语")
async def update_evaluation_comment(
    course_id: int = Path(..., description="课程ID"),
    id: int = Path(..., description="评价ID"),
    data: CourseEvaluationCommentUpdate = Body(...),
    db: Session = Depends(async_db),
    current_user: User = Depends(get_current_active_user),
):
    """更新评价评语"""
    service = CourseEvaluationService(db)
    service.update_evaluation_comment(course_id, id, data.comment)
    return Response()


@router.post("/batch", response_model=Response, summary="批量评价")
async def batch_evaluate(
    course_id: int = Path(..., description="课程ID"),
    data: List[CourseEvaluationCreate] = Body(...),
    db: Session = Depends(async_db),
    current_user: User = Depends(get_current_active_user),
):
    """批量评价"""
    service = CourseEvaluationService(db)
    result = service.batch_evaluate(course_id, data)
    return Response(data=result)


@router.post("/import", response_model=Response, summary="导入评价")
async def import_evaluations(
    course_id: int = Path(..., description="课程ID"),
    file: UploadFile = File(...),
    db: Session = Depends(async_db),
    current_user: User = Depends(get_current_active_user),
):
    """导入评价"""
    service = CourseEvaluationService(db)
    result = service.import_evaluations(course_id, file)
    return Response(data=result)


@router.get("/export", response_model=Response, summary="导出评价")
async def export_evaluations(
    course_id: int = Path(..., description="课程ID"),
    semester: str = Query(None, description="学期"),
    status: str = Query(None, description="状态"),
    student_id: int = Query(None, description="学生ID"),
    class_id: int = Query(None, description="班级ID"),
    major_id: int = Query(None, description="专业ID"),
    department_id: int = Query(None, description="院系ID"),
    db: Session = Depends(async_db),
    current_user: User = Depends(get_current_active_user),
):
    """导出评价"""
    service = CourseEvaluationService(db)
    result = service.export_evaluations(
        course_id=course_id,
        semester=semester,
        status=status,
        student_id=student_id,
        class_id=class_id,
        major_id=major_id,
        department_id=department_id,
    )
    return Response(data=result)


@router.get("/stats", response_model=Response, summary="获取评价统计")
async def get_evaluation_stats(
    course_id: int = Path(..., description="课程ID"),
    semester: str = Query(None, description="学期"),
    start_time: str = Query(None, description="开始时间"),
    end_time: str = Query(None, description="结束时间"),
    db: Session = Depends(async_db),
    current_user: User = Depends(get_current_active_user),
):
    """获取评价统计"""
    service = CourseEvaluationService(db)
    stats = service.get_evaluation_stats(
        course_id=course_id, semester=semester, start_time=start_time, end_time=end_time
    )
    return Response(data=stats)


@router.get("/analysis", response_model=Response, summary="获取评价分析")
async def get_evaluation_analysis(
    course_id: int = Path(..., description="课程ID"),
    semester: str = Query(None, description="学期"),
    class_id: int = Query(None, description="班级ID"),
    major_id: int = Query(None, description="专业ID"),
    department_id: int = Query(None, description="院系ID"),
    db: Session = Depends(async_db),
    current_user: User = Depends(get_current_active_user),
):
    """获取评价分析"""
    service = CourseEvaluationService(db)
    analysis = service.get_evaluation_analysis(
        course_id=course_id, semester=semester, class_id=class_id, major_id=major_id, department_id=department_id
    )
    return Response(data=analysis)


@router.post("/indicators", response_model=EvaluationIndicatorInDB)
async def create_evaluation_indicator(
    *,
    db: AsyncSession = Depends(async_db),
    indicator_in: EvaluationIndicatorCreate,
    current_user: User = Depends(get_current_user),
):
    """创建评价指标"""
    # 验证权限
    if not current_user.is_superuser:
        raise HTTPException(status_code=status.HTTP_403_FORBIDDEN, detail="没有权限执行此操作")

    return await evaluation_service.create_indicator(db, indicator_in=indicator_in)


@router.put("/indicators/{indicator_id}", response_model=EvaluationIndicatorInDB)
async def update_evaluation_indicator(
    *,
    db: AsyncSession = Depends(async_db),
    indicator_id: int,
    indicator_in: EvaluationIndicatorUpdate,
    current_user: User = Depends(get_current_user),
):
    """更新评价指标"""
    # 验证权限
    if not current_user.is_superuser:
        raise HTTPException(status_code=status.HTTP_403_FORBIDDEN, detail="没有权限执行此操作")

    return await evaluation_service.update_indicator(db, indicator_id=indicator_id, indicator_in=indicator_in)


@router.get("/indicators/{indicator_id}", response_model=EvaluationIndicatorInDB)
async def get_evaluation_indicator(
    *, db: AsyncSession = Depends(async_db), indicator_id: int, current_user: User = Depends(get_current_user)
):
    """获取评价指标"""
    return await evaluation_service.get_indicator(db, indicator_id=indicator_id)


@router.get("/indicators", response_model=dict)
async def get_evaluation_indicators(
    *,
    db: AsyncSession = Depends(async_db),
    pagination: PaginationParams = Depends(),
    type: Optional[str] = Query(None, description="指标类型"),
    is_active: Optional[bool] = Query(None, description="是否启用"),
    current_user: User = Depends(get_current_user),
):
    """获取评价指标列表"""
    return await evaluation_service.get_indicators(db, pagination=pagination, type=type, is_active=is_active)


@router.post("/rules", response_model=EvaluationRuleInDB)
async def create_evaluation_rule(
    *,
    db: AsyncSession = Depends(async_db),
    rule_in: EvaluationRuleCreate,
    current_user: User = Depends(get_current_user),
):
    """创建评价规则"""
    # 验证权限
    if not current_user.is_superuser:
        raise HTTPException(status_code=status.HTTP_403_FORBIDDEN, detail="没有权限执行此操作")

    return await evaluation_service.create_rule(db, rule_in=rule_in)


@router.put("/rules/{rule_id}", response_model=EvaluationRuleInDB)
async def update_evaluation_rule(
    *,
    db: AsyncSession = Depends(async_db),
    rule_id: int,
    rule_in: EvaluationRuleUpdate,
    current_user: User = Depends(get_current_user),
):
    """更新评价规则"""
    # 验证权限
    if not current_user.is_superuser:
        raise HTTPException(status_code=status.HTTP_403_FORBIDDEN, detail="没有权限执行此操作")

    return await evaluation_service.update_rule(db, rule_id=rule_id, rule_in=rule_in)


@router.get("/rules/{rule_id}", response_model=EvaluationRuleInDB)
async def get_evaluation_rule(
    *, db: AsyncSession = Depends(async_db), rule_id: int, current_user: User = Depends(get_current_user)
):
    """获取评价规则"""
    return await evaluation_service.get_rule(db, rule_id=rule_id)


@router.get("/rules", response_model=dict)
async def get_evaluation_rules(
    *,
    db: AsyncSession = Depends(async_db),
    pagination: PaginationParams = Depends(),
    target_type: Optional[str] = Query(None, description="评价对象类型"),
    course_id: int = Path(..., description="课程ID"),
    teacher_id: Optional[int] = Query(None, description="教师ID"),
    is_active: Optional[bool] = Query(None, description="是否启用"),
    current_user: User = Depends(get_current_user),
):
    """获取评价规则列表"""
    return await evaluation_service.get_evaluation_rules(
        db,
        pagination=pagination,
        target_type=target_type,
        course_id=course_id,
        teacher_id=teacher_id,
        is_active=is_active,
    )


@router.post("/evaluations", response_model=EvaluationRecordInDB)
async def create_evaluation_record(
    *,
    db: AsyncSession = Depends(async_db),
    evaluation_in: EvaluationRecordCreate,
    current_user: User = Depends(get_current_user),
):
    """创建评价记录"""
    # 验证权限
    if not current_user.is_student:
        raise HTTPException(status_code=status.HTTP_403_FORBIDDEN, detail="只有学生可以创建评价")

    # 验证学生身份
    if current_user.id != evaluation_in.student_id:
        raise HTTPException(status_code=status.HTTP_403_FORBIDDEN, detail="只能创建自己的评价")

    return await evaluation_service.create_evaluation(db, evaluation_in=evaluation_in)


@router.put("/evaluations/{evaluation_id}", response_model=EvaluationRecordInDB)
async def update_evaluation_record(
    *,
    db: AsyncSession = Depends(async_db),
    evaluation_id: int,
    evaluation_in: EvaluationRecordUpdate,
    current_user: User = Depends(get_current_user),
):
    """更新评价记录"""
    # 获取评价记录
    evaluation = await evaluation_service.get_evaluation(db, evaluation_id=evaluation_id)

    # 验证权限
    if not current_user.is_student or current_user.id != evaluation.student_id:
        raise HTTPException(status_code=status.HTTP_403_FORBIDDEN, detail="只能更新自己的评价")

    return await evaluation_service.update_evaluation(db, evaluation_id=evaluation_id, evaluation_in=evaluation_in)


@router.get("/evaluations/{evaluation_id}", response_model=EvaluationRecordInDB)
async def get_evaluation_record(
    *, db: AsyncSession = Depends(async_db), evaluation_id: int, current_user: User = Depends(get_current_user)
):
    """获取评价记录"""
    evaluation = await evaluation_service.get_evaluation(db, evaluation_id=evaluation_id)

    # 验证权限
    if not current_user.is_superuser and not current_user.is_teacher and current_user.id != evaluation.student_id:
        raise HTTPException(status_code=status.HTTP_403_FORBIDDEN, detail="没有权限查看此评价")

    return evaluation


@router.get("/evaluations", response_model=dict)
async def get_evaluation_records(
    *,
    db: AsyncSession = Depends(async_db),
    pagination: PaginationParams = Depends(),
    student_id: Optional[int] = Query(None, description="学生ID"),
    course_id: int = Path(..., description="课程ID"),
    teacher_id: Optional[int] = Query(None, description="教师ID"),
    indicator_id: Optional[int] = Query(None, description="评价指标ID"),
    rule_id: Optional[int] = Query(None, description="评价规则ID"),
    status: Optional[str] = Query(None, description="状态"),
    is_anonymous: Optional[bool] = Query(None, description="是否匿名"),
    current_user: User = Depends(get_current_user),
):
    """获取评价记录列表"""
    # 验证权限
    if not current_user.is_superuser and not current_user.is_teacher:
        # 学生只能查看自己的评价
        student_id = current_user.id

    return await evaluation_service.get_evaluations(
        db,
        pagination=pagination,
        student_id=student_id,
        course_id=course_id,
        teacher_id=teacher_id,
        indicator_id=indicator_id,
        rule_id=rule_id,
        status=status,
        is_anonymous=is_anonymous,
    )


@router.get("/statistics", response_model=EvaluationStatistics)
async def get_evaluation_statistics(
    *,
    db: AsyncSession = Depends(async_db),
    course_id: int = Path(..., description="课程ID"),
    teacher_id: Optional[int] = Query(None, description="教师ID"),
    current_user: User = Depends(get_current_user),
):
    """获取评价统计信息"""
    # 验证权限
    if not current_user.is_superuser and not current_user.is_teacher:
        raise HTTPException(status_code=status.HTTP_403_FORBIDDEN, detail="没有权限查看统计信息")

    return await evaluation_service.get_evaluation_statistics(db, course_id=course_id, teacher_id=teacher_id)
