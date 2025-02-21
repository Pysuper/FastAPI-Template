import json
import logging
import random
import re
import time
import uuid
from collections import defaultdict
from dataclasses import asdict, dataclass
from datetime import datetime
from pathlib import Path
from typing import Dict, List, Optional

from sqlalchemy.engine import CursorResult

logger = logging.getLogger(__name__)


@dataclass
class SlowQueryInfo:
    """慢查询信息"""

    query_id: str  # 查询ID
    sql: str  # SQL语句
    parameters: Dict  # 参数
    start_time: datetime  # 开始时间
    duration: float  # 执行时长(秒)
    result_count: Optional[int]  # 结果数量
    database: str  # 数据库名
    user: str  # 用户名
    client_host: str  # 客户端主机
    stack_trace: str  # 堆栈跟踪
    explain_plan: Optional[Dict]  # 执行计划
    table_stats: Optional[Dict]  # 表统计信息
    index_stats: Optional[Dict]  # 索引使用统计

    def to_dict(self) -> Dict:
        """转换为字典"""
        return asdict(self)

    @classmethod
    def from_dict(cls, data: Dict) -> "SlowQueryInfo":
        """从字典创建"""
        return cls(**{k: datetime.fromisoformat(v) if k == "start_time" else v for k, v in data.items()})


class SlowQueryLogger:
    """慢查询日志记录器"""

    def __init__(
        self,
        log_dir: str = "logs/slow_queries",
        threshold: float = 1.0,  # 慢查询阈值(秒)
        max_file_size: int = 100 * 1024 * 1024,  # 100MB
        max_files: int = 10,
        collect_explain: bool = True,  # 是否收集执行计划
        collect_stats: bool = True,  # 是否收集统计信息
        sample_rate: float = 1.0,  # 采样率(0-1)
    ):
        self.log_dir = Path(log_dir)
        self.threshold = threshold
        self.max_file_size = max_file_size
        self.max_files = max_files
        self.collect_explain = collect_explain
        self.collect_stats = collect_stats
        self.sample_rate = sample_rate

        self.current_file: Optional[Path] = None
        self.current_size = 0

        # 创建日志目录
        self.log_dir.mkdir(parents=True, exist_ok=True)

        # 初始化当前日志文件
        self._init_current_file()

        # 统计信息
        self._stats = {
            "total_queries": 0,
            "slow_queries": 0,
            "total_duration": 0.0,
            "max_duration": 0.0,
            "min_duration": float("inf"),
            "avg_duration": 0.0,
        }

    def _init_current_file(self):
        """初始化当前日志文件"""
        # 查找最新的日志文件
        log_files = sorted(self.log_dir.glob("slow_query_*.log"), key=lambda p: p.stat().st_mtime, reverse=True)

        if not log_files:
            # 创建新文件
            self.current_file = self.log_dir / f"slow_query_{datetime.now().strftime('%Y%m%d_%H%M%S')}.log"
            self.current_size = 0
        else:
            self.current_file = log_files[0]
            self.current_size = self.current_file.stat().st_size

        # 如果当前文件大小超过限制,创建新文件
        if self.current_size >= self.max_file_size:
            self._rotate_files()

    def _rotate_files(self):
        """轮转日志文件"""
        # 获取所有日志文件
        log_files = sorted(self.log_dir.glob("slow_query_*.log"), key=lambda p: p.stat().st_mtime)

        # 如果文件数超过限制,删除最旧的文件
        while len(log_files) >= self.max_files:
            log_files[0].unlink()
            log_files = log_files[1:]

        # 创建新文件
        self.current_file = self.log_dir / f"slow_query_{datetime.now().strftime('%Y%m%d_%H%M%S')}.log"
        self.current_size = 0

    def _write_entry(self, entry: SlowQueryInfo):
        """写入日志条目"""
        # 如果当前文件大小超过限制,轮转文件
        if self.current_size >= self.max_file_size:
            self._rotate_files()

        # 写入日志条目
        entry_data = json.dumps(entry.to_dict()) + "\n"
        entry_size = len(entry_data.encode("utf-8"))

        with self.current_file.open("a", encoding="utf-8") as f:
            f.write(entry_data)

        self.current_size += entry_size

    async def _collect_explain_plan(self, session, sql: str, parameters: Dict) -> Optional[Dict]:
        """收集执行计划"""
        try:
            result = await session.execute(f"EXPLAIN {sql}", parameters)
            return result.mappings().all()
        except Exception as e:
            logger.error(f"Failed to collect explain plan: {e}")
            return None

    async def _collect_table_stats(self, session, sql: str) -> Optional[Dict]:
        """收集表统计信息"""
        try:
            # 解析SQL中涉及的表
            tables = self._extract_tables(sql)

            stats = {}
            for table in tables:
                result = await session.execute(
                    f"""
                    SELECT
                        table_rows,
                        avg_row_length,
                        data_length,
                        index_length
                    FROM information_schema.tables
                    WHERE table_name = :table
                """,
                    {"table": table},
                )
                stats[table] = result.mappings().first()

            return stats
        except Exception as e:
            logger.error(f"Failed to collect table stats: {e}")
            return None

    async def _collect_index_stats(self, session, sql: str) -> Optional[Dict]:
        """收集索引使用统计"""
        try:
            # 解析SQL中涉及的表
            tables = self._extract_tables(sql)

            stats = {}
            for table in tables:
                result = await session.execute(
                    f"""
                    SELECT
                        index_name,
                        column_name,
                        cardinality,
                        nullable
                    FROM information_schema.statistics
                    WHERE table_name = :table
                """,
                    {"table": table},
                )
                stats[table] = result.mappings().all()

            return stats
        except Exception as e:
            logger.error(f"Failed to collect index stats: {e}")
            return None

    def _extract_tables(self, sql: str) -> List[str]:
        """从SQL中提取表名"""

        # 这里使用简单的方式,仅作示例
        sql = sql.lower()
        tables = []

        # 提取FROM子句后的表名
        if " from " in sql:
            from_part = sql.split(" from ")[1].split(" where ")[0]
            tables.extend(t.strip() for t in from_part.split(","))

        # 提取JOIN子句的表名
        if " join " in sql:
            join_parts = sql.split(" join ")
            for part in join_parts[1:]:
                table = part.split(" ")[0]
                tables.append(table.strip())

        return list(set(tables))

    def _should_sample(self) -> bool:
        """是否应该采样"""
        if self.sample_rate >= 1.0:
            return True
        return random.random() < self.sample_rate

    def _update_stats(self, duration: float):
        """更新统计信息"""
        self._stats["total_queries"] += 1
        self._stats["total_duration"] += duration
        self._stats["max_duration"] = max(self._stats["max_duration"], duration)
        self._stats["min_duration"] = min(self._stats["min_duration"], duration)
        self._stats["avg_duration"] = self._stats["total_duration"] / self._stats["total_queries"]

        if duration >= self.threshold:
            self._stats["slow_queries"] += 1

    async def log_query(
        self, session, sql: str, parameters: Dict, result: Optional[CursorResult] = None, stack_trace: str = None
    ):
        """记录查询"""
        # 更新统计信息
        duration = time.time() - getattr(result, "start_time", 0)
        self._update_stats(duration)

        # 如果执行时间小于阈值,不记录
        if duration < self.threshold:
            return

        # 是否需要采样
        if not self._should_sample():
            return

        # 收集额外信息
        explain_plan = None
        table_stats = None
        index_stats = None

        if self.collect_explain:
            explain_plan = await self._collect_explain_plan(session, sql, parameters)

        if self.collect_stats:
            table_stats = await self._collect_table_stats(session, sql)
            index_stats = await self._collect_index_stats(session, sql)

        # 创建慢查询信息
        query_info = SlowQueryInfo(
            query_id=str(uuid.uuid4()),
            sql=sql,
            parameters=parameters,
            start_time=datetime.fromtimestamp(getattr(result, "start_time", time.time())),
            duration=duration,
            result_count=result.rowcount if result else None,
            database=session.bind.url.database,
            user=session.bind.url.username,
            client_host=session.bind.url.host,
            stack_trace=stack_trace or "",
            explain_plan=explain_plan,
            table_stats=table_stats,
            index_stats=index_stats,
        )

        # 写入日志
        self._write_entry(query_info)

    def get_slow_queries(
        self,
        start_time: Optional[datetime] = None,
        end_time: Optional[datetime] = None,
        min_duration: Optional[float] = None,
        limit: int = 100,
    ) -> List[SlowQueryInfo]:
        """获取慢查询记录"""
        queries = []

        # 遍历所有日志文件
        for log_file in sorted(self.log_dir.glob("slow_query_*.log"), key=lambda p: p.stat().st_mtime):
            with log_file.open("r", encoding="utf-8") as f:
                for line in f:
                    try:
                        entry_data = json.loads(line)
                        query = SlowQueryInfo.from_dict(entry_data)

                        # 过滤条件
                        if start_time and query.start_time < start_time:
                            continue
                        if end_time and query.start_time > end_time:
                            continue
                        if min_duration and query.duration < min_duration:
                            continue

                        queries.append(query)

                        if len(queries) >= limit:
                            break
                    except Exception as e:
                        logger.error(f"Failed to parse log entry: {e}")

        return sorted(queries, key=lambda q: q.duration, reverse=True)

    def get_metrics(self) -> Dict:
        """获取日志指标"""
        log_files = list(self.log_dir.glob("slow_query_*.log"))
        total_size = sum(f.stat().st_size for f in log_files)

        return {
            "log_dir": str(self.log_dir),
            "threshold": self.threshold,
            "max_file_size": self.max_file_size,
            "max_files": self.max_files,
            "current_file": str(self.current_file) if self.current_file else None,
            "current_size": self.current_size,
            "total_files": len(log_files),
            "total_size": total_size,
            "stats": self._stats.copy(),
        }


class QueryPattern:
    """查询模式"""

    def __init__(
        self,
        pattern_id: str,
        sql_pattern: str,
        total_count: int = 0,
        total_duration: float = 0.0,
        min_duration: float = float("inf"),
        max_duration: float = 0.0,
        example_queries: List[SlowQueryInfo] = None,
    ):
        self.pattern_id = pattern_id
        self.sql_pattern = sql_pattern
        self.total_count = total_count
        self.total_duration = total_duration
        self.min_duration = min_duration
        self.max_duration = max_duration
        self.example_queries = example_queries or []

    @property
    def avg_duration(self) -> float:
        """平均执行时长"""
        if self.total_count == 0:
            return 0.0
        return self.total_duration / self.total_count

    def add_query(self, query: SlowQueryInfo):
        """添加查询"""
        self.total_count += 1
        self.total_duration += query.duration
        self.min_duration = min(self.min_duration, query.duration)
        self.max_duration = max(self.max_duration, query.duration)

        # 保留最慢的查询作为示例
        self.example_queries.append(query)
        self.example_queries.sort(key=lambda q: q.duration, reverse=True)
        self.example_queries = self.example_queries[:5]  # 最多保留5个示例

    def to_dict(self) -> Dict:
        """转换为字典"""
        return {
            "pattern_id": self.pattern_id,
            "sql_pattern": self.sql_pattern,
            "total_count": self.total_count,
            "total_duration": self.total_duration,
            "min_duration": self.min_duration,
            "max_duration": self.max_duration,
            "avg_duration": self.avg_duration,
            "example_queries": [q.to_dict() for q in self.example_queries],
        }


class QueryAnalyzer:
    """查询分析器"""

    def __init__(self, slow_query_logger: SlowQueryLogger, pattern_threshold: int = 3):  # 模式识别阈值
        self.logger = slow_query_logger
        self.pattern_threshold = pattern_threshold

    def _normalize_sql(self, sql: str) -> str:
        """规范化SQL,提取模式"""

        # 这里使用简单的方式,仅作示例
        sql = sql.lower()

        # 替换数字
        sql = re.sub(r"\d+", "?", sql)

        # 替换字符串
        sql = re.sub(r"'[^']*'", "?", sql)

        # 替换IN列表
        sql = re.sub(r"in\s*\([^)]+\)", "in (?)", sql)

        return sql

    def _analyze_patterns(self, queries: List[SlowQueryInfo]) -> List[QueryPattern]:
        """分析查询模式"""
        patterns = defaultdict(lambda: QueryPattern(pattern_id=str(uuid.uuid4()), sql_pattern=""))

        # 按模式分组
        for query in queries:
            pattern_sql = self._normalize_sql(query.sql)
            pattern = patterns[pattern_sql]
            pattern.sql_pattern = pattern_sql
            pattern.add_query(query)

        # 过滤掉出现次数少的模式
        return [pattern for pattern in patterns.values() if pattern.total_count >= self.pattern_threshold]

    def _analyze_tables(self, queries: List[SlowQueryInfo]) -> Dict[str, Dict]:
        """分析表使用情况"""
        table_stats = defaultdict(
            lambda: {
                "query_count": 0,
                "total_duration": 0.0,
                "avg_duration": 0.0,
                "row_count": 0,
                "data_size": 0,
                "index_size": 0,
            }
        )

        for query in queries:
            if not query.table_stats:
                continue

            for table, stats in query.table_stats.items():
                table_stats[table]["query_count"] += 1
                table_stats[table]["total_duration"] += query.duration
                table_stats[table]["row_count"] = stats.get("table_rows", 0)
                table_stats[table]["data_size"] = stats.get("data_length", 0)
                table_stats[table]["index_size"] = stats.get("index_length", 0)

        # 计算平均值
        for stats in table_stats.values():
            if stats["query_count"] > 0:
                stats["avg_duration"] = stats["total_duration"] / stats["query_count"]

        return dict(table_stats)

    def _analyze_indexes(self, queries: List[SlowQueryInfo]) -> Dict[str, Dict]:
        """分析索引使用情况"""
        index_stats = defaultdict(
            lambda: defaultdict(
                lambda: {
                    "query_count": 0,
                    "total_duration": 0.0,
                    "avg_duration": 0.0,
                    "cardinality": 0,
                }
            )
        )

        for query in queries:
            if not query.index_stats:
                continue

            for table, indexes in query.index_stats.items():
                for index in indexes:
                    index_name = index["index_name"]
                    index_stats[table][index_name]["query_count"] += 1
                    index_stats[table][index_name]["total_duration"] += query.duration
                    index_stats[table][index_name]["cardinality"] = index["cardinality"]

        # 计算平均值
        for table_stats in index_stats.values():
            for stats in table_stats.values():
                if stats["query_count"] > 0:
                    stats["avg_duration"] = stats["total_duration"] / stats["query_count"]

        return {table: dict(indexes) for table, indexes in index_stats.items()}

    def _analyze_time_distribution(self, queries: List[SlowQueryInfo]) -> Dict[str, int]:
        """分析时间分布"""
        distribution = defaultdict(int)

        for query in queries:
            hour = query.start_time.strftime("%H:00")
            distribution[hour] += 1

        return dict(distribution)

    def analyze(
        self,
        start_time: Optional[datetime] = None,
        end_time: Optional[datetime] = None,
        min_duration: Optional[float] = None,
    ) -> Dict:
        """分析慢查询"""
        # 获取慢查询记录
        queries = self.logger.get_slow_queries(
            start_time=start_time,
            end_time=end_time,
            min_duration=min_duration,
        )

        if not queries:
            return {
                "patterns": [],
                "tables": {},
                "indexes": {},
                "time_distribution": {},
                "summary": {
                    "total_queries": 0,
                    "total_duration": 0.0,
                    "avg_duration": 0.0,
                    "start_time": start_time.isoformat() if start_time else None,
                    "end_time": end_time.isoformat() if end_time else None,
                },
            }

        # 分析查询模式
        patterns = self._analyze_patterns(queries)

        # 分析表使用情况
        tables = self._analyze_tables(queries)

        # 分析索引使用情况
        indexes = self._analyze_indexes(queries)

        # 分析时间分布
        time_distribution = self._analyze_time_distribution(queries)

        # 生成分析报告
        return {
            "patterns": [p.to_dict() for p in patterns],
            "tables": tables,
            "indexes": indexes,
            "time_distribution": time_distribution,
            "summary": {
                "total_queries": len(queries),
                "total_duration": sum(q.duration for q in queries),
                "avg_duration": sum(q.duration for q in queries) / len(queries),
                "start_time": start_time.isoformat() if start_time else None,
                "end_time": end_time.isoformat() if end_time else None,
            },
        }

    def get_recommendations(self, analysis: Dict) -> List[Dict]:
        """获取优化建议"""
        recommendations = []

        # 分析查询模式
        for pattern in analysis["patterns"]:
            if pattern["avg_duration"] > 10.0:  # 平均执行时间超过10秒
                recommendations.append(
                    {
                        "type": "query_pattern",
                        "level": "high",
                        "title": "发现耗时查询模式",
                        "description": f"查询模式 '{pattern['sql_pattern']}' "
                        f"平均执行时间为 {pattern['avg_duration']:.2f} 秒, "
                        f"共执行 {pattern['total_count']} 次",
                        "suggestion": "建议优化SQL或添加适当的索引",
                    }
                )

        # 分析表
        for table, stats in analysis["tables"].items():
            if stats["row_count"] > 1000000:  # 表数据量大
                recommendations.append(
                    {
                        "type": "table",
                        "level": "medium",
                        "title": f"表 {table} 数据量较大",
                        "description": f"表包含 {stats['row_count']} 行数据, "
                        f"数据大小 {stats['data_size'] / 1024 / 1024:.2f}MB",
                        "suggestion": "建议考虑分表或归档历史数据",
                    }
                )

        # 分析索引
        for table, indexes in analysis["indexes"].items():
            for index_name, stats in indexes.items():
                if stats["cardinality"] < 100:  # 索引区分度低
                    recommendations.append(
                        {
                            "type": "index",
                            "level": "low",
                            "title": f"索引 {index_name} 区分度低",
                            "description": f"表 {table} 的索引 {index_name} "
                            f"区分度为 {stats['cardinality']}, "
                            f"使用次数 {stats['query_count']}",
                            "suggestion": "建议检查索引是否合理",
                        }
                    )

        # 分析时间分布
        time_distribution = analysis["time_distribution"]
        peak_hour = max(time_distribution.items(), key=lambda x: x[1])[0]
        peak_count = time_distribution[peak_hour]

        if peak_count > 100:  # 峰值查询量大
            recommendations.append(
                {
                    "type": "time_distribution",
                    "level": "medium",
                    "title": f"发现查询峰值",
                    "description": f"在 {peak_hour} 时段出现查询峰值, " f"共 {peak_count} 次慢查询",
                    "suggestion": "建议调整业务逻辑或增加缓存",
                }
            )

        return sorted(recommendations, key=lambda r: {"high": 0, "medium": 1, "low": 2}[r["level"]])
