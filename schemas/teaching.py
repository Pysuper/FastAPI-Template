from datetime import datetime
from typing import List, Optional

from pydantic import BaseModel, Field


class TeachingPlanDetailBase(BaseModel):
    """教学计划详情基础模型"""

    week: int = Field(..., description="教学周次")
    hours: int = Field(..., description="课时数")
    content: str = Field(..., description="教学内容")
    objectives: str = Field(..., description="教学目标")
    methods: Optional[str] = Field(None, description="教学方法")
    resources: Optional[str] = Field(None, description="教学资源")
    assignments: Optional[str] = Field(None, description="作业要求")


class TeachingPlanDetailCreate(TeachingPlanDetailBase):
    """创建教学计划详情模型"""

    plan_id: int = Field(..., description="教学计划ID")


class TeachingPlanDetailUpdate(TeachingPlanDetailBase):
    """更新教学计划详情模型"""

    pass


class TeachingPlanDetailInDB(TeachingPlanDetailBase):
    """数据库中的教学计划详情模型"""

    id: int
    plan_id: int
    created_at: datetime
    updated_at: datetime

    class Config:
        from_attributes = True


class TeachingScheduleBase(BaseModel):
    """教学进度基础模型"""

    actual_date: datetime = Field(..., description="实际授课日期")
    actual_content: str = Field(..., description="实际教学内容")
    completion_rate: int = Field(..., ge=0, le=100, description="完成度（百分比）")
    status: str = Field(..., description="状态：待完成、已完成、延期、取消")
    notes: Optional[str] = Field(None, description="备注")


class TeachingScheduleCreate(TeachingScheduleBase):
    """创建教学进度模型"""

    plan_id: int = Field(..., description="教学计划ID")
    detail_id: int = Field(..., description="教学计划详情ID")


class TeachingScheduleUpdate(TeachingScheduleBase):
    """更新教学进度模型"""

    pass


class TeachingScheduleInDB(TeachingScheduleBase):
    """数据库中的教学进度模型"""

    id: int
    plan_id: int
    detail_id: int
    created_at: datetime
    updated_at: datetime

    class Config:
        from_attributes = True


class TeachingPlanBase(BaseModel):
    """教学计划基础模型"""

    name: str = Field(..., description="计划名称")
    description: Optional[str] = Field(None, description="计划描述")
    semester: str = Field(..., description="学期")
    year: int = Field(..., description="学年")
    status: str = Field(..., description="状态：草稿、已发布、已归档")


class TeachingPlanCreate(TeachingPlanBase):
    """创建教学计划模型"""

    course_id: int = Field(..., description="课程ID")
    teacher_id: int = Field(..., description="教师ID")
    details: List[TeachingPlanDetailCreate] = Field([], description="教学计划详情列表")


class TeachingPlanUpdate(TeachingPlanBase):
    """更新教学计划模型"""

    details: Optional[List[TeachingPlanDetailUpdate]] = Field(None, description="教学计划详情列表")


class TeachingPlanInDB(TeachingPlanBase):
    """数据库中的教学计划模型"""

    id: int
    course_id: int
    teacher_id: int
    created_at: datetime
    updated_at: datetime
    details: List[TeachingPlanDetailInDB] = []
    schedules: List[TeachingScheduleInDB] = []

    class Config:
        from_attributes = True
