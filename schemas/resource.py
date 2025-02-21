from datetime import datetime
from typing import Optional

from pydantic import BaseModel, Field, validator


class ResourceBase(BaseModel):
    """资源基础模型"""

    title: str = Field(..., description="资源标题")
    type: str = Field(..., description="资源类型")
    author: str = Field(..., description="作者")
    description: Optional[str] = Field(None, description="资源描述")
    category_id: int = Field(..., description="分类ID")


class ResourceCreate(ResourceBase):
    """资源创建模型"""

    publisher: Optional[str] = Field(None, description="出版社")
    publish_date: Optional[datetime] = Field(None, description="出版日期")
    isbn: Optional[str] = Field(None, description="ISBN")
    file_path: str = Field(..., description="文件路径")

    @validator("isbn")
    def validate_isbn(cls, v):
        if v and not v.replace("-", "").isdigit():
            raise ValueError("ISBN格式不正确")
        return v

    @validator("file_path")
    def validate_file_path(cls, v):
        if not v:
            raise ValueError("文件路径不能为空")
        return v


class ResourceUpdate(BaseModel):
    """资源更新模型"""

    title: Optional[str] = Field(None, description="资源标题")
    type: Optional[str] = Field(None, description="资源类型")
    author: Optional[str] = Field(None, description="作者")
    publisher: Optional[str] = Field(None, description="出版社")
    publish_date: Optional[datetime] = Field(None, description="出版日期")
    description: Optional[str] = Field(None, description="资源描述")
    category_id: Optional[int] = Field(None, description="分类ID")
    isbn: Optional[str] = Field(None, description="ISBN")
    file_path: Optional[str] = Field(None, description="文件路径")

    @validator("isbn")
    def validate_isbn(cls, v):
        if v and not v.replace("-", "").isdigit():
            raise ValueError("ISBN格式不正确")
        return v

    @validator("file_path")
    def validate_file_path(cls, v):
        if v and not v:
            raise ValueError("文件路径不能为空")
        return v
