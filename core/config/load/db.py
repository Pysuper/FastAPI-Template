from typing import List, Optional
from urllib.parse import quote_plus

from pydantic import Field, validator
from sqlalchemy import URL

from core.config.load.base import BaseConfig


class DatabaseConfig(BaseConfig):
    """数据库配置类"""

    # 数据库连接配置
    driver: str = Field(default="mysql+asyncmy", description="数据库驱动")
    host: str = Field(default="localhost", description="数据库主机")
    port: int = Field(default=your_port, description="数据库端口")
    username: str = Field(default="project_name", description="数据库用户名")
    password: str = Field(default="bSCKN64kJjXT5f5J", description="数据库密码")
    database: str = Field(default="project_name", description="数据库名")
    charset: str = Field(default="utf8mb4", description="数据库字符集")
    database_uri: Optional[str] = None

    # 连接池配置
    pool_size: int = Field(default=5, description="连接池大小")
    max_overflow: int = Field(default=10, description="最大溢出连接数")
    pool_timeout: int = Field(default=30, description="连接池超时时间")
    pool_recycle: int = Field(default=3600, description="连接回收时间")
    pool_pre_ping: bool = Field(default=True, description="是否预先ping")

    # 查询配置
    echo_sql: bool = Field(default=False, description="是否打印SQL语句")
    echo_pool: bool = Field(default=False, description="是否打印连接池日志")

    # 读写分离配置
    read_hosts: List[str] = Field(default=["localhost"], description="只读数据库主机列表")
    read_ports: List[int] = Field(default=[your_port], description="只读数据库端口列表")
    read_usernames: List[str] = Field(default=["project_name"], description="只读数据库用户名列表")
    read_passwords: List[str] = Field(default=["bSCKN64kJjXT5f5J"], description="只读数据库密码列表")
    read_databases: List[str] = Field(default=["project_name"], description="只读数据库名列表")

    # 兼容旧版本配置
    SQLALCHEMY_DATABASE_URI: Optional[str] = None
    SQLALCHEMY_ECHO: bool = False
    SQLALCHEMY_POOL_SIZE: int = 5
    SQLALCHEMY_MAX_OVERFLOW: int = 10
    SQLALCHEMY_POOL_TIMEOUT: int = 30
    SQLALCHEMY_POOL_RECYCLE: int = 3600

    def get_url(self) -> str:
        """获取数据库URL"""
        encoded_username = quote_plus(self.username)
        encoded_password = quote_plus(self.password)
        print(
            f"MySQL ==> {self.driver}://{encoded_username}:{encoded_password}@{self.host}:{self.port}/{self.database}"
        )
        return f"{self.driver}://{encoded_username}:{encoded_password}@{self.host}:{self.port}/{self.database}"

    def get_engine_options(self) -> dict:
        """获取数据库引擎选项"""
        return {
            "pool_size": self.pool_size,
            "max_overflow": self.max_overflow,
            "pool_timeout": self.pool_timeout,
            "pool_recycle": self.pool_recycle,
            "echo": self.echo_sql,
            "echo_pool": self.echo_pool,
        }

    async def get_async_url(self) -> dict:
        """获取异步数据库URL"""
        return await self.get_async_engine_options()

    async def get_async_engine_options(self) -> dict:
        """获取数据库引擎选项"""
        return {
            "pool_size": self.pool_size,
            "max_overflow": self.max_overflow,
            "pool_timeout": self.pool_timeout,
            "pool_recycle": self.pool_recycle,
            "echo": self.echo_sql,
            "echo_pool": self.echo_pool,
        }

    @property
    def url(self) -> URL:
        """获取数据库连接URL"""
        return URL.create(
            drivername=self.driver,
            username=self.username,
            password=self.password,
            host=self.host,
            port=self.port,
            database=self.database,
            query={"charset": self.charset},
        )

    @validator("database_uri", pre=True)
    def assemble_db_connection(cls, v: Optional[str], values: dict) -> str:
        """组装数据库连接URI"""
        if isinstance(v, str):
            return v

        return (
            f"mysql+aiomysql://{values.get('user')}:{values.get('password')}@"
            f"{values.get('host')}:{values.get('port')}/{values.get('database')}?"
            f"charset={values.get('charset')}"
        )

    @property
    def write_url(self) -> str:
        """获取写库连接URL"""
        return (
            f"mysql+aiomysql://{self.username}:{self.password}@"
            f"{self.host}:{self.port}/{self.database}?"
            f"charset={self.charset}"
        )

    @property
    def read_urls(self) -> List[str]:
        """获取读库连接URL列表"""
        urls = []
        for i in range(len(self.read_hosts)):
            urls.append(
                f"mysql+aiomysql://{self.read_usernames[i]}:{self.read_passwords[i]}@"
                f"{self.read_hosts[i]}:{self.read_ports[i]}/{self.read_databases[i]}?"
                f"charset={self.charset}"
            )
        return urls or [self.write_url]

    @property
    def master_url(self) -> str:
        """获取主库连接URL（兼容旧版本）"""
        return self.write_url

    class Config:
        """Pydantic配置"""

        from_attributes = True
        validate_assignment = True
        json_schema_extra = {
            "example": {
                "driver": "mysql+asyncmy",
                "host": "localhost",
                "port": 3306,
                "username": "root",
                "password": "",
                "database": "project_name",
            }
        }
