from datetime import datetime
from typing import Optional

from pydantic import BaseModel, Field, validator


class CourseBase(BaseModel):
    """课程基础模型"""

    name: str = Field(..., description="课程名称")
    description: Optional[str] = Field(None, description="课程描述")
    credits: int = Field(..., ge=1, description="学分")
    hours: int = Field(..., ge=1, description="课时")


class CourseCreate(CourseBase):
    """课程创建模型"""

    code: str = Field(..., description="课程代码")
    teacher_id: int = Field(..., description="教师ID")

    @validator("credits")
    def validate_credits(cls, v):
        if v <= 0:
            raise ValueError("学分必须大于0")
        return v

    @validator("hours")
    def validate_hours(cls, v):
        if v <= 0:
            raise ValueError("课时必须大于0")
        return v

    @validator("code")
    def validate_code(cls, v):
        if not v.isalnum():
            raise ValueError("课程代码只能包含字母和数字")
        return v


class CourseUpdate(BaseModel):
    """课程更新模型"""

    name: Optional[str] = Field(None, description="课程名称")
    description: Optional[str] = Field(None, description="课程描述")
    credits: Optional[int] = Field(None, ge=1, description="学分")
    hours: Optional[int] = Field(None, ge=1, description="课时")
    teacher_id: Optional[int] = Field(None, description="教师ID")

    @validator("credits")
    def validate_credits(cls, v):
        if v is not None and v <= 0:
            raise ValueError("学分必须大于0")
        return v

    @validator("hours")
    def validate_hours(cls, v):
        if v is not None and v <= 0:
            raise ValueError("课时必须大于0")
        return v


class CourseResponse(CourseBase):
    """课程响应模型"""

    id: int = Field(..., description="课程ID")
    code: str = Field(..., description="课程代码")
    teacher_id: int = Field(..., description="教师ID")
    created_at: datetime = Field(..., description="创建时间")
    updated_at: datetime = Field(..., description="更新时间")

    class Config:
        from_attributes = True


class CourseGradeBase(BaseModel):
    """成绩基础模型"""

    student_id: int = Field(..., description="学生ID")
    score: float = Field(..., ge=0, le=100, description="分数")
    level: Optional[str] = Field(None, description="等级")
    status: str = Field("pending", description="状态")
    semester: str = Field(..., description="学期")
    remark: Optional[str] = Field(None, description="备注")

    @validator("score")
    def validate_score(cls, v):
        if v < 0 or v > 100:
            raise ValueError("分数必须在0-100之间")
        return v

    @validator("status")
    def validate_status(cls, v):
        valid_status = {"pending", "approved", "rejected"}
        if v not in valid_status:
            raise ValueError(f"状态必须是以下之一: {valid_status}")
        return v


class CourseGradeCreate(CourseGradeBase):
    """成绩创建模型"""

    pass


class CourseGradeUpdate(BaseModel):
    """成绩更新模型"""

    score: Optional[float] = Field(None, ge=0, le=100, description="分数")
    level: Optional[str] = Field(None, description="等级")
    status: Optional[str] = Field(None, description="状态")
    remark: Optional[str] = Field(None, description="备注")

    @validator("score")
    def validate_score(cls, v):
        if v is not None and (v < 0 or v > 100):
            raise ValueError("分数必须在0-100之间")
        return v

    @validator("status")
    def validate_status(cls, v):
        if v is not None:
            valid_status = {"pending", "approved", "rejected"}
            if v not in valid_status:
                raise ValueError(f"状态必须是以下之一: {valid_status}")
        return v


class CourseGradeResponse(CourseGradeBase):
    """成绩响应模型"""

    id: int = Field(..., description="成绩ID")
    course_id: int = Field(..., description="课程ID")
    created_at: datetime = Field(..., description="创建时间")
    updated_at: datetime = Field(..., description="更新时间")

    class Config:
        from_attributes = True


class CourseGradeStatusUpdate(BaseModel):
    """成绩状态更新模型"""

    status: str = Field(..., description="状态")

    @validator("status")
    def validate_status(cls, v):
        valid_status = {"pending", "approved", "rejected"}
        if v not in valid_status:
            raise ValueError(f"状态必须是以下之一: {valid_status}")
        return v


class CourseGradeScoreUpdate(BaseModel):
    """成绩分数更新模型"""

    score: float = Field(..., ge=0, le=100, description="分数")

    @validator("score")
    def validate_score(cls, v):
        if v < 0 or v > 100:
            raise ValueError("分数必须在0-100之间")
        return v


class CourseGradeLevelUpdate(BaseModel):
    """成绩等级更新模型"""

    level: str = Field(..., description="等级")

    @validator("level")
    def validate_level(cls, v):
        valid_levels = {"A", "B", "C", "D", "F"}
        if v not in valid_levels:
            raise ValueError(f"等级必须是以下之一: {valid_levels}")
        return v


class CourseSelect(BaseModel):
    """选课请求模型"""

    course_id: int
    semester_id: int


# class CourseUpdate(BaseModel):
#     """更新选课记录请求模型"""
#
#     status: Optional[str] = None
#     score: Optional[float] = None
#     grade_point: Optional[float] = None
#     attendance_rate: Optional[float] = None
#     comments: Optional[str] = None
#
#
# class CourseResponse(BaseModel):
#     """选课记录响应模型"""
#
#     id: int
#     student_id: int
#     course_id: int
#     semester_id: int
#     status: str
#     score: Optional[float]
#     grade_point: Optional[float]
#     attendance_rate: Optional[float]
#     comments: Optional[str]
#     create_time: datetime
#     update_time: Optional[datetime]
#
#     class Config:
#         from_attributes = True


class CourseAssign(BaseModel):
    """分配课程请求模型"""

    teacher_id: int
    course_id: int
    semester_id: int
    role: str
    workload: float
    comments: Optional[str] = None


# class CourseUpdate(BaseModel):
#     """更新课程记录请求模型"""
#
#     role: Optional[str] = None
#     workload: Optional[float] = None
#     status: Optional[str] = None
#     evaluation_score: Optional[float] = None
#     comments: Optional[str] = None
#
#
# class CourseResponse(BaseModel):
#     """课程记录响应模型"""
#
#     id: int
#     teacher_id: int
#     course_id: int
#     semester_id: int
#     role: str
#     workload: float
#     status: str
#     evaluation_score: Optional[float]
#     comments: Optional[str]
#     create_time: datetime
#     update_time: Optional[datetime]
#
#     class Config:
#         from_attributes = True
