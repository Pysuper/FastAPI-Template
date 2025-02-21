# 第三方集成模块

## 模块简介

第三方集成模块提供了与外部服务和系统集成的统一接口，包括支付服务、消息推送、对象存储、地图服务等常用第三方服务的集成实现。

## 核心功能

1. 支付服务
   - 支付宝
   - 微信支付
   - PayPal
   - 银联支付
   - 加密货币

2. 云服务
   - 对象存储
   - 消息队列
   - 邮件服务
   - CDN服务
   - 云数据库

3. 社交平台
   - 微信
   - 微博
   - Facebook
   - Twitter
   - LinkedIn

4. 基础服务
   - 短信服务
   - 地图服务
   - 验证码
   - OCR识别
   - 实时通讯

## 使用方法

### 支付集成

```python
from core.third.payment import AliPay, WeChatPay

# 支付宝支付
alipay = AliPay(
    app_id="your_app_id",
    private_key_path="path/to/private_key.pem",
    public_key_path="path/to/public_key.pem"
)

# 创建订单
order = await alipay.create_order(
    out_trade_no="123456",
    total_amount=100.00,
    subject="测试商品"
)

# 微信支付
wxpay = WeChatPay(
    app_id="your_app_id",
    mch_id="your_mch_id",
    api_key="your_api_key"
)

# 创建支付
result = await wxpay.create_jsapi_payment(
    openid="user_openid",
    out_trade_no="123456",
    total_fee=10000
)
```

### 云存储

```python
from core.third.storage import OSSStorage, S3Storage

# 阿里云OSS
oss = OSSStorage(
    access_key="your_access_key",
    secret_key="your_secret_key",
    bucket="your_bucket"
)

# 上传文件
file_url = await oss.upload_file(
    file_path="path/to/file",
    object_name="folder/file.jpg"
)

# 亚马逊S3
s3 = S3Storage(
    access_key="your_access_key",
    secret_key="your_secret_key",
    bucket="your_bucket",
    region="us-east-1"
)

# 下载文件
await s3.download_file(
    object_name="folder/file.jpg",
    file_path="path/to/download"
)
```

### 消息推送

```python
from core.third.push import WeChatPush, APNSPush

# 微信推送
wechat = WeChatPush(
    app_id="your_app_id",
    app_secret="your_app_secret"
)

# 发送模板消息
await wechat.send_template_message(
    openid="user_openid",
    template_id="template_id",
    data={
        "first": "消息通知",
        "keyword1": "订单已支付",
        "keyword2": "2024-01-05 12:00:00",
        "remark": "感谢您的使用"
    }
)

# iOS推送
apns = APNSPush(
    cert_file="path/to/cert.pem",
    key_file="path/to/key.pem"
)

# 发送推送
await apns.send_notification(
    device_token="device_token",
    alert="新消息通知",
    badge=1,
    sound="default"
)
```

## 配置选项

```python
THIRD_PARTY_CONFIG = {
    "payment": {
        "alipay": {
            "app_id": "your_app_id",
            "private_key_path": "path/to/private_key.pem",
            "public_key_path": "path/to/public_key.pem",
            "sandbox": False
        },
        "wechat": {
            "app_id": "your_app_id",
            "mch_id": "your_mch_id",
            "api_key": "your_api_key",
            "cert_path": "path/to/cert.pem"
        }
    },
    "storage": {
        "oss": {
            "access_key": "your_access_key",
            "secret_key": "your_secret_key",
            "endpoint": "oss-cn-beijing.aliyuncs.com",
            "bucket": "your_bucket"
        },
        "s3": {
            "access_key": "your_access_key",
            "secret_key": "your_secret_key",
            "region": "us-east-1",
            "bucket": "your_bucket"
        }
    },
    "push": {
        "wechat": {
            "app_id": "your_app_id",
            "app_secret": "your_app_secret"
        },
        "apns": {
            "cert_file": "path/to/cert.pem",
            "key_file": "path/to/key.pem",
            "sandbox": False
        }
    }
}
```

## 最佳实践

1. 配置管理
   - 环境隔离
   - 密钥保护
   - 配置验证
   - 动态配置

2. 错误处理
   - 重试机制
   - 降级策略
   - 超时控制
   - 异常日志

3. 性能优化
   - 连接池
   - 异步处理
   - 缓存策略
   - 批量操作

## 注意事项

1. 安全考虑
   - 密钥管理
   - 数据加密
   - 访问控制
   - 安全审计

2. 可用性
   - 服务监控
   - 故障转移
   - 限流控制
   - 容错处理

3. 维护更新
   - API版本
   - 依赖更新
   - 兼容性
   - 文档同步 