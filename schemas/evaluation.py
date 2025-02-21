from datetime import datetime
from typing import Dict, Optional

from pydantic import BaseModel, Field, field_validator


class EvaluationIndicatorBase(BaseModel):
    """教学评价指标基础模型"""

    name: str = Field(..., description="指标名称")
    description: Optional[str] = Field(None, description="指标描述")
    weight: float = Field(1.0, ge=0, le=1.0, description="权重")
    max_score: int = Field(100, ge=0, description="最高分")
    min_score: int = Field(0, ge=0, description="最低分")
    type: str = Field(..., description="类型")
    is_active: bool = Field(True, description="是否启用")

    @field_validator("type")
    @classmethod
    def validate_type(cls, v: str):
        valid_types = {"teaching_attitude", "teaching_content", "teaching_method", "teaching_effect"}
        if v not in valid_types:
            raise ValueError(f"类型必须是以下之一: {valid_types}")
        return v

    @field_validator("weight")
    @classmethod
    def validate_weight(cls, v: float):
        if v < 0 or v > 1:
            raise ValueError("权重必须在0-1之间")
        return v

    @field_validator("max_score")
    @classmethod
    def validate_max_score(cls, v: int, info):
        if "min_score" in info.data and v < info.data["min_score"]:
            raise ValueError("最高分必须大于等于最低分")
        return v


class EvaluationIndicatorCreate(EvaluationIndicatorBase):
    """创建教学评价指标模型"""

    pass


class EvaluationIndicatorUpdate(BaseModel):
    """更新教学评价指标模型"""

    name: Optional[str] = Field(None, description="指标名称")
    description: Optional[str] = Field(None, description="指标描述")
    weight: Optional[float] = Field(None, ge=0, le=1.0, description="权重")
    max_score: Optional[int] = Field(None, ge=0, description="最高分")
    min_score: Optional[int] = Field(None, ge=0, description="最低分")
    type: Optional[str] = Field(None, description="类型")
    is_active: Optional[bool] = Field(None, description="是否启用")

    @field_validator("type")
    @classmethod
    def validate_type(cls, v: Optional[str]):
        if v is not None:
            valid_types = {"teaching_attitude", "teaching_content", "teaching_method", "teaching_effect"}
            if v not in valid_types:
                raise ValueError(f"类型必须是以下之一: {valid_types}")
        return v

    @field_validator("weight")
    @classmethod
    def validate_weight(cls, v: Optional[float]):
        if v is not None and (v < 0 or v > 1):
            raise ValueError("权重必须在0-1之间")
        return v

    @field_validator("max_score")
    @classmethod
    def validate_max_score(cls, v: Optional[int], info):
        if (
            v is not None
            and "min_score" in info.data
            and info.data["min_score"] is not None
            and v < info.data["min_score"]
        ):
            raise ValueError("最高分必须大于等于最低分")
        return v


class EvaluationIndicatorInDB(EvaluationIndicatorBase):
    """数据库中的教学评价指标模型"""

    id: int = Field(..., description="指标ID")
    created_at: datetime = Field(..., description="创建时间")
    updated_at: datetime = Field(..., description="更新时间")

    class Config:
        from_attributes = True


class CourseEvaluationBase(BaseModel):
    """课程评价基础模型"""

    student_id: int = Field(..., description="学生ID")
    score: float = Field(..., ge=1, le=5, description="评分")
    comment: str = Field(..., min_length=1, max_length=1000, description="评价内容")
    status: str = Field("pending", description="状态")
    semester: str = Field(..., description="学期")
    anonymous: bool = Field(False, description="是否匿名")

    @field_validator("score")
    @classmethod
    def validate_score(cls, v: float):
        if v < 1 or v > 5:
            raise ValueError("评分必须在1-5之间")
        return v

    @field_validator("status")
    @classmethod
    def validate_status(cls, v: str):
        valid_status = {"pending", "approved", "rejected"}
        if v not in valid_status:
            raise ValueError(f"状态必须是以下之一: {valid_status}")
        return v


class CourseEvaluationCreate(CourseEvaluationBase):
    """课程评价创建模型"""

    pass


class CourseEvaluationUpdate(BaseModel):
    """课程评价更新模型"""

    score: Optional[float] = Field(None, ge=1, le=5, description="评分")
    comment: Optional[str] = Field(None, min_length=1, max_length=1000, description="评价内容")
    status: Optional[str] = Field(None, description="状态")
    anonymous: Optional[bool] = Field(None, description="是否匿名")

    @field_validator("score")
    @classmethod
    def validate_score(cls, v: Optional[float]):
        if v is not None and (v < 1 or v > 5):
            raise ValueError("评分必须在1-5之间")
        return v

    @field_validator("status")
    @classmethod
    def validate_status(cls, v: Optional[str]):
        if v is not None:
            valid_status = {"pending", "approved", "rejected"}
            if v not in valid_status:
                raise ValueError(f"状态必须是以下之一: {valid_status}")
        return v


class CourseEvaluationResponse(CourseEvaluationBase):
    """课程评价响应模型"""

    id: int = Field(..., description="评价ID")
    course_id: int = Field(..., description="课程ID")
    created_at: datetime = Field(..., description="创建时间")
    updated_at: datetime = Field(..., description="更新时间")

    class Config:
        from_attributes = True


class CourseEvaluationStatusUpdate(BaseModel):
    """课程评价状态更新模型"""

    status: str = Field(..., description="状态")

    @field_validator("status")
    @classmethod
    def validate_status(cls, v: str):
        valid_status = {"pending", "approved", "rejected"}
        if v not in valid_status:
            raise ValueError(f"状态必须是以下之一: {valid_status}")
        return v


class CourseEvaluationScoreUpdate(BaseModel):
    """课程评价分数更新模型"""

    score: float = Field(..., ge=1, le=5, description="评分")

    @field_validator("score")
    @classmethod
    def validate_score(cls, v: float):
        if v < 1 or v > 5:
            raise ValueError("评分必须在1-5之间")
        return v


class CourseEvaluationCommentUpdate(BaseModel):
    """课程评价内容更新模型"""

    comment: str = Field(..., min_length=1, max_length=1000, description="评价内容")


class EvaluationRuleBase(BaseModel):
    """教学评价规则基础模型"""

    name: str = Field(..., description="规则名称")
    description: Optional[str] = Field(None, description="规则描述")
    start_date: datetime = Field(..., description="开始时间")
    end_date: datetime = Field(..., description="结束时间")
    is_required: bool = Field(True, description="是否必须评价")
    min_word_count: int = Field(0, ge=0, description="最少字数要求")
    allow_anonymous: bool = Field(False, description="是否允许匿名")
    target_type: str = Field(..., description="评价对象类型")
    is_active: bool = Field(True, description="是否启用")

    @field_validator("end_date")
    @classmethod
    def validate_end_date(cls, v: datetime, info):
        if "start_date" in info.data and v <= info.data["start_date"]:
            raise ValueError("结束时间必须晚于开始时间")
        return v

    @field_validator("target_type")
    @classmethod
    def validate_target_type(cls, v: str):
        valid_types = {"course", "teacher"}
        if v not in valid_types:
            raise ValueError(f"评价对象类型必须是以下之一: {valid_types}")
        return v

    @field_validator("min_word_count")
    @classmethod
    def validate_min_word_count(cls, v: int):
        if v < 0:
            raise ValueError("最少字数要求不能为负数")
        return v


class EvaluationRuleCreate(EvaluationRuleBase):
    """创建教学评价规则模型"""

    course_id: Optional[int] = Field(None, description="课程ID")
    teacher_id: Optional[int] = Field(None, description="教师ID")

    @field_validator("course_id", "teacher_id")
    @classmethod
    def validate_target_id(cls, v: Optional[int], info):
        field_name = info.field_name
        if "target_type" in info.data:
            target_type = info.data["target_type"]
            if target_type == "course" and field_name == "course_id" and v is None:
                raise ValueError("评价课程时必须提供课程ID")
            if target_type == "teacher" and field_name == "teacher_id" and v is None:
                raise ValueError("评价教师时必须提供教师ID")
        return v


class EvaluationRuleUpdate(BaseModel):
    """更新教学评价规则模型"""

    name: Optional[str] = Field(None, description="规则名称")
    description: Optional[str] = Field(None, description="规则描述")
    start_date: Optional[datetime] = Field(None, description="开始时间")
    end_date: Optional[datetime] = Field(None, description="结束时间")
    is_required: Optional[bool] = Field(None, description="是否必须评价")
    min_word_count: Optional[int] = Field(None, ge=0, description="最少字数要求")
    allow_anonymous: Optional[bool] = Field(None, description="是否允许匿名")
    is_active: Optional[bool] = Field(None, description="是否启用")

    @field_validator("end_date")
    @classmethod
    def validate_end_date(cls, v: Optional[datetime], info):
        if (
            v is not None
            and "start_date" in info.data
            and info.data["start_date"] is not None
            and v <= info.data["start_date"]
        ):
            raise ValueError("结束时间必须晚于开始时间")
        return v

    @field_validator("min_word_count")
    @classmethod
    def validate_min_word_count(cls, v: Optional[int]):
        if v is not None and v < 0:
            raise ValueError("最少字数要求不能为负数")
        return v


class EvaluationRuleInDB(EvaluationRuleBase):
    """数据库中的教学评价规则模型"""

    id: int = Field(..., description="规则ID")
    course_id: Optional[int] = Field(None, description="课程ID")
    teacher_id: Optional[int] = Field(None, description="教师ID")
    created_at: datetime = Field(..., description="创建时间")
    updated_at: datetime = Field(..., description="更新时间")

    class Config:
        from_attributes = True


class EvaluationRecordBase(BaseModel):
    """教学评价记录基础模型"""

    score: int = Field(..., ge=0, le=100, description="评分")
    comment: Optional[str] = Field(None, description="评价内容")
    is_anonymous: bool = Field(False, description="是否匿名")
    status: str = Field("draft", description="状态")

    @field_validator("score")
    @classmethod
    def validate_score(cls, v: int):
        if v < 0 or v > 100:
            raise ValueError("评分必须在0-100之间")
        return v

    @field_validator("status")
    @classmethod
    def validate_status(cls, v: str):
        valid_status = {"draft", "submitted", "approved", "rejected"}
        if v not in valid_status:
            raise ValueError(f"状态必须是以下之一: {valid_status}")
        return v


class EvaluationRecordCreate(EvaluationRecordBase):
    """创建教学评价记录模型"""

    student_id: int = Field(..., description="学生ID")
    course_id: int = Field(..., description="课程ID")
    teacher_id: int = Field(..., description="教师ID")
    indicator_id: int = Field(..., description="评价指标ID")
    rule_id: int = Field(..., description="评价规则ID")


class EvaluationRecordUpdate(BaseModel):
    """更新教学评价记录模型"""

    score: Optional[int] = Field(None, ge=0, le=100, description="评分")
    comment: Optional[str] = Field(None, description="评价内容")
    status: Optional[str] = Field(None, description="状态")

    @field_validator("score")
    @classmethod
    def validate_score(cls, v: Optional[int]):
        if v is not None and (v < 0 or v > 100):
            raise ValueError("评分必须在0-100之间")
        return v

    @field_validator("status")
    @classmethod
    def validate_status(cls, v: Optional[str]):
        if v is not None:
            valid_status = {"draft", "submitted", "approved", "rejected"}
            if v not in valid_status:
                raise ValueError(f"状态必须是以下之一: {valid_status}")
        return v


class EvaluationRecordInDB(EvaluationRecordBase):
    """数据库中的教学评价记录模型"""

    id: int = Field(..., description="记录ID")
    student_id: int = Field(..., description="学生ID")
    course_id: int = Field(..., description="课程ID")
    teacher_id: int = Field(..., description="教师ID")
    indicator_id: int = Field(..., description="评价指标ID")
    rule_id: int = Field(..., description="评价规则ID")
    submit_date: Optional[datetime] = Field(None, description="提交时间")
    review_date: Optional[datetime] = Field(None, description="审核时间")
    created_at: datetime = Field(..., description="创建时间")
    updated_at: datetime = Field(..., description="更新时间")

    class Config:
        from_attributes = True


class EvaluationStatistics(BaseModel):
    """教学评价统计模型"""

    total_count: int = Field(..., description="评价总数")
    average_score: float = Field(..., description="平均分")
    score_distribution: Dict[str, int] = Field(..., description="分数段分布")
    indicator_scores: Dict[str, float] = Field(..., description="各指标平均分")
    comment_count: int = Field(..., description="评价内容数量")
    anonymous_count: int = Field(..., description="匿名评价数量")


class IndicatorCreate(BaseModel):
    """创建评价指标请求模型"""

    name: str
    code: str
    category: str
    weight: float
    max_score: float
    min_score: float
    description: Optional[str] = None
    parent_id: Optional[int] = None
    level: Optional[int] = 1
    sort: Optional[int] = 0


class IndicatorUpdate(BaseModel):
    """更新评价指标请求模型"""

    name: Optional[str] = None
    code: Optional[str] = None
    category: Optional[str] = None
    weight: Optional[float] = None
    max_score: Optional[float] = None
    min_score: Optional[float] = None
    description: Optional[str] = None
    parent_id: Optional[int] = None
    level: Optional[int] = None
    sort: Optional[int] = None
    is_active: Optional[bool] = None


class IndicatorResponse(BaseModel):
    """评价指标响应模型"""

    id: int
    name: str
    code: str
    category: str
    weight: float
    max_score: float
    min_score: float
    description: Optional[str]
    parent_id: Optional[int]
    level: int
    sort: int
    is_active: bool
    create_time: datetime
    update_time: Optional[datetime]

    class Config:
        from_attributes = True
