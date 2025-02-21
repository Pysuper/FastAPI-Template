from typing import List

from fastapi import APIRouter, Depends, HTTPException, Query, status
from sqlalchemy.ext.asyncio import AsyncSession

from core.deps import get_current_user, get_db
from models.rbac import User
from repositories.school import (
    class_repository,
    course_repository,
    department_repository,
    major_repository,
    student_repository,
    teacher_repository,
)
from schemas.common import PaginationParams
from schemas.school import (
    ClassCreate,
    ClassInDB,
    ClassUpdate,
    CourseCreate,
    CourseInDB,
    CourseUpdate,
    DepartmentCreate,
    DepartmentInDB,
    DepartmentUpdate,
    MajorCreate,
    MajorInDB,
    MajorUpdate,
    StudentCreate,
    StudentInDB,
    StudentUpdate,
    TeacherCreate,
    TeacherInDB,
    TeacherUpdate,
)

router = APIRouter()


# Department routes
@router.post("/departments", response_model=DepartmentInDB, status_code=status.HTTP_201_CREATED)
async def create_department(
    *,
    db: AsyncSession = Depends(async_db),
    department_in: DepartmentCreate,
    current_user: User = Depends(get_current_user),
) -> DepartmentInDB:
    """创建院系"""
    if not current_user.is_superuser:
        raise HTTPException(status_code=status.HTTP_403_FORBIDDEN, detail="没有权限执行此操作")

    department = await department_repository.get_by_code(db, code=department_in.code)
    if department:
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail="院系代码已存在")

    return await department_repository.create(db, obj_in=department_in)


@router.get("/departments", response_model=List[DepartmentInDB])
async def get_departments(
    *,
    db: AsyncSession = Depends(async_db),
    pagination: PaginationParams = Depends(),
    current_user: User = Depends(get_current_user),
) -> List[DepartmentInDB]:
    """获取院系列表"""
    departments = await department_repository.get_multi(db, pagination=pagination)
    return departments


@router.get("/departments/{department_id}", response_model=DepartmentInDB)
async def get_department(
    *, db: AsyncSession = Depends(async_db), department_id: int, current_user: User = Depends(get_current_user)
) -> DepartmentInDB:
    """获取院系详情"""
    department = await department_repository.get(db, id=department_id)
    if not department:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="院系不存在")
    return department


@router.put("/departments/{department_id}", response_model=DepartmentInDB)
async def update_department(
    *,
    db: AsyncSession = Depends(async_db),
    department_id: int,
    department_in: DepartmentUpdate,
    current_user: User = Depends(get_current_user),
) -> DepartmentInDB:
    """更新院系"""
    if not current_user.is_superuser:
        raise HTTPException(status_code=status.HTTP_403_FORBIDDEN, detail="没有权限执行此操作")

    department = await department_repository.get(db, id=department_id)
    if not department:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="院系不存在")

    return await department_repository.update(db, db_obj=department, obj_in=department_in)


@router.delete("/departments/{department_id}", status_code=status.HTTP_204_NO_CONTENT)
async def delete_department(
    *, db: AsyncSession = Depends(async_db), department_id: int, current_user: User = Depends(get_current_user)
):
    """删除院系"""
    if not current_user.is_superuser:
        raise HTTPException(status_code=status.HTTP_403_FORBIDDEN, detail="没有权限执行此操作")

    department = await department_repository.get(db, id=department_id)
    if not department:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="院系不存在")

    await department_repository.remove(db, id=department_id)


# Major routes
@router.post("/majors", response_model=MajorInDB, status_code=status.HTTP_201_CREATED)
async def create_major(
    *, db: AsyncSession = Depends(async_db), major_in: MajorCreate, current_user: User = Depends(get_current_user)
) -> MajorInDB:
    """创建专业"""
    if not current_user.is_superuser:
        raise HTTPException(status_code=status.HTTP_403_FORBIDDEN, detail="没有权限执行此操作")

    major = await major_repository.get_by_code(db, code=major_in.code)
    if major:
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail="专业代码已存在")

    return await major_repository.create(db, obj_in=major_in)


@router.get("/majors", response_model=List[MajorInDB])
async def get_majors(
    *,
    db: AsyncSession = Depends(async_db),
    pagination: PaginationParams = Depends(),
    department_id: int = Query(None, description="院系ID"),
    current_user: User = Depends(get_current_user),
) -> List[MajorInDB]:
    """获取专业列表"""
    if department_id:
        return await major_repository.get_by_department(db, department_id=department_id)
    return await major_repository.get_multi(db, pagination=pagination)


# Class routes
@router.post("/classes", response_model=ClassInDB, status_code=status.HTTP_201_CREATED)
async def create_class(
    *, db: AsyncSession = Depends(async_db), class_in: ClassCreate, current_user: User = Depends(get_current_user)
) -> ClassInDB:
    """创建班级"""
    if not current_user.is_superuser:
        raise HTTPException(status_code=status.HTTP_403_FORBIDDEN, detail="没有权限执行此操作")

    class_ = await class_repository.get_by_code(db, code=class_in.code)
    if class_:
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail="班级代码已存在")

    return await class_repository.create(db, obj_in=class_in)


@router.get("/classes", response_model=List[ClassInDB])
async def get_classes(
    *,
    db: AsyncSession = Depends(async_db),
    pagination: PaginationParams = Depends(),
    major_id: int = Query(None, description="专业ID"),
    current_user: User = Depends(get_current_user),
) -> List[ClassInDB]:
    """获取班级列表"""
    if major_id:
        return await class_repository.get_by_major(db, major_id=major_id)
    return await class_repository.get_multi(db, pagination=pagination)


# Teacher routes
@router.post("/teachers", response_model=TeacherInDB, status_code=status.HTTP_201_CREATED)
async def create_teacher(
    *, db: AsyncSession = Depends(async_db), teacher_in: TeacherCreate, current_user: User = Depends(get_current_user)
) -> TeacherInDB:
    """创建教师"""
    if not current_user.is_superuser:
        raise HTTPException(status_code=status.HTTP_403_FORBIDDEN, detail="没有权限执行此操作")

    teacher = await teacher_repository.get_by_code(db, code=teacher_in.code)
    if teacher:
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail="教师工号已存在")

    return await teacher_repository.create(db, obj_in=teacher_in)


@router.get("/teachers", response_model=List[TeacherInDB])
async def get_teachers(
    *,
    db: AsyncSession = Depends(async_db),
    pagination: PaginationParams = Depends(),
    department_id: int = Query(None, description="院系ID"),
    current_user: User = Depends(get_current_user),
) -> List[TeacherInDB]:
    """获取教师列表"""
    if department_id:
        return await teacher_repository.get_by_department(db, department_id=department_id)
    return await teacher_repository.get_multi(db, pagination=pagination)


# Student routes
@router.post("/students", response_model=StudentInDB, status_code=status.HTTP_201_CREATED)
async def create_student(
    *, db: AsyncSession = Depends(async_db), student_in: StudentCreate, current_user: User = Depends(get_current_user)
) -> StudentInDB:
    """创建学生"""
    if not current_user.is_superuser:
        raise HTTPException(status_code=status.HTTP_403_FORBIDDEN, detail="没有权限执行此操作")

    student = await student_repository.get_by_code(db, code=student_in.code)
    if student:
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail="学号已存在")

    return await student_repository.create(db, obj_in=student_in)


@router.get("/students", response_model=List[StudentInDB])
async def get_students(
    *,
    db: AsyncSession = Depends(async_db),
    pagination: PaginationParams = Depends(),
    class_id: int = Query(None, description="班级ID"),
    current_user: User = Depends(get_current_user),
) -> List[StudentInDB]:
    """获取学生列表"""
    if class_id:
        return await student_repository.get_by_class(db, class_id=class_id)
    return await student_repository.get_multi(db, pagination=pagination)


# Course routes
@router.post("/courses", response_model=CourseInDB, status_code=status.HTTP_201_CREATED)
async def create_course(
    *, db: AsyncSession = Depends(async_db), course_in: CourseCreate, current_user: User = Depends(get_current_user)
) -> CourseInDB:
    """创建课程"""
    if not current_user.is_superuser:
        raise HTTPException(status_code=status.HTTP_403_FORBIDDEN, detail="没有权限执行此操作")

    course = await course_repository.get_by_code(db, code=course_in.code)
    if course:
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail="课程代码已存在")

    return await course_repository.create(db, obj_in=course_in)


@router.get("/courses", response_model=List[CourseInDB])
async def get_courses(
    *,
    db: AsyncSession = Depends(async_db),
    pagination: PaginationParams = Depends(),
    major_id: int = Query(None, description="专业ID"),
    teacher_id: int = Query(None, description="教师ID"),
    current_user: User = Depends(get_current_user),
) -> List[CourseInDB]:
    """获取课程列表"""
    if major_id:
        return await course_repository.get_by_major(db, major_id=major_id)
    if teacher_id:
        return await course_repository.get_by_teacher(db, teacher_id=teacher_id)
    return await course_repository.get_multi(db, pagination=pagination)
