"""
API路由主模块
用于注册所有的API路由和版本控制
"""

from fastapi import APIRouter

from api.v1.endpoints.academic.courses import grade, evaluation
from api.v1.endpoints.academic.students import students, courses
from api.v1.endpoints.academic.teachers import teachers, attendance, teaching
from api.v1.endpoints.auth import auth
from api.v1.endpoints.system import departments, majors, classes
from api.v1.endpoints.user import users

# 创建主路由
api_router = APIRouter()

# 认证模块
api_router.include_router(
    auth.router,
    prefix="/auth",
    tags=["认证管理"],
    responses={401: {"description": "认证失败"}},
)

# 用户管理
api_router.include_router(
    users.router,
    prefix="/users",
    tags=["用户管理"],
    responses={404: {"description": "未找到用户"}},
)

# 院系管理
api_router.include_router(
    departments.router,
    prefix="/departments",
    tags=["院系管理"],
    responses={404: {"description": "未找到院系"}},
)

# 专业管理
api_router.include_router(
    majors.router,
    prefix="/majors",
    tags=["专业管理"],
    responses={404: {"description": "未找到专业"}},
)

# 班级管理
api_router.include_router(
    classes.router,
    prefix="/classes",
    tags=["班级管理"],
    responses={404: {"description": "未找到班级"}},
)

# 教师管理
api_router.include_router(
    teachers.router,
    # prefix="/teachers",
    # tags=["教师管理"],
    responses={404: {"description": "未找到教师"}},
)

# 学生管理
api_router.include_router(
    students.router,
    # prefix="/students",
    # tags=["学生管理"],
    responses={404: {"description": "未找到学生"}},
)

# 课程管理
api_router.include_router(
    courses.router,
    prefix="/courses",
    tags=["课程管理"],
    responses={404: {"description": "未找到课程"}},
)

# 考勤管理
api_router.include_router(
    attendance.router,
    prefix="/attendance",
    tags=["考勤管理"],
    responses={404: {"description": "未找到考勤记录"}},
)

# 教学计划管理
api_router.include_router(
    teaching.router,
    prefix="/teaching",
    tags=["教学计划"],
    responses={404: {"description": "未找到教学计划"}},
)

# 成绩管理
api_router.include_router(
    grade.router,
    # prefix="/grade",
    # tags=["成绩管理"],
    responses={404: {"description": "未找到成绩记录"}},
)

# 评价管理
api_router.include_router(
    evaluation.router,
    # prefix="/evaluation",
    # tags=["评价管理"],
    responses={404: {"description": "未找到评价记录"}},
)
