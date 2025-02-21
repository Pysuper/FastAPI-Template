# from datetime import date
# from typing import Optional
#
# from pydantic import BaseModel, EmailStr, Field
#
#
# # 基础模型
# class BaseSchema(BaseModel):
#     class Config:
#         from_attributes = True
#
#
# # Department schemas
# class DepartmentBase(BaseSchema):
#     name: str = Field(..., description="院系名称")
#     code: str = Field(..., description="院系代码")
#     description: Optional[str] = Field(None, description="院系描述")
#     is_active: bool = Field(True, description="是否激活")
#
#
# class DepartmentCreate(DepartmentBase):
#     pass
#
#
# class DepartmentUpdate(BaseSchema):
#     name: Optional[str] = None
#     description: Optional[str] = None
#     is_active: Optional[bool] = None
#
#
# class DepartmentInDB(DepartmentBase):
#     id: int
#     created_at: date
#     updated_at: date
#
#
# # Major schemas
# class MajorBase(BaseSchema):
#     name: str = Field(..., description="专业名称")
#     code: str = Field(..., description="专业代码")
#     description: Optional[str] = Field(None, description="专业描述")
#     duration: int = Field(4, description="学制年限")
#     is_active: bool = Field(True, description="是否激活")
#     department_id: int = Field(..., description="所属院系ID")
#
#
# class MajorCreate(MajorBase):
#     pass
#
#
# class MajorUpdate(BaseSchema):
#     name: Optional[str] = None
#     description: Optional[str] = None
#     duration: Optional[int] = None
#     is_active: Optional[bool] = None
#
#
# class MajorInDB(MajorBase):
#     id: int
#     created_at: date
#     updated_at: date
#
#
# # Class schemas
# class ClassBase(BaseSchema):
#     name: str = Field(..., description="班级名称")
#     code: str = Field(..., description="班级代码")
#     grade: int = Field(..., description="年级")
#     capacity: int = Field(50, description="班级容量")
#     is_active: bool = Field(True, description="是否激活")
#     major_id: int = Field(..., description="所属专业ID")
#     teacher_id: Optional[int] = Field(None, description="班主任ID")
#
#
# class ClassCreate(ClassBase):
#     pass
#
#
# class ClassUpdate(BaseSchema):
#     name: Optional[str] = None
#     capacity: Optional[int] = None
#     is_active: Optional[bool] = None
#     teacher_id: Optional[int] = None
#
#
# class ClassInDB(ClassBase):
#     id: int
#     created_at: date
#     updated_at: date
#
#
# # Teacher schemas
# class TeacherBase(BaseSchema):
#     name: str = Field(..., description="教师姓名")
#     code: str = Field(..., description="教师工号")
#     title: Optional[str] = Field(None, description="职称")
#     email: Optional[EmailStr] = Field(None, description="邮箱")
#     phone: Optional[str] = Field(None, description="电话")
#     gender: str = Field(..., description="性别")
#     birth_date: Optional[date] = Field(None, description="出生日期")
#     is_active: bool = Field(True, description="是否在职")
#     department_id: int = Field(..., description="所属院系ID")
#
#
# class TeacherCreate(TeacherBase):
#     pass
#
#
# class TeacherUpdate(BaseSchema):
#     name: Optional[str] = None
#     title: Optional[str] = None
#     email: Optional[EmailStr] = None
#     phone: Optional[str] = None
#     is_active: Optional[bool] = None
#
#
# class TeacherInDB(TeacherBase):
#     id: int
#     created_at: date
#     updated_at: date
#
#
# # Student schemas
# class StudentBase(BaseSchema):
#     name: str = Field(..., description="学生姓名")
#     code: str = Field(..., description="学号")
#     gender: str = Field(..., description="性别")
#     birth_date: Optional[date] = Field(None, description="出生日期")
#     email: Optional[EmailStr] = Field(None, description="邮箱")
#     phone: Optional[str] = Field(None, description="电话")
#     admission_date: date = Field(..., description="入学日期")
#     graduation_date: Optional[date] = Field(None, description="毕业日期")
#     is_active: bool = Field(True, description="是否在读")
#     class_id: int = Field(..., description="所属班级ID")
#
#
# class StudentCreate(StudentBase):
#     pass
#
#
# class StudentUpdate(BaseSchema):
#     name: Optional[str] = None
#     email: Optional[EmailStr] = None
#     phone: Optional[str] = None
#     graduation_date: Optional[date] = None
#     is_active: Optional[bool] = None
#
#
# class StudentInDB(StudentBase):
#     id: int
#     created_at: date
#     updated_at: date
#
#
# # Course schemas
# class CourseBase(BaseSchema):
#     name: str = Field(..., description="课程名称")
#     code: str = Field(..., description="课程代码")
#     description: Optional[str] = Field(None, description="课程描述")
#     credits: int = Field(..., description="学分")
#     hours: int = Field(..., description="课时")
#     semester: str = Field(..., description="学期")
#     max_students: int = Field(100, description="最大学生数")
#     is_active: bool = Field(True, description="是否激活")
#     major_id: int = Field(..., description="所属专业ID")
#     teacher_id: int = Field(..., description="授课教师ID")
#
#
# class CourseCreate(CourseBase):
#     pass
#
#
# class CourseUpdate(BaseSchema):
#     name: Optional[str] = None
#     description: Optional[str] = None
#     max_students: Optional[int] = None
#     is_active: Optional[bool] = None
#     teacher_id: Optional[int] = None
#
#
# class CourseInDB(CourseBase):
#     id: int
#     created_at: date
#     updated_at: date
#
#
# # CourseEnrollment schemas
# class CourseEnrollmentBase(BaseSchema):
#     student_id: int = Field(..., description="学生ID")
#     course_id: int = Field(..., description="课程ID")
#     enrollment_date: date = Field(..., description="选课日期")
#     grade: Optional[int] = Field(None, description="成绩")
#     status: str = Field("enrolled", description="状态")
#
#
# class CourseEnrollmentCreate(CourseEnrollmentBase):
#     pass
#
#
# class CourseEnrollmentUpdate(BaseSchema):
#     grade: Optional[int] = None
#     status: Optional[str] = None
#
#
# class CourseEnrollmentInDB(CourseEnrollmentBase):
#     id: int
#     created_at: date
#     updated_at: date
#
#
# class CourseEnrollmentResponse:
#     pass
#
#
# class CourseEnrollmentStatusUpdate:
#     pass
#
#
# class CourseEnrollmentScoreUpdate:
#     pass
#
#
# class CourseEnrollmentGradeUpdate:
#     pass
