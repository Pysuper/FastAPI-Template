# 使用

```python
# 创建配置
master_config = DatabaseConfig(
    drivername="postgresql+asyncpg",
    host="localhost",
    port=5432,
    username="user",
    password="password",
    database="db_name",
    pool_size=10,
    max_overflow=20
)

# 从节点配置
replica_configs = [
    {
        "config": {
            "drivername": "postgresql+asyncpg",
            "host": "replica1.host",
            "port": 5432,
            "username": "user",
            "password": "password",
            "database": "db_name",
            "pool_size": 5,
            "max_overflow": 10
        },
        "weight": 2,
        "max_lag": 5
    },
    {
        "config": {
            "drivername": "postgresql+asyncpg",
            "host": "replica2.host",
            "port": 5432,
            "username": "user",
            "password": "password",
            "database": "db_name",
            "pool_size": 5,
            "max_overflow": 10
        },
        "weight": 1,
        "max_lag": 5
    }
]

# 创建读写分离连接池
pool = await pool_factory.create_pool(
    name="main",
    config=master_config,
    pool_type="read_write",
    replica_configs=replica_configs,
    read_strategy="weighted",
    auto_failover=True
)

# 获取读写连接池
read_pool = await pool_factory.get_pool("main", for_read=True)
write_pool = await pool_factory.get_pool("main", for_read=False)

# 使用连接池
async with read_pool.engine.connect() as conn:
    result = await conn.execute("SELECT * FROM users")

async with write_pool.engine.connect() as conn:
    await conn.execute("INSERT INTO users (name) VALUES (:name)", {"name": "test"})

# 获取连接池指标
metrics = pool_factory.get_metrics()

# 关闭连接池
await pool_factory.close_all()
```