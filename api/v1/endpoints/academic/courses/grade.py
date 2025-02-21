from typing import List

from fastapi import APIRouter, Depends, Query, Path, Body, UploadFile, File
from sqlalchemy.orm import Session

from core.db.metrics.pagination import PageResponse
from core.dependencies.auth import get_current_active_user
from core.dependencies import async_db
from exceptions.database.query import QueryResultException
from schemas.base.response import Response
from models.user import User

# from custom.schemas.validators.rbac import User
from schemas.course import (
    CourseGradeStatusUpdate,
    CourseGradeCreate,
    CourseGradeUpdate,
    CourseGradeScoreUpdate,
    CourseGradeLevelUpdate,
    CourseGradeResponse,
)

router = APIRouter(prefix="/courses/{course_id}/grades", tags=["课程成绩"])


@router.get("/", response_model=PageResponse[CourseGradeResponse], summary="获取成绩列表")
async def get_grades(
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
    """获取成绩列表"""
    service = CourseGradeService(db)
    total, items = service.get_grades(
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


@router.post("/", response_model=Response, summary="创建成绩")
async def create_grade(
    course_id: int = Path(..., description="课程ID"),
    data: CourseGradeCreate = Body(...),
    db: Session = Depends(async_db),
    current_user: User = Depends(get_current_active_user),
):
    """创建成绩"""
    service = CourseGradeService(db)
    grade = service.create_grade(course_id, data)
    return Response(data={"id": grade.id})


@router.get("/{id}", response_model=Response, summary="获取成绩详情")
async def get_grade(
    course_id: int = Path(..., description="课程ID"),
    id: int = Path(..., description="成绩ID"),
    db: Session = Depends(async_db),
    current_user: User = Depends(get_current_active_user),
):
    """获取成绩详情"""
    service = CourseGradeService(db)
    grade = service.get_grade(course_id, id)
    if not grade:
        raise QueryResultException("成绩不存在")
    return Response(data=grade)


@router.put("/{id}", response_model=Response, summary="更新成绩")
async def update_grade(
    course_id: int = Path(..., description="课程ID"),
    id: int = Path(..., description="成绩ID"),
    data: CourseGradeUpdate = Body(...),
    db: Session = Depends(async_db),
    current_user: User = Depends(get_current_active_user),
):
    """更新成绩"""
    service = CourseGradeService(db)
    grade = service.update_grade(course_id, id, data)
    return Response()


def CourseGradeService(db):
    pass


@router.delete("/{id}", response_model=Response, summary="删除成绩")
async def delete_grade(
    course_id: int = Path(..., description="课程ID"),
    id: int = Path(..., description="成绩ID"),
    db: Session = Depends(async_db),
    current_user: User = Depends(get_current_active_user),
):
    """删除成绩"""
    service = CourseGradeService(db)
    service.delete_grade(course_id, id)
    return Response()


@router.put("/{id}/status", response_model=Response, summary="更新成绩状态")
async def update_grade_status(
    course_id: int = Path(..., description="课程ID"),
    id: int = Path(..., description="成绩ID"),
    data: CourseGradeStatusUpdate = Body(...),
    db: Session = Depends(async_db),
    current_user: User = Depends(get_current_active_user),
):
    """更新成绩状态"""
    service = CourseGradeService(db)
    service.update_grade_status(course_id, id, data.status)
    return Response()


@router.put("/{id}/score", response_model=Response, summary="更新成绩分数")
async def update_grade_score(
    course_id: int = Path(..., description="课程ID"),
    id: int = Path(..., description="成绩ID"),
    data: CourseGradeScoreUpdate = Body(...),
    db: Session = Depends(async_db),
    current_user: User = Depends(get_current_active_user),
):
    """更新成绩分数"""
    service = CourseGradeService(db)
    service.update_grade_score(course_id, id, data.score)
    return Response()


@router.put("/{id}/level", response_model=Response, summary="更新成绩等级")
async def update_grade_level(
    course_id: int = Path(..., description="课程ID"),
    id: int = Path(..., description="成绩ID"),
    data: CourseGradeLevelUpdate = Body(...),
    db: Session = Depends(async_db),
    current_user: User = Depends(get_current_active_user),
):
    """更新成绩等级"""
    service = CourseGradeService(db)
    service.update_grade_level(course_id, id, data.level)
    return Response()


@router.post("/batch", response_model=Response, summary="批量录入成绩")
async def batch_grade(
    course_id: int = Path(..., description="课程ID"),
    data: List[CourseGradeCreate] = Body(...),
    db: Session = Depends(async_db),
    current_user: User = Depends(get_current_active_user),
):
    """批量录入成绩"""
    service = CourseGradeService(db)
    result = service.batch_grade(course_id, data)
    return Response(data=result)


@router.post("/import", response_model=Response, summary="导入成绩")
async def import_grades(
    course_id: int = Path(..., description="课程ID"),
    file: UploadFile = File(...),
    db: Session = Depends(async_db),
    current_user: User = Depends(get_current_active_user),
):
    """导入成绩"""
    service = CourseGradeService(db)
    result = service.import_grades(course_id, file)
    return Response(data=result)


@router.get("/export", response_model=Response, summary="导出成绩")
async def export_grades(
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
    """导出成绩"""
    service = CourseGradeService(db)
    result = service.export_grades(
        course_id=course_id,
        semester=semester,
        status=status,
        student_id=student_id,
        class_id=class_id,
        major_id=major_id,
        department_id=department_id,
    )
    return Response(data=result)


@router.get("/stats", response_model=Response, summary="获取成绩统计")
async def get_grade_stats(
    course_id: int = Path(..., description="课程ID"),
    semester: str = Query(None, description="学期"),
    start_time: str = Query(None, description="开始时间"),
    end_time: str = Query(None, description="结束时间"),
    db: Session = Depends(async_db),
    current_user: User = Depends(get_current_active_user),
):
    """获取成绩统计"""
    service = CourseGradeService(db)
    stats = service.get_grade_stats(course_id=course_id, semester=semester, start_time=start_time, end_time=end_time)
    return Response(data=stats)


@router.get("/analysis", response_model=Response, summary="获取成绩分析")
async def get_grade_analysis(
    course_id: int = Path(..., description="课程ID"),
    semester: str = Query(None, description="学期"),
    class_id: int = Query(None, description="班级ID"),
    major_id: int = Query(None, description="专业ID"),
    department_id: int = Query(None, description="院系ID"),
    db: Session = Depends(async_db),
    current_user: User = Depends(get_current_active_user),
):
    """获取成绩分析"""
    service = CourseGradeService(db)
    analysis = service.get_grade_analysis(
        course_id=course_id, semester=semester, class_id=class_id, major_id=major_id, department_id=department_id
    )
    return Response(data=analysis)
