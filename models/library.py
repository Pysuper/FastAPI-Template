from datetime import datetime
from enum import Enum as PyEnum
from typing import Optional, List

from sqlalchemy import String, Integer, DateTime, ForeignKey, Text, Boolean, Index
from sqlalchemy.orm import Mapped, mapped_column, relationship

from core.db.core.base import AbstractModel


class ResourceType(str, PyEnum):
    """资源类型"""

    BOOK = "book"  # 图书
    PAPER = "paper"  # 论文
    JOURNAL = "journal"  # 期刊
    THESIS = "thesis"  # 学位论文
    MAGAZINE = "magazine"  # 杂志
    NEWSPAPER = "newspaper"  # 报纸
    CONFERENCE = "conference"  # 会议论文
    PATENT = "patent"  # 专利
    STANDARD = "standard"  # 标准
    REPORT = "report"  # 报告
    MULTIMEDIA = "multimedia"  # 多媒体
    SOFTWARE = "software"  # 软件
    OTHER = "other"  # 其他


class ResourceStatus(str, PyEnum):
    """资源状态"""

    DRAFT = "draft"  # 草稿
    PENDING = "pending"  # 待审核
    APPROVED = "approved"  # 已批准
    REJECTED = "rejected"  # 已拒绝
    PUBLISHED = "published"  # 已发布
    DEPRECATED = "deprecated"  # 已废弃
    ARCHIVED = "archived"  # 已归档


class BorrowingStatus(str, PyEnum):
    """借阅状态"""

    PENDING = "pending"  # 待审核
    APPROVED = "approved"  # 已批准
    REJECTED = "rejected"  # 已拒绝
    BORROWED = "borrowed"  # 已借出
    RENEWED = "renewed"  # 已续借
    RETURNED = "returned"  # 已归还
    OVERDUE = "overdue"  # 已逾期
    LOST = "lost"  # 已遗失
    DAMAGED = "damaged"  # 已损坏


class Resource(AbstractModel):
    """电子资源模型"""

    __tablename__ = "library_resources"

    # 基本信息
    title: Mapped[str] = mapped_column(String(200), nullable=False, index=True, comment="资源标题")
    subtitle: Mapped[Optional[str]] = mapped_column(String(200), comment="副标题")
    type: Mapped[ResourceType] = mapped_column(nullable=False, index=True, comment="资源类型")
    status: Mapped[ResourceStatus] = mapped_column(
        default=ResourceStatus.DRAFT, nullable=False, index=True, comment="资源状态"
    )

    # 作者信息
    author: Mapped[str] = mapped_column(String(100), nullable=False, index=True, comment="作者")
    translator: Mapped[Optional[str]] = mapped_column(String(100), comment="译者")
    editor: Mapped[Optional[str]] = mapped_column(String(100), comment="编辑")

    # 出版信息
    publisher: Mapped[Optional[str]] = mapped_column(String(100), index=True, comment="出版社")
    publish_date: Mapped[Optional[datetime]] = mapped_column(DateTime, comment="出版日期")
    edition: Mapped[Optional[str]] = mapped_column(String(50), comment="版本")
    isbn: Mapped[Optional[str]] = mapped_column(String(20), unique=True, comment="ISBN")
    issn: Mapped[Optional[str]] = mapped_column(String(20), unique=True, comment="ISSN")
    doi: Mapped[Optional[str]] = mapped_column(String(100), unique=True, comment="DOI")

    # 资源信息
    language: Mapped[Optional[str]] = mapped_column(String(50), comment="语言")
    pages: Mapped[Optional[int]] = mapped_column(Integer, comment="页数")
    format: Mapped[Optional[str]] = mapped_column(String(50), comment="格式")
    size: Mapped[Optional[int]] = mapped_column(Integer, comment="文件大小(KB)")
    keywords: Mapped[Optional[str]] = mapped_column(Text, comment="关键词")
    summary: Mapped[Optional[str]] = mapped_column(Text, comment="摘要")

    # 存储信息
    file_path: Mapped[str] = mapped_column(String(500), nullable=False, comment="文件路径")
    cover_url: Mapped[Optional[str]] = mapped_column(String(500), comment="封面URL")
    download_count: Mapped[int] = mapped_column(Integer, default=0, comment="下载次数")
    view_count: Mapped[int] = mapped_column(Integer, default=0, comment="浏览次数")
    citation_count: Mapped[int] = mapped_column(Integer, default=0, comment="引用次数")

    # 借阅信息
    is_borrowable: Mapped[bool] = mapped_column(Boolean, default=True, comment="是否可借")
    max_borrow_days: Mapped[int] = mapped_column(Integer, default=30, comment="最大借阅天数")
    max_renew_times: Mapped[Optional[int]] = mapped_column(Integer, comment="最大续借次数")
    current_borrower_count: Mapped[int] = mapped_column(Integer, default=0, comment="当前借阅人数")

    # 其他信息
    remark: Mapped[Optional[str]] = mapped_column(Text, comment="备注")

    # 外键关联
    category_id: Mapped[int] = mapped_column(
        ForeignKey("resource_categories.id", ondelete="RESTRICT"),
        nullable=False,
        index=True,
        comment="分类ID",
    )
    uploader_id: Mapped[int] = mapped_column(
        ForeignKey("users.id", ondelete="RESTRICT"),
        nullable=False,
        comment="上传者ID",
    )
    approver_id: Mapped[Optional[int]] = mapped_column(
        ForeignKey("users.id", ondelete="SET NULL"),
        comment="审批人ID",
    )

    # 关联关系
    category: Mapped["ResourceCategory"] = relationship(
        "ResourceCategory",
        back_populates="resources",
        lazy="joined",
    )
    uploader: Mapped["User"] = relationship("User", foreign_keys=[uploader_id], lazy="joined")
    approver: Mapped[Optional["User"]] = relationship("User", foreign_keys=[approver_id], lazy="joined")
    borrowing_records: Mapped[List["BorrowingRecord"]] = relationship(
        "BorrowingRecord",
        back_populates="resource",
        cascade="all, delete-orphan",
    )

    # 索引
    __table_args__ = (
        Index(
            "ix_library_resources_type_status",
            "type",
            "status",
        ),
        Index(
            "ix_library_resources_category",
            "category_id",
            "status",
        ),
        Index(
            "ix_library_resources_publish_date",
            "publish_date",
            "type",
        ),
    )

    def __repr__(self) -> str:
        return f"<Resource {self.title}>"


class ResourceCategory(AbstractModel):
    """资源分类模型"""

    __tablename__ = "resource_categories"

    id: Mapped[int] = mapped_column(Integer, primary_key=True, autoincrement=True, comment="分类ID")
    # 基本信息
    name: Mapped[str] = mapped_column(String(100), nullable=False, index=True, comment="分类名称")
    code: Mapped[str] = mapped_column(String(50), unique=True, nullable=False, comment="分类编码")
    description: Mapped[Optional[str]] = mapped_column(Text, comment="分类描述")

    # 层级关系
    parent_id: Mapped[Optional[int]] = mapped_column(
        ForeignKey("resource_categories.id", ondelete="SET NULL"), index=True, comment="父分类ID"
    )
    level: Mapped[int] = mapped_column(Integer, default=1, comment="层级")
    sort: Mapped[int] = mapped_column(Integer, default=0, comment="排序号")

    # 状态信息
    is_active: Mapped[bool] = mapped_column(Boolean, default=True, comment="是否启用")
    remark: Mapped[Optional[str]] = mapped_column(Text, comment="备注")

    # 关联关系
    parent: Mapped[Optional["ResourceCategory"]] = relationship(
        "ResourceCategory",
        remote_side=[id],
        back_populates="children",
        lazy="joined",
    )
    children: Mapped[List["ResourceCategory"]] = relationship(
        "ResourceCategory",
        back_populates="parent",
        cascade="all, delete-orphan",
    )
    resources: Mapped[List["Resource"]] = relationship(
        "Resource",
        back_populates="category",
        cascade="all, delete-orphan",
    )

    # 索引
    __table_args__ = (
        Index(
            "ix_resource_categories_parent_sort",
            "parent_id",
            "sort",
        ),
        Index(
            "ix_resource_categories_level",
            "level",
            "is_active",
        ),
    )

    def __repr__(self) -> str:
        return f"<ResourceCategory {self.code} {self.name}>"


class BorrowingRecord(AbstractModel):
    """借阅记录模型"""

    __tablename__ = "borrowing_records"

    # 基本信息
    status: Mapped[BorrowingStatus] = mapped_column(
        default=BorrowingStatus.PENDING,
        nullable=False,
        index=True,
        comment="借阅状态",
    )

    # 借阅时间
    borrow_date: Mapped[datetime] = mapped_column(DateTime, default=datetime.now, nullable=False, comment="借阅时间")
    due_date: Mapped[datetime] = mapped_column(DateTime, nullable=False, comment="应还时间")
    return_date: Mapped[Optional[datetime]] = mapped_column(comment="实际归还时间")
    renew_count: Mapped[int] = mapped_column(Integer, default=0, comment="续借次数")
    overdue_days: Mapped[int] = mapped_column(Integer, default=0, comment="逾期天数")

    # 处理信息
    process_time: Mapped[Optional[datetime]] = mapped_column(comment="处理时间")
    process_comments: Mapped[Optional[str]] = mapped_column(Text, comment="处理意见")
    fine_amount: Mapped[Optional[float]] = mapped_column(comment="罚款金额")
    fine_status: Mapped[Optional[str]] = mapped_column(String(20), comment="罚款状态")
    remark: Mapped[Optional[str]] = mapped_column(Text, comment="备注")

    # 外键关联
    resource_id: Mapped[int] = mapped_column(
        ForeignKey("library_resources.id", ondelete="RESTRICT"),
        nullable=False,
        index=True,
        comment="资源ID",
    )
    user_id: Mapped[int] = mapped_column(
        ForeignKey("users.id", ondelete="CASCADE"),
        nullable=False,
        index=True,
        comment="借阅人ID",
    )
    approver_id: Mapped[Optional[int]] = mapped_column(
        ForeignKey("users.id", ondelete="SET NULL"),
        comment="审批人ID",
    )

    # 关联关系
    resource: Mapped["Resource"] = relationship(
        "Resource",
        back_populates="borrowing_records",
        lazy="joined",
    )
    user: Mapped["User"] = relationship(
        "User",
        foreign_keys=[user_id],
        lazy="joined",
    )
    approver: Mapped[Optional["User"]] = relationship(
        "User",
        foreign_keys=[approver_id],
        lazy="joined",
    )

    # 索引
    __table_args__ = (
        Index(
            "ix_borrowing_records_user_status",
            "user_id",
            "status",
        ),
        Index(
            "ix_borrowing_records_resource_date",
            "resource_id",
            "borrow_date",
        ),
        Index(
            "ix_borrowing_records_due_date",
            "due_date",
            "status",
        ),
    )

    def __repr__(self) -> str:
        return f"<BorrowingRecord {self.user.name} {self.resource.title} {self.status}>"
