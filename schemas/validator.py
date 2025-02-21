from datetime import datetime
from enum import Enum
from typing import Optional

from pydantic import BaseModel, validator, EmailStr


class Gender(str, Enum):
    MALE = "male"
    FEMALE = "female"
    OTHER = "other"


# 学生相关验证模型
class StudentCreate(BaseModel):
    student_id: str
    name: str
    gender: Gender
    birth_date: datetime
    phone: Optional[str] = None
    email: Optional[EmailStr] = None
    address: Optional[str] = None
    class_id: int
    parent_id: Optional[int] = None

    @validator("student_id")
    def validate_student_id(cls, v):
        if not v.isalnum():
            raise ValueError("学号只能包含字母和数字")
        return v

    @validator("phone")
    def validate_phone(cls, v):
        if v and not v.isdigit():
            raise ValueError("电话号码只能包含数字")
        return v


class StudentUpdate(BaseModel):
    name: Optional[str] = None
    phone: Optional[str] = None
    email: Optional[EmailStr] = None
    address: Optional[str] = None
    class_id: Optional[int] = None
    parent_id: Optional[int] = None


# 课程相关验证模型
class CourseCreate(BaseModel):
    code: str
    name: str
    description: Optional[str] = None
    credits: int
    hours: int
    teacher_id: int

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


class CourseUpdate(BaseModel):
    name: Optional[str] = None
    description: Optional[str] = None
    credits: Optional[int] = None
    hours: Optional[int] = None
    teacher_id: Optional[int] = None


# 考试相关验证模型
class ExamCreate(BaseModel):
    title: str
    description: Optional[str] = None
    course_id: int
    start_time: datetime
    end_time: datetime
    duration: int
    total_score: float

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


class ExamUpdate(BaseModel):
    title: Optional[str] = None
    description: Optional[str] = None
    start_time: Optional[datetime] = None
    end_time: Optional[datetime] = None
    duration: Optional[int] = None
    total_score: Optional[float] = None


# 图书馆资源相关验证模型
class ResourceCreate(BaseModel):
    title: str
    type: str
    author: str
    publisher: Optional[str] = None
    publish_date: Optional[datetime] = None
    isbn: Optional[str] = None
    description: Optional[str] = None
    file_path: str
    category_id: int

    @validator("isbn")
    def validate_isbn(cls, v):
        if v and not v.replace("-", "").isdigit():
            raise ValueError("ISBN格式不正确")
        return v


class ResourceUpdate(BaseModel):
    title: Optional[str] = None
    author: Optional[str] = None
    publisher: Optional[str] = None
    publish_date: Optional[datetime] = None
    description: Optional[str] = None
    category_id: Optional[int] = None


# 活动相关验证模型
class ActivityCreate(BaseModel):
    title: str
    description: str
    type: str
    start_time: datetime
    end_time: datetime
    location: str
    max_participants: Optional[int] = None
    registration_deadline: Optional[datetime] = None
    is_public: bool = True
    organizer_id: int

    @validator("end_time")
    def validate_end_time(cls, v, values):
        if "start_time" in values and v <= values["start_time"]:
            raise ValueError("结束时间必须晚于开始时间")
        return v

    @validator("registration_deadline")
    def validate_registration_deadline(cls, v, values):
        if v and "start_time" in values and v >= values["start_time"]:
            raise ValueError("报名截止时间必须早于活动开始时间")
        return v


class ActivityUpdate(BaseModel):
    title: Optional[str] = None
    description: Optional[str] = None
    start_time: Optional[datetime] = None
    end_time: Optional[datetime] = None
    location: Optional[str] = None
    max_participants: Optional[int] = None
    registration_deadline: Optional[datetime] = None
    is_public: Optional[bool] = None


# 通用响应模型
class ResponseModel(BaseModel):
    code: int = 200
    message: str = "success"
    data: Optional[dict] = None
