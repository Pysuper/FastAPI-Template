from typing import List, Optional

from sqlalchemy.orm import Session

from models.school import Course, Department, Teacher
from schemas.course import CourseCreate, CourseUpdate


class CourseService:
    def __init__(self, db: Session):
        self.db = db

    def get_course(self, course_id: int) -> Optional[Course]:
        return self.db.query(Course).filter(Course.id == course_id).first()

    def get_course_by_code(self, code: str) -> Optional[Course]:
        return self.db.query(Course).filter(Course.code == code).first()

    def get_courses(
        self, skip: int = 0, limit: int = 100, department_id: int = None, teacher_id: int = None
    ) -> List[Course]:
        query = self.db.query(Course)
        if department_id:
            query = query.filter(Course.department_id == department_id)
        if teacher_id:
            query = query.filter(Course.teacher_id == teacher_id)
        return query.offset(skip).limit(limit).all()

    def create_course(self, course_in: CourseCreate) -> Course:
        course = Course(**course_in.model_dump())
        self.db.add(course)
        self.db.commit()
        self.db.refresh(course)
        return course

    def update_course(self, course: Course, course_in: CourseUpdate) -> Course:
        for field, value in course_in.model_dump(exclude_unset=True).items():
            setattr(course, field, value)
        self.db.commit()
        self.db.refresh(course)
        return course

    def delete_course(self, course_id: int) -> None:
        self.db.query(Course).filter(Course.id == course_id).delete()
        self.db.commit()

    def count_courses(self, department_id: int = None, teacher_id: int = None) -> int:
        query = self.db.query(Course)
        if department_id:
            query = query.filter(Course.department_id == department_id)
        if teacher_id:
            query = query.filter(Course.teacher_id == teacher_id)
        return query.count()

    def department_exists(self, department_id: int) -> bool:
        return self.db.query(Department).filter(Department.id == department_id).first() is not None

    def teacher_exists(self, teacher_id: int) -> bool:
        return self.db.query(Teacher).filter(Teacher.id == teacher_id).first() is not None

    def has_related_records(self, course_id: int) -> bool:
        return False
