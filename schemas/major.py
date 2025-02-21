from typing import Optional

from pydantic import BaseModel


class MajorBase(BaseModel):
    name: str
    code: str
    description: Optional[str] = None
    duration: int = 4
    is_active: bool = True
    department_id: int


class MajorCreate(MajorBase):
    pass


class MajorUpdate(BaseModel):
    name: Optional[str] = None
    description: Optional[str] = None
    duration: Optional[int] = None
    is_active: Optional[bool] = None
    department_id: Optional[int] = None


class MajorResponse(MajorBase):
    id: int

    class Config:
        from_attributes = True
