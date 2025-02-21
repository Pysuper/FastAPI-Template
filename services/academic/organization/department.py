from typing import Optional, List

from sqlalchemy.orm import Session

from models.school import Department
from schemas.school import DepartmentCreate, DepartmentUpdate


class DepartmentService:
    def __init__(self, db: Session):
        self.db = db

    def get_department(self, department_id: int) -> Optional[Department]:
        return self.db.query(Department).filter(Department.id == department_id).first()

    def get_department_by_name(self, name: str) -> Optional[Department]:
        return self.db.query(Department).filter(Department.name == name).first()

    def get_departments(self, skip: int = 0, limit: int = 100) -> List[Department]:
        return self.db.query(Department).offset(skip).limit(limit).all()

    def create_department(self, department_in: DepartmentCreate) -> Department:
        department = Department(**department_in.model_dump())
        self.db.add(department)
        self.db.commit()
        self.db.refresh(department)
        return department

    def update_department(self, department: Department, department_in: DepartmentUpdate) -> Department:
        for field, value in department_in.model_dump(exclude_unset=True).items():
            setattr(department, field, value)
        self.db.commit()
        self.db.refresh(department)
        return department

    def delete_department(self, department_id: int) -> None:
        department = self.get_department(department_id)
        self.db.delete(department)
        self.db.commit()

    def count_departments(self) -> int:
        return self.db.query(Department).count()

    def has_related_majors(self, department_id: int) -> bool:
        department = self.get_department(department_id)
        return len(department.majors) > 0 if department else False
