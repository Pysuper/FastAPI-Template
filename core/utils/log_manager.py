import csv
import io
import json
import logging
from datetime import datetime, timedelta
from typing import Dict, List, Optional, Union

import pandas as pd
from sqlalchemy import func
from sqlalchemy.orm import Session

from models.system import SystemLog

logger = logging.getLogger(__name__)

class LogManager:
    """日志管理器"""

    def __init__(self, db: Session):
        self.db = db

    def export_logs(
        self,
        format: str,
        start_time: Optional[datetime] = None,
        end_time: Optional[datetime] = None,
        level: Optional[str] = None,
        module: Optional[str] = None
    ) -> Union[str, bytes]:
        """
        导出日志
        :param format: 导出格式（csv, json, excel）
        :param start_time: 开始时间
        :param end_time: 结束时间
        :param level: 日志级别
        :param module: 模块名称
        :return: 导出的数据
        """
        # 构建查询
        query = self.db.query(SystemLog)
        
        # 应用过滤条件
        if start_time:
            query = query.filter(SystemLog.created_at >= start_time)
        if end_time:
            query = query.filter(SystemLog.created_at <= end_time)
        if level:
            query = query.filter(SystemLog.level == level)
        if module:
            query = query.filter(SystemLog.module == module)
            
        # 获取日志数据
        logs = query.all()
        
        # 转换为字典列表
        log_data = []
        for log in logs:
            log_dict = {
                'id': log.id,
                'level': log.level,
                'module': log.module,
                'message': log.message,
                'trace': log.trace,
                'created_at': log.created_at.isoformat(),
                'updated_at': log.updated_at.isoformat()
            }
            log_data.append(log_dict)
            
        # 根据格式导出
        if format.lower() == 'csv':
            output = io.StringIO()
            if log_data:
                writer = csv.DictWriter(output, fieldnames=log_data[0].keys())
                writer.writeheader()
                writer.writerows(log_data)
            return output.getvalue()
            
        elif format.lower() == 'json':
            return json.dumps(log_data, ensure_ascii=False)
            
        elif format.lower() == 'excel':
            output = io.BytesIO()
            df = pd.DataFrame(log_data)
            df.to_excel(output, index=False)
            return output.getvalue()
            
        else:
            raise ValueError(f"Unsupported format: {format}")

    def analyze_logs(
        self,
        start_time: Optional[datetime] = None,
        end_time: Optional[datetime] = None,
        group_by: Optional[List[str]] = None,
        metrics: Optional[List[str]] = None
    ) -> Dict:
        """
        分析日志
        :param start_time: 开始时间
        :param end_time: 结束时间
        :param group_by: 分组字段
        :param metrics: 统计指标
        :return: 分析结果
        """
        # 基础查询
        query = self.db.query(SystemLog)
        
        # 应用时间范围过滤
        if start_time:
            query = query.filter(SystemLog.created_at >= start_time)
        if end_time:
            query = query.filter(SystemLog.created_at <= end_time)
            
        # 计算基本统计信息
        total_logs = query.count()
        error_logs = query.filter(SystemLog.level == 'ERROR').count()
        error_rate = (error_logs / total_logs * 100) if total_logs > 0 else 0
        
        # 获取日志级别分布
        level_distribution = (
            query.with_entities(SystemLog.level, func.count(SystemLog.id))
            .group_by(SystemLog.level)
            .all()
        )
        level_stats = {level: count for level, count in level_distribution}
        
        # 获取模块分布
        module_distribution = (
            query.with_entities(SystemLog.module, func.count(SystemLog.id))
            .group_by(SystemLog.module)
            .all()
        )
        module_stats = {module: count for module, count in module_distribution}
        
        # 计算时间趋势（按小时）
        time_trend = (
            query.with_entities(
                func.date_trunc('hour', SystemLog.created_at),
                func.count(SystemLog.id)
            )
            .group_by(func.date_trunc('hour', SystemLog.created_at))
            .order_by(func.date_trunc('hour', SystemLog.created_at))
            .all()
        )
        trend_stats = {str(dt): count for dt, count in time_trend}
        
        # 构建响应
        return {
            "total_logs": total_logs,
            "error_rate": error_rate,
            "level_distribution": level_stats,
            "module_distribution": module_stats,
            "time_trend": trend_stats,
            "start_time": start_time,
            "end_time": end_time
        } 