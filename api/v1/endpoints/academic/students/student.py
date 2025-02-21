from typing import List, Optional

from black import Cache
from fastapi import APIRouter, Depends
from sqlalchemy.orm import Query, Session

from core.constants.enums import ResourceType, Action
from core.dependencies import async_db
from core.exceptions.http.base import HTTPException
from core.rbac.permissions import PermissionChecker
from middleware import logger
from schemas.validator import ResponseModel, StudentCreate, StudentUpdate
from services.academic.student.student_management import StudentService

router = APIRouter(prefix="/students", tags=["students"])
permission = PermissionChecker(get_db(), Cache())


@router.get("", response_model=List[ResponseModel])
@permission.has_permission(ResourceType.STUDENT, Action.READ)
async def get_students(
    skip: int = Query(0, ge=0),
    limit: int = Query(100, ge=1, le=100),
    class_id: Optional[int] = None,
    db: Session = Depends(async_db),
):
    """获取学生列表"""
    try:
        service = StudentService(db, Cache())
        if class_id:
            students = await service.get_class_students(class_id)
        else:
            students = await service.get_students(skip, limit)
        return ResponseModel(data={"students": [student.__dict__ for student in students]})
    except Exception as e:
        logger.error(f"Failed to get students: {str(e)}")
        raise HTTPException(status_code=500, detail="获取学生列表失败")


@router.get("/{student_id}", response_model=ResponseModel)
@permission.has_permission(ResourceType.STUDENT, Action.READ)
async def get_student(student_id: int, db: Session = Depends(async_db)):
    """获取学生详情"""
    try:
        service = StudentService(db, Cache())
        student = await service.get_student_by_id(student_id)
        if not student:
            raise HTTPException(status_code=404, detail="学生不存在")
        return ResponseModel(data={"student": student.__dict__})
    except HTTPException as e:
        raise e
    except Exception as e:
        logger.error(f"Failed to get student: {str(e)}")
        raise HTTPException(status_code=500, detail="获取学生信息失败")


@router.post("", response_model=ResponseModel)
@permission.has_permission(ResourceType.STUDENT, Action.CREATE)
async def create_student(student: StudentCreate, db: Session = Depends(async_db)):
    """创建学生"""
    try:
        service = StudentService(db, Cache())
        new_student = await service.create_student(student)
        return ResponseModel(message="创建学生成功", data={"student": new_student.__dict__})
    except HTTPException as e:
        raise e
    except Exception as e:
        logger.error(f"Failed to create student: {str(e)}")
        raise HTTPException(status_code=500, detail="创建学生失败")


@router.put("/{student_id}", response_model=ResponseModel)
@permission.has_permission(ResourceType.STUDENT, Action.UPDATE)
async def update_student(student_id: int, student: StudentUpdate, db: Session = Depends(async_db)):
    """更新学生信息"""
    try:
        service = StudentService(db, Cache())
        updated_student = await service.update_student(student_id, student)
        return ResponseModel(message="更新学生成功", data={"student": updated_student.__dict__})
    except HTTPException as e:
        raise e
    except Exception as e:
        logger.error(f"Failed to update student: {str(e)}")
        raise HTTPException(status_code=500, detail="更新学生失败")


@router.delete("/{student_id}", response_model=ResponseModel)
@permission.has_permission(ResourceType.STUDENT, Action.DELETE)
async def delete_student(student_id: int, db: Session = Depends(async_db)):
    """删除学生"""
    try:
        service = StudentService(db, Cache())
        await service.delete_student(student_id)
        return ResponseModel(message="删除学生成功")
    except HTTPException as e:
        raise e
    except Exception as e:
        logger.error(f"Failed to delete student: {str(e)}")
        raise HTTPException(status_code=500, detail="删除学生失败")


@router.get("/{student_id}/behaviors", response_model=ResponseModel)
@permission.has_permission(ResourceType.STUDENT, Action.READ)
async def get_student_behaviors(
    student_id: int, skip: int = Query(0, ge=0), limit: int = Query(100, ge=1, le=100), db: Session = Depends(async_db)
):
    """获取学生行为记录"""
    try:
        service = StudentService(db, Cache())
        behaviors = await service.get_student_behaviors(student_id, skip, limit)
        return ResponseModel(data={"behaviors": [behavior.__dict__ for behavior in behaviors]})
    except HTTPException as e:
        raise e
    except Exception as e:
        logger.error(f"Failed to get student behaviors: {str(e)}")
        raise HTTPException(status_code=500, detail="获取学生行为记录失败")


@router.post("/{student_id}/behaviors", response_model=ResponseModel)
@permission.has_permission(ResourceType.STUDENT, Action.UPDATE)
async def add_behavior_record(
    student_id: int, type: str, description: str, score: int, recorder_id: int, db: Session = Depends(async_db)
):
    """添加行为记录"""
    try:
        service = StudentService(db, Cache())
        behavior = await service.add_behavior_record(student_id, type, description, score, recorder_id)
        return ResponseModel(message="添加行为记录成功", data={"behavior": behavior.__dict__})
    except HTTPException as e:
        raise e
    except Exception as e:
        logger.error(f"Failed to add behavior record: {str(e)}")
        raise HTTPException(status_code=500, detail="添加行为记录失败")
