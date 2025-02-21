- settings.py
  - 配置的加载和验证
  - 配置的存储和访问
  - 配置文件的监控
- manager.py
  - 各功能模块管理器的生命周期管理
  - 使用 settings 中的配置来初始化这些管理器
  - 在配置变更时重新加载管理器

```python
# 在其他模块中使用配置
from core.config.setting import settings

# 使用配置
api_prefix = settings.api_config.api_v1_str
db_url = settings.database_config.DATABASE_URL

# 在需要管理器的地方使用 config_manager
from core.config.manager import config_manager

# 使用管理器
db_manager = config_manager.database
cache_manager = config_manager.cache
```