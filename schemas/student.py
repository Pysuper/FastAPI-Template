from datetime import datetime
from typing import Optional

from pydantic import BaseModel, EmailStr, Field, validator

from constants.users import Gender, StudentStatus


class StudentBase(BaseModel):
    """学生基础模型"""

    name: str = Field(..., description="学生姓名")
    student_id: str = Field(..., description="学号")
    gender: Gender = Field(..., description="性别")
    birth_date: datetime = Field(..., description="出生日期")
    phone: Optional[str] = Field(None, description="电话号码")
    email: Optional[EmailStr] = Field(None, description="电子邮箱")
    address: Optional[str] = Field(None, description="地址")

    # 学籍信息
    department_id: int = Field(..., description="院系ID")
    major_id: int = Field(..., description="专业ID")
    class_id: int = Field(..., description="班级ID")
    enrollment_date: datetime = Field(..., description="入学日期")
    education_level: str = Field(..., description="学历层次")
    study_length: int = Field(..., description="学制(年)")

    # 其他信息
    political_status: Optional[str] = Field(None, description="政治面貌")
    nationality: Optional[str] = Field(None, description="民族")
    native_place: Optional[str] = Field(None, description="籍贯")
    photo_url: Optional[str] = Field(None, description="照片URL")

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

    @validator("study_length")
    def validate_study_length(cls, v):
        if v <= 0 or v > 8:
            raise ValueError("学制年限必须在1-8年之间")
        return v


class StudentCreate(StudentBase):
    """创建学生请求模型"""

    id_card: str = Field(..., description="身份证号")

    @validator("id_card")
    def validate_id_card(cls, v):
        if len(v) != 18 or not (v[:-1].isdigit() and (v[-1].isdigit() or v[-1].upper() == "X")):
            raise ValueError("无效的身份证号码格式")
        return v


class StudentUpdate(BaseModel):
    """更新学生请求模型"""

    name: Optional[str] = None
    gender: Optional[Gender] = None
    birth_date: Optional[datetime] = None
    phone: Optional[str] = None
    email: Optional[EmailStr] = None
    address: Optional[str] = None
    department_id: Optional[int] = None
    major_id: Optional[int] = None
    class_id: Optional[int] = None
    education_level: Optional[str] = None
    study_length: Optional[int] = None
    status: Optional[StudentStatus] = None
    is_registered: Optional[bool] = None
    political_status: Optional[str] = None
    nationality: Optional[str] = None
    native_place: Optional[str] = None
    photo_url: Optional[str] = None

    @validator("phone")
    def validate_phone(cls, v):
        if v and not v.isdigit():
            raise ValueError("电话号码只能包含数字")
        return v

    @validator("study_length")
    def validate_study_length(cls, v):
        if v is not None and (v <= 0 or v > 8):
            raise ValueError("学制年限必须在1-8年之间")
        return v


class StudentResponse(StudentBase):
    """学生响应模型"""

    id: int
    id_card: str
    status: StudentStatus = Field(default=StudentStatus.ACTIVE)
    is_registered: bool = Field(default=True)
    graduation_date: Optional[datetime] = None
    create_time: datetime
    update_time: Optional[datetime] = None

    class Config:
        from_attributes = True


class StudentFilter(BaseModel):
    """学生查询过滤模型"""

    keyword: Optional[str] = Field(None, description="关键字(学号/姓名/身份证号/电话)")
    department_id: Optional[int] = Field(None, description="院系ID")
    major_id: Optional[int] = Field(None, description="专业ID")
    class_id: Optional[int] = Field(None, description="班级ID")
    status: Optional[StudentStatus] = Field(None, description="学生状态")
    is_registered: Optional[bool] = Field(None, description="是否注册")
    enrollment_date_start: Optional[datetime] = Field(None, description="入学日期开始")
    enrollment_date_end: Optional[datetime] = Field(None, description="入学日期结束")


class StatusRecordCreate(BaseModel):
    """创建学籍变动记录请求模型"""

    student_id: int
    change_type: str
    original_department_id: Optional[int] = None
    original_major_id: Optional[int] = None
    original_class_id: Optional[int] = None
    target_department_id: Optional[int] = None
    target_major_id: Optional[int] = None
    target_class_id: Optional[int] = None
    reason: Optional[str] = None
    effective_date: datetime


class StatusRecordUpdate(BaseModel):
    """更新学籍变动记录请求模型"""

    reason: Optional[str] = None
    effective_date: Optional[datetime] = None
    status: Optional[str] = None
    approve_comments: Optional[str] = None


class StatusRecordResponse(BaseModel):
    """学籍变动记录响应模型"""

    id: int
    student_id: int
    change_type: str
    original_department_id: Optional[int]
    original_major_id: Optional[int]
    original_class_id: Optional[int]
    target_department_id: Optional[int]
    target_major_id: Optional[int]
    target_class_id: Optional[int]
    reason: Optional[str]
    effective_date: datetime
    status: str
    approver_id: Optional[int]
    approve_time: Optional[datetime]
    approve_comments: Optional[str]
    create_time: datetime
    update_time: Optional[datetime]

    class Config:
        from_attributes = True
