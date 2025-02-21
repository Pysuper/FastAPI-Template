from datetime import datetime
from typing import List, Optional

from pydantic import BaseModel, Field, confloat


class GradeItemBase(BaseModel):
    """成绩项目基础模型"""

    name: str = Field(..., description="项目名称")
    description: Optional[str] = Field(None, description="项目描述")
    score: confloat(ge=0, le=100) = Field(..., description="分数")
    weight: confloat(ge=0, le=1) = Field(..., description="权重")
    type: str = Field(..., description="类型：作业、考试、其他")


class GradeItemCreate(GradeItemBase):
    """创建成绩项目模型"""

    grade_id: int = Field(..., description="成绩ID")


class GradeItemUpdate(GradeItemBase):
    """更新成绩项目模型"""

    pass


class GradeItemInDB(GradeItemBase):
    """数据库中的成绩项目模型"""

    id: int
    grade_id: int
    created_at: datetime
    updated_at: datetime

    class Config:
        from_attributes = True


class GradeRuleBase(BaseModel):
    """成绩规则基础模型"""

    name: str = Field(..., description="规则名称")
    description: Optional[str] = Field(None, description="规则描述")
    attendance_weight: confloat(ge=0, le=1) = Field(0.1, description="考勤成绩比例")
    homework_weight: confloat(ge=0, le=1) = Field(0.2, description="作业成绩比例")
    midterm_weight: confloat(ge=0, le=1) = Field(0.3, description="期中成绩比例")
    final_weight: confloat(ge=0, le=1) = Field(0.4, description="期末成绩比例")
    pass_score: confloat(ge=0, le=100) = Field(60.0, description="及格分数线")
    is_active: bool = Field(True, description="是否启用")


class GradeRuleCreate(GradeRuleBase):
    """创建成绩规则模型"""

    course_id: int = Field(..., description="课程ID")


class GradeRuleUpdate(GradeRuleBase):
    """更新成绩规则模型"""

    pass


class GradeRuleInDB(GradeRuleBase):
    """数据库中的成绩规则模型"""

    id: int
    course_id: int
    created_at: datetime
    updated_at: datetime

    class Config:
        from_attributes = True


class GradeBase(BaseModel):
    """成绩基础模型"""

    attendance_score: Optional[confloat(ge=0, le=100)] = Field(None, description="考勤成绩")
    homework_score: Optional[confloat(ge=0, le=100)] = Field(None, description="作业成绩")
    midterm_score: Optional[confloat(ge=0, le=100)] = Field(None, description="期中成绩")
    final_score: Optional[confloat(ge=0, le=100)] = Field(None, description="期末成绩")
    total_score: Optional[confloat(ge=0, le=100)] = Field(None, description="总评成绩")
    status: str = Field("draft", description="状态：草稿、已发布、已归档")
    notes: Optional[str] = Field(None, description="备注")


class GradeCreate(GradeBase):
    """创建成绩模型"""

    student_id: int = Field(..., description="学生ID")
    course_id: int = Field(..., description="课程ID")
    teacher_id: int = Field(..., description="教师ID")
    items: Optional[List[GradeItemCreate]] = Field([], description="成绩项目列表")


class GradeUpdate(GradeBase):
    """更新成绩模型"""

    items: Optional[List[GradeItemUpdate]] = Field(None, description="成绩项目列表")


class GradeInDB(GradeBase):
    """数据库中的成绩模型"""

    id: int
    student_id: int
    course_id: int
    teacher_id: int
    created_at: datetime
    updated_at: datetime
    items: List[GradeItemInDB] = []

    class Config:
        from_attributes = True


class GradeStatistics(BaseModel):
    """成绩统计模型"""

    total: int = Field(..., description="总人数")
    pass_count: int = Field(..., description="及格人数")
    fail_count: int = Field(..., description="不及格人数")
    highest_score: float = Field(..., description="最高分")
    lowest_score: float = Field(..., description="最低分")
    average_score: float = Field(..., description="平均分")
    score_distribution: dict = Field(..., description="分数段分布")


# class GradeCreate(BaseModel):
#     """创建成绩记录请求模型"""
#
#     student_id: int
#     course_id: int
#     semester_id: int
#     score: float
#     grade_point: float
#     grade_level: str
#     exam_score: Optional[float] = None
#     homework_score: Optional[float] = None
#     lab_score: Optional[float] = None
#     attendance_score: Optional[float] = None
#     midterm_score: Optional[float] = None
#     final_score: Optional[float] = None
#     comments: Optional[str] = None
#
#
# class GradeUpdate(BaseModel):
#     """更新成绩记录请求模型"""
#
#     score: Optional[float] = None
#     grade_point: Optional[float] = None
#     grade_level: Optional[str] = None
#     exam_score: Optional[float] = None
#     homework_score: Optional[float] = None
#     lab_score: Optional[float] = None
#     attendance_score: Optional[float] = None
#     midterm_score: Optional[float] = None
#     final_score: Optional[float] = None
#     status: Optional[str] = None
#     comments: Optional[str] = None


class GradeResponse(BaseModel):
    """成绩记录响应模型"""

    id: int
    student_id: int
    course_id: int
    semester_id: int
    score: float
    grade_point: float
    grade_level: str
    exam_score: Optional[float]
    homework_score: Optional[float]
    lab_score: Optional[float]
    attendance_score: Optional[float]
    midterm_score: Optional[float]
    final_score: Optional[float]
    status: str
    comments: Optional[str]
    create_time: datetime
    update_time: Optional[datetime]

    class Config:
        from_attributes = True
