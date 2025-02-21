from datetime import datetime
from enum import Enum as PyEnum
from typing import List, Optional

from sqlalchemy import BigInteger, Boolean, Column, DateTime, Float, ForeignKey, Index, Integer, JSON, String, Text
from sqlalchemy.orm import Mapped, mapped_column, relationship

from core.db.core.base import AbstractModel


class QuestionType(str, PyEnum):
    """试题类型"""

    SINGLE_CHOICE = "single_choice"  # 单选题
    MULTIPLE_CHOICE = "multiple_choice"  # 多选题
    TRUE_FALSE = "true_false"  # 判断题
    FILL_BLANK = "fill_blank"  # 填空题
    SHORT_ANSWER = "short_answer"  # 简答题
    ESSAY = "essay"  # 论述题
    PROGRAMMING = "programming"  # 编程题
    CALCULATION = "calculation"  # 计算题


class ExamStatus(str, PyEnum):
    """考试状态"""

    DRAFT = "draft"  # 草稿
    PENDING = "pending"  # 待审核
    APPROVED = "approved"  # 已批准
    REJECTED = "rejected"  # 已拒绝
    PUBLISHED = "published"  # 已发布
    IN_PROGRESS = "in_progress"  # 进行中
    ENDED = "ended"  # 已结束
    GRADING = "grading"  # 批改中
    COMPLETED = "completed"  # 已完成
    ARCHIVED = "archived"  # 已归档


class ExamRecordStatus(str, PyEnum):
    """考试记录状态"""

    NOT_STARTED = "not_started"  # 未开始
    IN_PROGRESS = "in_progress"  # 进行中
    SUBMITTED = "submitted"  # 已提交
    GRADING = "grading"  # 批改中
    COMPLETED = "completed"  # 已完成
    CANCELLED = "cancelled"  # 已取消
    TIMEOUT = "timeout"  # 已超时
    CHEATING = "cheating"  # 作弊


class Exam(AbstractModel):
    """考试模型"""

    __tablename__ = "exams"

    # 基本信息
    title: Mapped[str] = mapped_column(String(200), nullable=False, index=True, comment="考试标题")
    description: Mapped[Optional[str]] = mapped_column(Text, comment="考试描述")
    status: Mapped[ExamStatus] = mapped_column(default=ExamStatus.DRAFT, nullable=False, index=True, comment="考试状态")

    # 时间信息
    start_time: Mapped[datetime] = mapped_column(DateTime, nullable=False, comment="开始时间")
    end_time: Mapped[datetime] = mapped_column(DateTime, nullable=False, comment="结束时间")
    duration: Mapped[int] = mapped_column(Integer, nullable=False, comment="考试时长(分钟)")
    extra_time: Mapped[Optional[int]] = mapped_column(Integer, comment="额外时长(分钟)")
    publish_time: Mapped[Optional[datetime]] = mapped_column(comment="发布时间")
    archive_time: Mapped[Optional[datetime]] = mapped_column(comment="归档时间")

    # 分数信息
    total_score: Mapped[float] = mapped_column(Float, nullable=False, comment="总分")
    pass_score: Mapped[float] = mapped_column(Float, nullable=False, comment="及格分数")
    actual_avg_score: Mapped[Optional[float]] = mapped_column(comment="实际平均分")
    highest_score: Mapped[Optional[float]] = mapped_column(comment="最高分")
    lowest_score: Mapped[Optional[float]] = mapped_column(comment="最低分")

    # 考试要求
    allow_retake: Mapped[bool] = mapped_column(Boolean, default=False, comment="是否允许重考")
    max_retakes: Mapped[Optional[int]] = mapped_column(Integer, comment="最大重考次数")
    shuffle_questions: Mapped[bool] = mapped_column(Boolean, default=False, comment="是否打乱题目")
    show_answer: Mapped[bool] = mapped_column(Boolean, default=False, comment="是否显示答案")
    show_score: Mapped[bool] = mapped_column(Boolean, default=True, comment="是否显示分数")
    need_approval: Mapped[bool] = mapped_column(Boolean, default=False, comment="是否需要审批")
    auto_submit: Mapped[bool] = mapped_column(Boolean, default=True, comment="是否自动提交")

    # 监考设置
    require_camera: Mapped[bool] = mapped_column(Boolean, default=False, comment="是否要求摄像头")
    require_microphone: Mapped[bool] = mapped_column(Boolean, default=False, comment="是否要求麦克风")
    allow_calculator: Mapped[bool] = mapped_column(Boolean, default=False, comment="是否允许计算器")
    prevent_copy: Mapped[bool] = mapped_column(Boolean, default=True, comment="是否防止复制")
    prevent_switch: Mapped[bool] = mapped_column(Boolean, default=True, comment="是否防止切换")
    ip_restriction: Mapped[Optional[str]] = mapped_column(Text, comment="IP限制")

    # 其他信息
    instructions: Mapped[Optional[str]] = mapped_column(Text, comment="考试说明")
    attachments: Mapped[Optional[str]] = mapped_column(Text, comment="附件")
    remark: Mapped[Optional[str]] = mapped_column(Text, comment="备注")

    # 外键关联
    course_id: Mapped[int] = mapped_column(
        ForeignKey("courses.id", ondelete="CASCADE"),
        nullable=False,
        index=True,
        comment="课程ID",
    )
    creator_id: Mapped[int] = mapped_column(
        ForeignKey("teachers.id", ondelete="RESTRICT"),
        nullable=False,
        comment="创建人ID",
    )
    approver_id: Mapped[Optional[int]] = mapped_column(
        ForeignKey("teachers.id", ondelete="SET NULL"),
        comment="审批人ID",
    )

    # 关联关系
    course: Mapped["Course"] = relationship(
        "Course",
        back_populates="exams",
        lazy="joined",
    )
    creator: Mapped["Teacher"] = relationship("Teacher", foreign_keys=[creator_id], lazy="joined")
    approver: Mapped[Optional["Teacher"]] = relationship(
        "Teacher",
        foreign_keys=[approver_id],
        lazy="joined",
    )
    questions: Mapped[List["Question"]] = relationship(
        "Question",
        back_populates="exam",
        cascade="all, delete-orphan",
    )
    exam_records: Mapped[List["ExamRecord"]] = relationship(
        "ExamRecord", back_populates="exam", cascade="all, delete-orphan"
    )

    # 索引
    __table_args__ = (
        Index(
            "ix_exams_course_status",
            "course_id",
            "status",
        ),
        Index(
            "ix_exams_time_range",
            "start_time",
            "end_time",
        ),
    )

    def __repr__(self) -> str:
        return f"<Exam {self.title}>"


class Question(AbstractModel):
    """试题模型"""

    __tablename__ = "questions"

    # 基本信息
    type: Mapped[QuestionType] = mapped_column(nullable=False, index=True, comment="题目类型")
    content: Mapped[str] = mapped_column(Text, nullable=False, comment="题目内容")
    answer: Mapped[str] = mapped_column(Text, nullable=False, comment="标准答案")
    analysis: Mapped[Optional[str]] = mapped_column(Text, comment="题目解析")
    options: Mapped[Optional[dict]] = mapped_column(JSON, comment="选项(选择题)")
    attachments: Mapped[Optional[str]] = mapped_column(Text, comment="附件")

    # 分数信息
    score: Mapped[float] = mapped_column(Float, nullable=False, comment="分值")
    partial_score: Mapped[bool] = mapped_column(Boolean, default=False, comment="是否允许部分分")
    min_score: Mapped[Optional[float]] = mapped_column(Float, comment="最低得分")
    scoring_criteria: Mapped[Optional[str]] = mapped_column(Text, comment="评分标准")

    # 其他信息
    difficulty: Mapped[Optional[int]] = mapped_column(Integer, comment="难度(1-5)")
    estimated_time: Mapped[Optional[int]] = mapped_column(Integer, comment="预计用时(分钟)")
    knowledge_points: Mapped[Optional[str]] = mapped_column(Text, comment="知识点")
    remark: Mapped[Optional[str]] = mapped_column(Text, comment="备注")

    # 外键关联
    exam_id: Mapped[int] = mapped_column(
        ForeignKey("exams.id", ondelete="CASCADE"),
        nullable=False,
        index=True,
        comment="所属考试ID",
    )
    creator_id: Mapped[int] = mapped_column(
        ForeignKey("teachers.id", ondelete="RESTRICT"),
        nullable=False,
        comment="创建人ID",
    )

    # 关联关系
    exam: Mapped["Exam"] = relationship("Exam", back_populates="questions", lazy="joined")
    creator: Mapped["Teacher"] = relationship("Teacher", lazy="joined")
    student_answers: Mapped[List["StudentAnswer"]] = relationship(
        "StudentAnswer",
        back_populates="question",
        cascade="all, delete-orphan",
    )

    # 索引
    __table_args__ = (
        Index(
            "ix_questions_exam_type",
            "exam_id",
            "type",
        ),
        Index(
            "ix_questions_difficulty",
            "difficulty",
            "exam_id",
        ),
    )

    def __repr__(self) -> str:
        return f"<Question {self.type} {self.score}分>"


class ExamRecord(AbstractModel):
    """考试记录模型"""

    __tablename__ = "exam_records"

    # 基本信息
    status: Mapped[ExamRecordStatus] = mapped_column(
        default=ExamRecordStatus.NOT_STARTED,
        nullable=False,
        index=True,
        comment="状态",
    )
    ip_address: Mapped[Optional[str]] = mapped_column(String(50), comment="IP地址")
    user_agent: Mapped[Optional[str]] = mapped_column(String(200), comment="浏览器信息")

    # 时间信息
    start_time: Mapped[datetime] = mapped_column(DateTime, nullable=False, comment="开始答题时间")
    submit_time: Mapped[Optional[datetime]] = mapped_column(comment="提交时间")
    grade_time: Mapped[Optional[datetime]] = mapped_column(comment="批改时间")

    # 分数信息
    total_score: Mapped[Optional[float]] = mapped_column(Float, comment="总得分")
    objective_score: Mapped[Optional[float]] = mapped_column(Float, comment="客观题得分")
    subjective_score: Mapped[Optional[float]] = mapped_column(Float, comment="主观题得分")
    pass_status: Mapped[Optional[bool]] = mapped_column(Boolean, comment="是否及格")

    # 其他信息
    retake_count: Mapped[int] = mapped_column(Integer, default=0, comment="重考次数")
    violation_count: Mapped[int] = mapped_column(Integer, default=0, comment="违规次数")
    violation_details: Mapped[Optional[str]] = mapped_column(Text, comment="违规详情")
    remark: Mapped[Optional[str]] = mapped_column(Text, comment="备注")

    # 外键关联
    exam_id: Mapped[int] = mapped_column(
        ForeignKey("exams.id", ondelete="CASCADE"),
        nullable=False,
        index=True,
        comment="考试ID",
    )
    student_id: Mapped[int] = mapped_column(
        ForeignKey("students.id", ondelete="CASCADE"),
        nullable=False,
        index=True,
        comment="学生ID",
    )
    grader_id: Mapped[Optional[int]] = mapped_column(
        ForeignKey("teachers.id", ondelete="SET NULL"),
        comment="批改人ID",
    )

    # 关联关系
    exam: Mapped["Exam"] = relationship("Exam", back_populates="exam_records", lazy="joined")
    student: Mapped["Student"] = relationship("Student", lazy="joined")
    grader: Mapped[Optional["Teacher"]] = relationship("Teacher", lazy="joined")
    student_answers: Mapped[List["StudentAnswer"]] = relationship(
        "StudentAnswer",
        back_populates="exam_record",
        cascade="all, delete-orphan",
    )

    # 索引
    __table_args__ = (
        Index(
            "ix_exam_records_exam_student",
            "exam_id",
            "student_id",
        ),
        Index(
            "ix_exam_records_status_exam",
            "status",
            "exam_id",
        ),
        Index(
            "ix_exam_records_score",
            "total_score",
            "exam_id",
        ),
    )

    def __repr__(self) -> str:
        return f"<ExamRecord {self.student.name} {self.status}>"


class StudentAnswer(AbstractModel):
    """学生答案模型"""

    __tablename__ = "student_answers"

    # 基本信息
    answer_content: Mapped[str] = mapped_column(Text, nullable=False, comment="答案内容")
    is_correct: Mapped[Optional[bool]] = mapped_column(Boolean, comment="是否正确")
    score: Mapped[Optional[float]] = mapped_column(Float, comment="得分")
    attachments: Mapped[Optional[str]] = mapped_column(Text, comment="附件")

    # 批改信息
    grade_time: Mapped[Optional[datetime]] = mapped_column(comment="批改时间")
    grade_comment: Mapped[Optional[str]] = mapped_column(Text, comment="评语")
    auto_graded: Mapped[bool] = mapped_column(Boolean, default=False, comment="是否自动批改")

    # 答题信息
    answer_time: Mapped[datetime] = mapped_column(DateTime, default=datetime.now, nullable=False, comment="答题时间")
    time_spent: Mapped[Optional[int]] = mapped_column(Integer, comment="用时(秒)")
    modified_count: Mapped[int] = mapped_column(Integer, default=0, comment="修改次数")
    remark: Mapped[Optional[str]] = mapped_column(Text, comment="备注")

    # 外键关联
    exam_record_id: Mapped[int] = mapped_column(
        ForeignKey("exam_records.id", ondelete="CASCADE"),
        nullable=False,
        index=True,
        comment="考试记录ID",
    )
    question_id: Mapped[int] = mapped_column(
        ForeignKey("questions.id", ondelete="CASCADE"),
        nullable=False,
        index=True,
        comment="试题ID",
    )
    grader_id: Mapped[Optional[int]] = mapped_column(
        ForeignKey("teachers.id", ondelete="SET NULL"),
        comment="批改人ID",
    )

    # 关联关系
    exam_record: Mapped["ExamRecord"] = relationship("ExamRecord", back_populates="student_answers", lazy="joined")
    question: Mapped["Question"] = relationship("Question", back_populates="student_answers", lazy="joined")
    grader: Mapped[Optional["Teacher"]] = relationship("Teacher", lazy="joined")

    # 索引
    __table_args__ = (
        Index(
            "ix_student_answers_record_question",
            "exam_record_id",
            "question_id",
            unique=True,
        ),
        Index(
            "ix_student_answers_score",
            "score",
            "exam_record_id",
        ),
    )

    def __repr__(self) -> str:
        return f"<StudentAnswer {self.question.type} {self.score}分>"
