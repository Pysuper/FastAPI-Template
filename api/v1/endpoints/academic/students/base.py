from datetime import datetime
from typing import List, Optional

from fastapi import APIRouter, Depends, HTTPException, Query
from sqlalchemy import or_, extract, func
from sqlalchemy.orm import Session

from core.dependencies.auth import get_current_user
from core.dependencies import async_db
from interceptor.response import ResponseSchema, success
from models.department import Department
from models.department import Major, Classes
from models.student import Student
from schemas.student import StudentResponse, StudentCreate, StudentUpdate

# 路由
router = APIRouter()


@router.post("/", response_model=ResponseSchema[StudentResponse])
async def create_student(
    student: StudentCreate, db: Session = Depends(async_db), current_user: int = Depends(get_current_user)
):
    """创建学生"""
    # 检查学号是否已存在
    if db.query(Student).filter(Student.student_id == student.student_id, Student.is_delete == False).first():
        raise HTTPException(status_code=400, detail="Student ID already exists")

    # 检查身份证号是否已存在
    if db.query(Student).filter(Student.id_card == student.id_card, Student.is_delete == False).first():
        raise HTTPException(status_code=400, detail="ID card already exists")

    # 检查院系是否存在
    if not db.query(Department).filter(Department.id == student.department_id).first():
        raise HTTPException(status_code=404, detail="Department not found")

    # 检查专业是否存在
    if not db.query(Major).filter(Major.id == student.major_id).first():
        raise HTTPException(status_code=404, detail="Major not found")

    # 检查班级是否存在
    if not db.query(Classes).filter(Classes.id == student.class_id).first():
        raise HTTPException(status_code=404, detail="Classes not found")

    db_student = Student(**student.dict(), create_by=current_user)
    db.add(db_student)
    db.commit()
    db.refresh(db_student)
    return success(data=db_student)


@router.get("/{student_id}", response_model=ResponseSchema[StudentResponse])
async def get_student(student_id: int, db: Session = Depends(async_db), current_user: int = Depends(get_current_user)):
    """获取学生详情"""
    student = db.query(Student).filter(Student.id == student_id, Student.is_delete == False).first()
    if not student:
        raise HTTPException(status_code=404, detail="Student not found")
    return success(data=student)


@router.put("/{student_id}", response_model=ResponseSchema[StudentResponse])
async def update_student(
    student_id: int,
    student_update: StudentUpdate,
    db: Session = Depends(async_db),
    current_user: int = Depends(get_current_user),
):
    """更新学生信息"""
    student = db.query(Student).filter(Student.id == student_id, Student.is_delete == False).first()
    if not student:
        raise HTTPException(status_code=404, detail="Student not found")

    # 如果更新院系，检查是否存在
    if student_update.department_id:
        if not db.query(Department).filter(Department.id == student_update.department_id).first():
            raise HTTPException(status_code=404, detail="Department not found")

    # 如果更新专业，检查是否存在
    if student_update.major_id:
        if not db.query(Major).filter(Major.id == student_update.major_id).first():
            raise HTTPException(status_code=404, detail="Major not found")

    # 如果更新班级，检查是否存在
    if student_update.class_id:
        if not db.query(Classes).filter(Classes.id == student_update.class_id).first():
            raise HTTPException(status_code=404, detail="Class not found")

    for field, value in student_update.dict(exclude_unset=True).items():
        setattr(student, field, value)

    student.update_by = current_user
    student.update_time = datetime.now()

    db.add(student)
    db.commit()
    db.refresh(student)
    return success(data=student)


@router.delete("/{student_id}", response_model=ResponseSchema)
async def delete_student(
    student_id: int, db: Session = Depends(async_db), current_user: int = Depends(get_current_user)
):
    """删除学生"""
    student = db.query(Student).filter(Student.id == student_id, Student.is_delete == False).first()
    if not student:
        raise HTTPException(status_code=404, detail="Student not found")

    student.is_delete = True
    student.delete_by = current_user
    student.delete_time = datetime.now()

    db.add(student)
    db.commit()
    return success(message="Student deleted successfully")


@router.get("/", response_model=ResponseSchema[List[StudentResponse]])
async def list_students(
    skip: int = Query(0, ge=0),
    limit: int = Query(10, ge=1, le=100),
    keyword: Optional[str] = None,
    department_id: Optional[int] = None,
    major_id: Optional[int] = None,
    class_id: Optional[int] = None,
    status: Optional[str] = None,
    is_registered: Optional[bool] = None,
    db: Session = Depends(async_db),
    current_user: int = Depends(get_current_user),
):
    """获取学生列表"""
    query = db.query(Student).filter(Student.is_delete == False)

    if keyword:
        query = query.filter(
            or_(
                Student.student_id.ilike(f"%{keyword}%"),
                Student.name.ilike(f"%{keyword}%"),
                Student.id_card.ilike(f"%{keyword}%"),
                Student.phone.ilike(f"%{keyword}%"),
            )
        )
    if department_id:
        query = query.filter(Student.department_id == department_id)
    if major_id:
        query = query.filter(Student.major_id == major_id)
    if class_id:
        query = query.filter(Student.class_id == class_id)
    if status:
        query = query.filter(Student.status == status)
    if is_registered is not None:
        query = query.filter(Student.is_registered == is_registered)

    total = query.count()
    students = query.offset(skip).limit(limit).all()

    return success(data=students, meta={"total": total, "skip": skip, "limit": limit})


@router.put("/{student_id}/status", response_model=ResponseSchema[StudentResponse])
async def update_student_status(
    student_id: int, status: str, db: Session = Depends(async_db), current_user: int = Depends(get_current_user)
):
    """更新学生状态"""
    student = db.query(Student).filter(Student.id == student_id, Student.is_delete == False).first()
    if not student:
        raise HTTPException(status_code=404, detail="Student not found")

    valid_statuses = ["active", "graduated", "suspended", "dropped"]
    if status not in valid_statuses:
        raise HTTPException(status_code=400, detail=f"Invalid status. Must be one of: {', '.join(valid_statuses)}")

    student.status = status
    student.update_by = current_user
    student.update_time = datetime.now()

    # 如果是毕业状态，设置毕业日期
    if status == "graduated" and not student.graduation_date:
        student.graduation_date = datetime.now()

    db.add(student)
    db.commit()
    db.refresh(student)
    return success(data=student)


@router.put("/{student_id}/register", response_model=ResponseSchema[StudentResponse])
async def register_student(
    student_id: int, db: Session = Depends(async_db), current_user: int = Depends(get_current_user)
):
    """注册学生"""
    student = db.query(Student).filter(Student.id == student_id, Student.is_delete == False).first()
    if not student:
        raise HTTPException(status_code=404, detail="Student not found")

    if student.status != "active":
        raise HTTPException(status_code=400, detail="Only active students can be registered")

    student.is_registered = True
    student.update_by = current_user
    student.update_time = datetime.now()

    db.add(student)
    db.commit()
    db.refresh(student)
    return success(data=student)


@router.put("/{student_id}/unregister", response_model=ResponseSchema[StudentResponse])
async def unregister_student(
    student_id: int, db: Session = Depends(async_db), current_user: int = Depends(get_current_user)
):
    """取消注册学生"""
    student = db.query(Student).filter(Student.id == student_id, Student.is_delete == False).first()
    if not student:
        raise HTTPException(status_code=404, detail="Student not found")

    student.is_registered = False
    student.update_by = current_user
    student.update_time = datetime.now()

    db.add(student)
    db.commit()
    db.refresh(student)
    return success(data=student)


@router.get("/stats", response_model=ResponseSchema)
async def get_student_stats(
    department_id: Optional[int] = None,
    major_id: Optional[int] = None,
    db: Session = Depends(async_db),
    current_user: int = Depends(get_current_user),
):
    """获取学生统计信息"""
    query = db.query(Student).filter(Student.is_delete == False)

    if department_id:
        query = query.filter(Student.department_id == department_id)
    if major_id:
        query = query.filter(Student.major_id == major_id)

    total_students = query.count()
    active_students = query.filter(Student.status == "active").count()
    graduated_students = query.filter(Student.status == "graduated").count()
    suspended_students = query.filter(Student.status == "suspended").count()
    dropped_students = query.filter(Student.status == "dropped").count()
    registered_students = query.filter(Student.is_registered == True).count()

    # 性别分布
    gender_distribution = {
        gender: count
        for gender, count in db.query(Student.gender, func.count(Student.id))
        .filter(Student.is_delete == False)
        .group_by(Student.gender)
        .all()
    }

    # 年级分布
    grade_distribution = {
        year: count
        for year, count in db.query(extract("year", Student.enrollment_date), func.count(Student.id))
        .filter(Student.is_delete == False)
        .group_by(extract("year", Student.enrollment_date))
        .all()
    }

    stats = {
        "total_students": total_students,
        "active_students": active_students,
        "graduated_students": graduated_students,
        "suspended_students": suspended_students,
        "dropped_students": dropped_students,
        "registered_students": registered_students,
        "gender_distribution": gender_distribution,
        "grade_distribution": grade_distribution,
    }

    return success(data=stats)
