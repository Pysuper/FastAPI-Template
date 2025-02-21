from typing import Optional

from pydantic import BaseModel


class ClassBase(BaseModel):
    name: str
    code: str
    grade: int
    capacity: int = 50
    is_active: bool = True
    major_id: int
    teacher_id: Optional[int] = None


class ClassCreate(ClassBase):
    pass


class ClassUpdate(BaseModel):
    name: Optional[str] = None
    capacity: Optional[int] = None
    is_active: Optional[bool] = None
    teacher_id: Optional[int] = None
    major_id: Optional[int] = None


class ClassResponse(ClassBase):
    id: int

    class Config:
        from_attributes = True
