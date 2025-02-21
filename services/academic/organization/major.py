from typing import List, Optional

from sqlalchemy.orm import Session

from models.department import Major, Department
from schemas.major import MajorCreate, MajorUpdate


class MajorService:
    def __init__(self, db: Session):
        self.db = db

    def get_major(self, major_id: int) -> Optional[Major]:
        return self.db.query(Major).filter(Major.id == major_id).first()

    def get_major_by_name(self, name: str, department_id: int) -> Optional[Major]:
        return self.db.query(Major).filter(Major.name == name, Major.department_id == department_id).first()

    def get_majors(self, skip: int = 0, limit: int = 100, department_id: Optional[int] = None) -> List[Major]:
        query = self.db.query(Major)
        if department_id:
            query = query.filter(Major.department_id == department_id)
        return query.offset(skip).limit(limit).all()

    def create_major(self, major_in: MajorCreate) -> Major:
        major = Major(**major_in.model_dump())
        self.db.add(major)
        self.db.commit()
        self.db.refresh(major)
        return major

    def update_major(self, major: Major, major_in: MajorUpdate) -> Major:
        for field, value in major_in.model_dump(exclude_unset=True).items():
            setattr(major, field, value)
        self.db.commit()
        self.db.refresh(major)
        return major

    def delete_major(self, major_id: int) -> None:
        major = self.get_major(major_id)
        self.db.delete(major)
        self.db.commit()

    def count_majors(self, department_id: Optional[int] = None) -> int:
        query = self.db.query(Major)
        if department_id:
            query = query.filter(Major.department_id == department_id)
        return query.count()

    def department_exists(self, department_id: int) -> bool:
        return self.db.query(Department).filter(Department.id == department_id).first() is not None

    def has_related_classes(self, major_id: int) -> bool:
        major = self.get_major(major_id)
        return len(major.classes) > 0 if major else False
