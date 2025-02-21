from typing import List, Optional

from black import Cache
from fastapi import APIRouter, Depends, HTTPException, Query
from sqlalchemy.orm import Session

from core.constants.enums import Action
from core.dependencies import async_db
from core.rbac.permissions import PermissionChecker
from middleware import logger
from models.library import ResourceType
from schemas.validator import ExamCreate, ExamUpdate, ResponseModel
from services.academic.exams.exam_management import ExamService

router = APIRouter(prefix="/exams", tags=["exams"])
permission = PermissionChecker(get_db(), Cache())


@router.get("", response_model=ResponseModel)
@permission.has_permission(ResourceType.EXAM, Action.READ)
async def get_exams(
    skip: int = Query(0, ge=0),
    limit: int = Query(100, ge=1, le=100),
    course_id: Optional[int] = None,
    db: Session = Depends(async_db),
):
    """获取考试列表"""
    try:
        service = ExamService(db, Cache())
        if course_id:
            exams = await service.get_course_exams(course_id)
        else:
            exams = await service.get_exams(skip, limit)
        return ResponseModel(data={"exams": [exam.__dict__ for exam in exams]})
    except Exception as e:
        logger.error(f"Failed to get exams: {str(e)}")
        raise HTTPException(status_code=500, detail="获取考试列表失败")


@router.get("/{exam_id}", response_model=ResponseModel)
@permission.has_permission(ResourceType.EXAM, Action.READ)
async def get_exam(exam_id: int, db: Session = Depends(async_db)):
    """获取考试详情"""
    try:
        service = ExamService(db, Cache())
        exam = await service.get_exam_by_id(exam_id)
        if not exam:
            raise HTTPException(status_code=404, detail="考试不存在")
        return ResponseModel(data={"exam": exam.__dict__})
    except HTTPException as e:
        raise e
    except Exception as e:
        logger.error(f"Failed to get exam: {str(e)}")
        raise HTTPException(status_code=500, detail="获取考试信息失败")


@router.post("", response_model=ResponseModel)
@permission.has_permission(ResourceType.EXAM, Action.CREATE)
async def create_exam(exam: ExamCreate, db: Session = Depends(async_db)):
    """创建考试"""
    try:
        service = ExamService(db, Cache())
        new_exam = await service.create_exam(exam)
        return ResponseModel(message="创建考试成功", data={"exam": new_exam.__dict__})
    except HTTPException as e:
        raise e
    except Exception as e:
        logger.error(f"Failed to create exam: {str(e)}")
        raise HTTPException(status_code=500, detail="创建考试失败")


@router.put("/{exam_id}", response_model=ResponseModel)
@permission.has_permission(ResourceType.EXAM, Action.UPDATE)
async def update_exam(exam_id: int, exam: ExamUpdate, db: Session = Depends(async_db)):
    """更新考试信息"""
    try:
        service = ExamService(db, Cache())
        updated_exam = await service.update_exam(exam_id, exam)
        return ResponseModel(message="更新考试成功", data={"exam": updated_exam.__dict__})
    except HTTPException as e:
        raise e
    except Exception as e:
        logger.error(f"Failed to update exam: {str(e)}")
        raise HTTPException(status_code=500, detail="更新考试失败")


@router.delete("/{exam_id}", response_model=ResponseModel)
@permission.has_permission(ResourceType.EXAM, Action.DELETE)
async def delete_exam(exam_id: int, db: Session = Depends(async_db)):
    """删除考试"""
    try:
        service = ExamService(db, Cache())
        await service.delete_exam(exam_id)
        return ResponseModel(message="删除考试成功")
    except HTTPException as e:
        raise e
    except Exception as e:
        logger.error(f"Failed to delete exam: {str(e)}")
        raise HTTPException(status_code=500, detail="删除考试失败")


@router.get("/{exam_id}/questions", response_model=ResponseModel)
@permission.has_permission(ResourceType.EXAM, Action.READ)
async def get_exam_questions(exam_id: int, db: Session = Depends(async_db)):
    """获取考试题目"""
    try:
        service = ExamService(db, Cache())
        questions = await service.get_exam_questions(exam_id)
        return ResponseModel(data={"questions": [q.__dict__ for q in questions]})
    except HTTPException as e:
        raise e
    except Exception as e:
        logger.error(f"Failed to get exam questions: {str(e)}")
        raise HTTPException(status_code=500, detail="获取考试题目失败")


@router.post("/{exam_id}/questions", response_model=ResponseModel)
@permission.has_permission(ResourceType.EXAM, Action.UPDATE)
async def add_exam_question(exam_id: int, question: dict, db: Session = Depends(async_db)):
    """添加考试题目"""
    try:
        service = ExamService(db, Cache())
        new_question = await service.add_exam_question(exam_id, question)
        return ResponseModel(message="添加题目成功", data={"question": new_question.__dict__})
    except HTTPException as e:
        raise e
    except Exception as e:
        logger.error(f"Failed to add exam question: {str(e)}")
        raise HTTPException(status_code=500, detail="添加考试题目失败")


@router.get("/{exam_id}/records", response_model=ResponseModel)
@permission.has_permission(ResourceType.EXAM, Action.READ)
async def get_exam_records(
    exam_id: int,
    skip: int = Query(0, ge=0),
    limit: int = Query(100, ge=1, le=100),
    db: Session = Depends(async_db),
):
    """获取考试记录"""
    try:
        service = ExamService(db, Cache())
        records = await service.get_exam_records(exam_id, skip, limit)
        return ResponseModel(data={"records": [r.__dict__ for r in records]})
    except HTTPException as e:
        raise e
    except Exception as e:
        logger.error(f"Failed to get exam records: {str(e)}")
        raise HTTPException(status_code=500, detail="获取考试记录失败")


@router.post("/{exam_id}/start", response_model=ResponseModel)
@permission.has_permission(ResourceType.EXAM, Action.UPDATE)
async def start_exam(exam_id: int, student_id: int, db: Session = Depends(async_db)):
    """开始考试"""
    try:
        service = ExamService(db, Cache())
        exam_record = await service.start_exam(exam_id, student_id)
        return ResponseModel(message="开始考试成功", data={"exam_record": exam_record.__dict__})
    except HTTPException as e:
        raise e
    except Exception as e:
        logger.error(f"Failed to start exam: {str(e)}")
        raise HTTPException(status_code=500, detail="开始考试失败")


@router.post("/{exam_id}/submit", response_model=ResponseModel)
@permission.has_permission(ResourceType.EXAM, Action.UPDATE)
async def submit_exam(exam_id: int, student_id: int, answers: List[dict], db: Session = Depends(async_db)):
    """提交考试"""
    try:
        service = ExamService(db, Cache())
        result = await service.submit_exam(exam_id, student_id, answers)
        return ResponseModel(message="提交考试成功", data={"result": result})
    except HTTPException as e:
        raise e
    except Exception as e:
        logger.error(f"Failed to submit exam: {str(e)}")
        raise HTTPException(status_code=500, detail="提交考试失败")
