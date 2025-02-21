# -*- coding:utf-8 -*-
"""
@Project ：Speedy 
@File    ：exam_management.py
@Author  ：PySuper
@Date    ：2024-12-30 20:50
@Desc    ：Speedy exam_management
"""

from typing import List, Dict, Optional


class ExamService:
    def __init__(self):
        self.exams: Dict[int, Dict] = {}
        self.next_id: int = 1

    def create_exam(self, name: str, date: str, location: str) -> int:
        """创建考试"""
        exam_id = self.next_id
        self.exams[exam_id] = {"name": name, "date": date, "location": location, "results": {}}
        self.next_id += 1
        return exam_id

    def update_exam(
        self, exam_id: int, name: Optional[str] = None, date: Optional[str] = None, location: Optional[str] = None
    ) -> bool:
        """更新考试信息"""
        if exam_id not in self.exams:
            return False
        if name:
            self.exams[exam_id]["name"] = name
        if date:
            self.exams[exam_id]["date"] = date
        if location:
            self.exams[exam_id]["location"] = location
        return True

    def delete_exam(self, exam_id: int) -> bool:
        """删除考试"""
        if exam_id in self.exams:
            del self.exams[exam_id]
            return True
        return False

    def get_exam(self, exam_id: int) -> Optional[Dict]:
        """获取考试详情"""
        return self.exams.get(exam_id)

    def list_exams(self) -> List[Dict]:
        """列出所有考试"""
        return list(self.exams.values())

    def add_result(self, exam_id: int, student_id: int, score: float) -> bool:
        """录入考试成绩"""
        if exam_id not in self.exams:
            return False
        self.exams[exam_id]["results"][student_id] = score
        return True

    def get_results(self, exam_id: int) -> Optional[Dict[int, float]]:
        """查询考试成绩"""
        if exam_id not in self.exams:
            return None
        return self.exams[exam_id]["results"]
