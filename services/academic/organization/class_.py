# -*- coding:utf-8 -*-
"""
@Project ：Speedy 
@File    ：class_.py
@Author  ：PySuper
@Date    ：2024/12/27 09:52 
@Desc    ：Speedy class_.py
"""

from typing import List, Dict, Optional

class ClassService:
    def __init__(self):
        self.classes: Dict[int, Dict] = {}
        self.next_id: int = 1

    def create_class(self, name: str, teacher: str) -> int:
        """创建班级"""
        class_id = self.next_id
        self.classes[class_id] = {
            "name": name,
            "teacher": teacher,
            "students": [],
            "schedule": {}
        }
        self.next_id += 1
        return class_id

    def update_class(self, class_id: int, name: Optional[str] = None, teacher: Optional[str] = None) -> bool:
        """更新班级信息"""
        if class_id not in self.classes:
            return False
        if name:
            self.classes[class_id]["name"] = name
        if teacher:
            self.classes[class_id]["teacher"] = teacher
        return True

    def delete_class(self, class_id: int) -> bool:
        """删除班级"""
        if class_id in self.classes:
            del self.classes[class_id]
            return True
        return False

    def get_class(self, class_id: int) -> Optional[Dict]:
        """获取班级详情"""
        return self.classes.get(class_id)

    def list_classes(self) -> List[Dict]:
        """列出所有班级"""
        return list(self.classes.values())

    def add_student(self, class_id: int, student_id: int) -> bool:
        """添加学生到班级"""
        if class_id not in self.classes:
            return False
        self.classes[class_id]["students"].append(student_id)
        return True

    def remove_student(self, class_id: int, student_id: int) -> bool:
        """从班级中删除学生"""
        if class_id not in self.classes or student_id not in self.classes[class_id]["students"]:
            return False
        self.classes[class_id]["students"].remove(student_id)
        return True

    def get_students(self, class_id: int) -> Optional[List[int]]:
        """获取班级学生列表"""
        if class_id not in self.classes:
            return None
        return self.classes[class_id]["students"]
