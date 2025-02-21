# -*- coding:utf-8 -*-
"""
@Project ：Speedy 
@File    ：__init__.py
@Author  ：PySuper
@Date    ：2024-12-19 23:14
@Desc    ：Speedy __init__
"""

# from fastapi import APIRouter
# from .student import router as student_router
# from .course import router as course_router
# from .exam import router as exam_router
# from .library import router as library_router
# from .activity import router as activity_router
#
# # 创建主路由
# router = APIRouter(prefix="/api/v1")
#
# # 注册子路由
# router.include_router(student_router)
# router.include_router(course_router)
# router.include_router(exam_router)
# router.include_router(library_router)
# router.include_router(activity_router)
#
# # API版本信息
# @router.get("/version")
# async def get_version():
#     return {
#         "version": "1.0.0",
#         "name": "Speedy School Management System API",
#         "description": "学校信息管理平台API"
#     }
