from datetime import datetime
from typing import Optional

from pydantic import BaseModel, Field, validator


class ActivityBase(BaseModel):
    """活动基础模型"""

    title: str = Field(..., description="活动标题")
    description: str = Field(..., description="活动描述")
    type: str = Field(..., description="活动类型")
    location: str = Field(..., description="活动地点")
    is_public: bool = Field(True, description="是否公开")


class ActivityCreate(ActivityBase):
    """活动创建模型"""

    start_time: datetime = Field(..., description="开始时间")
    end_time: datetime = Field(..., description="结束时间")
    max_participants: Optional[int] = Field(None, gt=0, description="最大参与人数")
    registration_deadline: Optional[datetime] = Field(None, description="报名截止时间")
    organizer_id: int = Field(..., description="组织者ID")

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

    @validator("max_participants")
    def validate_max_participants(cls, v):
        if v is not None and v <= 0:
            raise ValueError("最大参与人数必须大于0")
        return v


class ActivityUpdate(BaseModel):
    """活动更新模型"""

    title: Optional[str] = Field(None, description="活动标题")
    description: Optional[str] = Field(None, description="活动描述")
    start_time: Optional[datetime] = Field(None, description="开始时间")
    end_time: Optional[datetime] = Field(None, description="结束时间")
    location: Optional[str] = Field(None, description="活动地点")
    max_participants: Optional[int] = Field(None, gt=0, description="最大参与人数")
    registration_deadline: Optional[datetime] = Field(None, description="报名截止时间")
    is_public: Optional[bool] = Field(None, description="是否公开")

    @validator("end_time")
    def validate_end_time(cls, v, values):
        if v is not None and "start_time" in values and values["start_time"] is not None:
            if v <= values["start_time"]:
                raise ValueError("结束时间必须晚于开始时间")
        return v

    @validator("registration_deadline")
    def validate_registration_deadline(cls, v, values):
        if v is not None and "start_time" in values and values["start_time"] is not None:
            if v >= values["start_time"]:
                raise ValueError("报名截止时间必须早于活动开始时间")
        return v

    @validator("max_participants")
    def validate_max_participants(cls, v):
        if v is not None and v <= 0:
            raise ValueError("最大参与人数必须大于0")
        return v
