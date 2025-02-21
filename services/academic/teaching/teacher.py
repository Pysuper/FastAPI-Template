from typing import List, Optional

from models import Department, Teacher
from sqlalchemy.orm import Session

from schemas.teacher import TeacherCreate, TeacherUpdate


class TeacherService:
    # def __init__(self, db: Session):
    #     self.db = db

    def get_teacher(self, db: Session, teacher_id: int) -> Optional[Teacher]:
        return db.query(Teacher).filter(Teacher.id == teacher_id).first()

    def get_teacher_by_number(self, db: Session, code: str) -> Optional[Teacher]:
        return db.query(Teacher).filter(Teacher.code == code).first()

    def get_teachers(
        self, db: Session, skip: int = 0, limit: int = 100, department_id: Optional[int] = None
    ) -> List[Teacher]:
        query = db.query(Teacher)
        if department_id:
            query = query.filter(Teacher.department_id == department_id)
        return query.offset(skip).limit(limit).all()

    def create_teacher(self, db: Session, teacher_in: TeacherCreate) -> Teacher:
        teacher = Teacher(**teacher_in.model_dump())
        db.add(teacher)
        db.commit()
        db.refresh(teacher)
        return teacher

    def update_teacher(self, db: Session, teacher: Teacher, teacher_in: TeacherUpdate) -> Teacher:
        for field, value in teacher_in.model_dump(exclude_unset=True).items():
            setattr(teacher, field, value)
        db.commit()
        db.refresh(teacher)
        return teacher

    def delete_teacher(self, db: Session, teacher_id: int) -> None:
        teacher = self.get_teacher(teacher_id)
        db.delete(teacher)
        db.commit()

    def count_teachers(self, db: Session, department_id: Optional[int] = None) -> int:
        query = db.query(Teacher)
        if department_id:
            query = query.filter(Teacher.department_id == department_id)
        return query.count()

    def department_exists(self, db: Session, department_id: int) -> bool:
        return db.query(Department).filter(Department.id == department_id).first() is not None

    def has_related_courses(self, db: Session, teacher_id: int) -> bool:
        teacher = self.get_teacher(db, teacher_id)
        return len(teacher.courses) > 0 if teacher else False
