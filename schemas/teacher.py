from datetime import date, datetime
from typing import Optional

from pydantic import BaseModel, EmailStr


class TeacherBase(BaseModel):
    name: str
    code: str
    title: Optional[str] = None
    email: Optional[EmailStr] = None
    phone: Optional[str] = None
    gender: str
    birth_date: Optional[date] = None
    is_active: bool = True
    department_id: int


class TeacherCreate(TeacherBase):
    pass


class TeacherUpdate(BaseModel):
    name: Optional[str] = None
    title: Optional[str] = None
    email: Optional[EmailStr] = None
    phone: Optional[str] = None
    is_active: Optional[bool] = None
    department_id: Optional[int] = None


class TeacherFilter(BaseModel):
    name: Optional[str] = None
    title: Optional[str] = None
    email: Optional[EmailStr] = None
    phone: Optional[str] = None
    gender: Optional[str] = None
    birth_date: Optional[date] = None
    is_active: Optional[bool] = None
    department_id: Optional[int] = None


class TeacherResponse(TeacherBase):
    id: int

    class Config:
        from_attributes = True


# ----------------------------------------------------------------------------------------------------------------------
# class TeacherCreate(PydanticBaseModel):
#     """创建教师请求模型"""
#
#     teacher_id: str
#     name: str
#     gender: str
#     birth_date: datetime
#     id_card: str
#     phone: Optional[str] = None
#     email: Optional[EmailStr] = None
#     address: Optional[str] = None
#     department_id: int
#     title: str
#     position: str
#     hire_date: datetime
#     education: str
#     degree: str
#     research_direction: Optional[str] = None
#     is_full_time: Optional[bool] = True
#     political_status: Optional[str] = None
#     nationality: Optional[str] = None
#     native_place: Optional[str] = None
#     photo_url: Optional[str] = None
#
#
# class TeacherUpdate(PydanticBaseModel):
#     """更新教师请求模型"""
#
#     name: Optional[str] = None
#     gender: Optional[str] = None
#     birth_date: Optional[datetime] = None
#     phone: Optional[str] = None
#     email: Optional[EmailStr] = None
#     address: Optional[str] = None
#     department_id: Optional[int] = None
#     title: Optional[str] = None
#     position: Optional[str] = None
#     education: Optional[str] = None
#     degree: Optional[str] = None
#     research_direction: Optional[str] = None
#     status: Optional[str] = None
#     is_full_time: Optional[bool] = None
#     political_status: Optional[str] = None
#     nationality: Optional[str] = None
#     native_place: Optional[str] = None
#     photo_url: Optional[str] = None
#
#
# class TeacherResponse(PydanticBaseModel):
#     """教师响应模型"""
#
#     id: int
#     teacher_id: str
#     name: str
#     gender: str
#     birth_date: datetime
#     id_card: str
#     phone: Optional[str]
#     email: Optional[str]
#     address: Optional[str]
#     department_id: int
#     title: str
#     position: str
#     hire_date: datetime
#     leave_date: Optional[datetime]
#     education: str
#     degree: str
#     research_direction: Optional[str]
#     status: str
#     is_full_time: bool
#     political_status: Optional[str]
#     nationality: Optional[str]
#     native_place: Optional[str]
#     photo_url: Optional[str]
#     create_time: datetime
#     update_time: Optional[datetime]
#
#     class Config:
#         from_attributes = True


class TitleCreate(BaseModel):
    """创建职称记录请求模型"""

    teacher_id: int
    title: str
    level: str
    certificate_no: Optional[str] = None
    issue_date: datetime
    issue_authority: str
    comments: Optional[str] = None


class TitleUpdate(BaseModel):
    """更新职称记录请求模型"""

    title: Optional[str] = None
    level: Optional[str] = None
    certificate_no: Optional[str] = None
    issue_date: Optional[datetime] = None
    issue_authority: Optional[str] = None
    status: Optional[str] = None
    revoke_reason: Optional[str] = None
    comments: Optional[str] = None


class TitleResponse(BaseModel):
    """职称记录响应模型"""

    id: int
    teacher_id: int
    title: str
    level: str
    certificate_no: Optional[str]
    issue_date: datetime
    issue_authority: str
    status: str
    revoke_reason: Optional[str]
    comments: Optional[str]
    create_time: datetime
    update_time: Optional[datetime]

    class Config:
        from_attributes = True


class AttendanceCreate(BaseModel):
    """创建考勤记录请求模型"""

    teacher_id: int
    date: date
    type: str
    check_in_time: Optional[datetime] = None
    check_out_time: Optional[datetime] = None
    leave_type: Optional[str] = None
    leave_reason: Optional[str] = None
    location: Optional[str] = None
    device: Optional[str] = None
    comments: Optional[str] = None


class AttendanceUpdate(BaseModel):
    """更新考勤记录请求模型"""

    type: Optional[str] = None
    check_in_time: Optional[datetime] = None
    check_out_time: Optional[datetime] = None
    leave_type: Optional[str] = None
    leave_reason: Optional[str] = None
    approve_status: Optional[str] = None
    approve_comments: Optional[str] = None
    location: Optional[str] = None
    device: Optional[str] = None
    comments: Optional[str] = None


class AttendanceResponse(BaseModel):
    """考勤记录响应模型"""

    id: int
    teacher_id: int
    date: date
    type: str
    check_in_time: Optional[datetime]
    check_out_time: Optional[datetime]
    leave_type: Optional[str]
    leave_reason: Optional[str]
    approver_id: Optional[int]
    approve_time: Optional[datetime]
    approve_status: str
    approve_comments: Optional[str]
    location: Optional[str]
    device: Optional[str]
    comments: Optional[str]
    create_time: datetime
    update_time: Optional[datetime]

    class Config:
        from_attributes = True
