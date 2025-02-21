from typing import List, Optional

from sqlalchemy.orm import Session

from models.school import Class, Major
from schemas.class_ import ClassCreate, ClassUpdate


class ClassService:
    def __init__(self, db: Session):
        self.db = db

    def get_class(self, class_id: int) -> Optional[Class]:
        return self.db.query(Class).filter(Class.id == class_id).first()

    def get_class_by_name(self, name: str, major_id: int) -> Optional[Class]:
        return self.db.query(Class).filter(Class.name == name, Class.major_id == major_id).first()

    def get_classes(self, skip: int = 0, limit: int = 100, major_id: Optional[int] = None) -> List[Class]:
        query = self.db.query(Class)
        if major_id:
            query = query.filter(Class.major_id == major_id)
        return query.offset(skip).limit(limit).all()

    def create_class(self, class_in: ClassCreate) -> Class:
        class_ = Class(**class_in.model_dump())
        self.db.add(class_)
        self.db.commit()
        self.db.refresh(class_)
        return class_

    def update_class(self, class_: Class, class_in: ClassUpdate) -> Class:
        for field, value in class_in.model_dump(exclude_unset=True).items():
            setattr(class_, field, value)
        self.db.commit()
        self.db.refresh(class_)
        return class_

    def delete_class(self, class_id: int) -> None:
        class_ = self.get_class(class_id)
        self.db.delete(class_)
        self.db.commit()

    def count_classes(self, major_id: Optional[int] = None) -> int:
        query = self.db.query(Class)
        if major_id:
            query = query.filter(Class.major_id == major_id)
        return query.count()

    def major_exists(self, major_id: int) -> bool:
        return self.db.query(Major).filter(Major.id == major_id).first() is not None

    def has_related_students(self, class_id: int) -> bool:
        class_ = self.get_class(class_id)
        return len(class_.students) > 0 if class_ else False
