from datetime import datetime
from typing import Optional

from pydantic import BaseModel, Field


class CourseEnrollmentBase(BaseModel):
    """选课记录基础模型"""

    status: str = Field("pending", description="状态：待审核、已通过、已拒绝、已退课、已完成")
    notes: Optional[str] = Field(None, description="备注")


class CourseEnrollmentCreate(CourseEnrollmentBase):
    """创建选课记录模型"""

    student_id: int = Field(..., description="学生ID")
    course_id: int = Field(..., description="课程ID")


class CourseEnrollmentUpdate(CourseEnrollmentBase):
    """更新选课记录模型"""

    pass


class CourseEnrollmentInDB(CourseEnrollmentBase):
    """数据库中的选课记录模型"""

    id: int
    student_id: int
    course_id: int
    enrollment_date: datetime
    approval_date: Optional[datetime]
    drop_date: Optional[datetime]
    created_at: datetime
    updated_at: datetime

    class Config:
        from_attributes = True


class EnrollmentRuleBase(BaseModel):
    """选课规则基础模型"""

    name: str = Field(..., description="规则名称")
    description: Optional[str] = Field(None, description="规则描述")
    start_date: datetime = Field(..., description="开始时间")
    end_date: datetime = Field(..., description="结束时间")
    min_students: int = Field(1, description="最少选课人数")
    max_students: int = Field(..., description="最大选课人数")
    prerequisites: Optional[str] = Field(None, description="先修课程要求")
    grade_requirements: Optional[str] = Field(None, description="成绩要求")
    year_requirements: Optional[str] = Field(None, description="年级要求")
    major_requirements: Optional[str] = Field(None, description="专业要求")
    need_approval: bool = Field(False, description="是否需要审批")
    auto_approve: bool = Field(True, description="是否自动审批")
    allow_drop: bool = Field(True, description="是否允许退课")
    drop_deadline: Optional[datetime] = Field(None, description="退课截止时间")
    is_active: bool = Field(True, description="是否启用")


class EnrollmentRuleCreate(EnrollmentRuleBase):
    """创建选课规则模型"""

    course_id: int = Field(..., description="课程ID")


class EnrollmentRuleUpdate(EnrollmentRuleBase):
    """更新选课规则模型"""

    pass


class EnrollmentRuleInDB(EnrollmentRuleBase):
    """数据库中的选课规则模型"""

    id: int
    course_id: int
    created_at: datetime
    updated_at: datetime

    class Config:
        from_attributes = True


class EnrollmentPeriodBase(BaseModel):
    """选课时段基础模型"""

    name: str = Field(..., description="时段名称")
    description: Optional[str] = Field(None, description="时段描述")
    type: str = Field("normal", description="类型：正常选课、补选、退课")
    start_date: datetime = Field(..., description="开始时间")
    end_date: datetime = Field(..., description="结束时间")
    status: str = Field("upcoming", description="状态：即将开始、进行中、已结束")
    target_grades: Optional[str] = Field(None, description="目标年级")
    target_majors: Optional[str] = Field(None, description="目标专业")
    is_active: bool = Field(True, description="是否启用")


class EnrollmentPeriodCreate(EnrollmentPeriodBase):
    """创建选课时段模型"""

    semester_id: int = Field(..., description="学期ID")


class EnrollmentPeriodUpdate(EnrollmentPeriodBase):
    """更新选课时段模型"""

    pass


class EnrollmentPeriodInDB(EnrollmentPeriodBase):
    """数据库中的选课时段模型"""

    id: int
    semester_id: int
    created_at: datetime
    updated_at: datetime

    class Config:
        from_attributes = True


class EnrollmentStatistics(BaseModel):
    """选课统计模型"""

    total_courses: int = Field(..., description="课程总数")
    total_students: int = Field(..., description="选课学生总数")
    avg_students_per_course: float = Field(..., description="每门课程平均选课人数")
    full_courses: int = Field(..., description="已满课程数")
    available_courses: int = Field(..., description="可选课程数")
    pending_approvals: int = Field(..., description="待审批数")
    course_distribution: dict = Field(..., description="课程分布")
