from datetime import datetime
from typing import Optional

from pydantic import BaseModel, Field, validator


class ExamBase(BaseModel):
    """考试基础模型"""

    title: str = Field(..., description="考试标题")
    description: Optional[str] = Field(None, description="考试描述")
    course_id: int = Field(..., description="课程ID")
    total_score: float = Field(..., gt=0, description="总分")


class ExamCreate(ExamBase):
    """考试创建模型"""

    start_time: datetime = Field(..., description="开始时间")
    end_time: datetime = Field(..., description="结束时间")
    duration: int = Field(..., gt=0, description="考试时长(分钟)")

    @validator("end_time")
    def validate_end_time(cls, v, values):
        if "start_time" in values and v <= values["start_time"]:
            raise ValueError("结束时间必须晚于开始时间")
        return v

    @validator("duration")
    def validate_duration(cls, v):
        if v <= 0:
            raise ValueError("考试时长必须大于0")
        return v

    @validator("total_score")
    def validate_total_score(cls, v):
        if v <= 0:
            raise ValueError("总分必须大于0")
        return v


class ExamUpdate(BaseModel):
    """考试更新模型"""

    title: Optional[str] = Field(None, description="考试标题")
    description: Optional[str] = Field(None, description="考试描述")
    start_time: Optional[datetime] = Field(None, description="开始时间")
    end_time: Optional[datetime] = Field(None, description="结束时间")
    duration: Optional[int] = Field(None, gt=0, description="考试时长(分钟)")
    total_score: Optional[float] = Field(None, gt=0, description="总分")

    @validator("end_time")
    def validate_end_time(cls, v, values):
        if v is not None and "start_time" in values and values["start_time"] is not None:
            if v <= values["start_time"]:
                raise ValueError("结束时间必须晚于开始时间")
        return v

    @validator("duration")
    def validate_duration(cls, v):
        if v is not None and v <= 0:
            raise ValueError("考试时长必须大于0")
        return v

    @validator("total_score")
    def validate_total_score(cls, v):
        if v is not None and v <= 0:
            raise ValueError("总分必须大于0")
        return v


class ExamCreate(BaseModel):
    """创建考试请求模型"""

    title: str
    description: Optional[str] = None
    exam_type: str
    start_time: datetime
    end_time: datetime
    duration: int
    total_score: int
    pass_score: int
    course_id: int
    teacher_id: int


class ExamUpdate(BaseModel):
    """更新考试请求模型"""

    title: Optional[str] = None
    description: Optional[str] = None
    exam_type: Optional[str] = None
    start_time: Optional[datetime] = None
    end_time: Optional[datetime] = None
    duration: Optional[int] = None
    total_score: Optional[int] = None
    pass_score: Optional[int] = None
    status: Optional[str] = None


class ExamResponse(BaseModel):
    """考试响应模型"""

    id: int
    title: str
    description: Optional[str]
    exam_type: str
    start_time: datetime
    end_time: datetime
    duration: int
    total_score: int
    pass_score: int
    course_id: int
    teacher_id: int
    status: str
    create_time: datetime
    update_time: Optional[datetime]

    class Config:
        from_attributes = True


class ExamFilter:
    pass


class ExamGradeCreate(BaseModel):
    """创建考试成绩请求模型"""

    exam_id: int
    student_id: int
    score: float
    comments: Optional[str] = None


class ExamGradeUpdate(BaseModel):
    """更新考试成绩请求模型"""

    score: Optional[float] = None
    status: Optional[str] = None
    comments: Optional[str] = None


class ExamGradeResponse(BaseModel):
    """考试成绩响应模型"""

    id: int
    exam_id: int
    student_id: int
    score: float
    status: str
    grader_id: Optional[int]
    grade_time: Optional[datetime]
    comments: Optional[str]
    create_time: datetime
    update_time: Optional[datetime]

    class Config:
        from_attributes = True


class ExamScheduleCreate(BaseModel):
    """创建考试安排请求模型"""

    exam_id: int
    room_id: int
    invigilator_id: int
    start_time: datetime
    end_time: datetime
    capacity: int


class ExamScheduleUpdate(BaseModel):
    """更新考试安排请求模型"""

    room_id: Optional[int] = None
    invigilator_id: Optional[int] = None
    start_time: Optional[datetime] = None
    end_time: Optional[datetime] = None
    capacity: Optional[int] = None
    actual_count: Optional[int] = None
    status: Optional[str] = None


class ExamScheduleResponse(BaseModel):
    """考试安排响应模型"""

    id: int
    exam_id: int
    room_id: int
    invigilator_id: int
    start_time: datetime
    end_time: datetime
    capacity: int
    actual_count: int
    status: str
    create_time: datetime
    update_time: Optional[datetime]

    class Config:
        from_attributes = True
