# -*- coding:utf-8 -*-
"""
@Project ：Speedy 
@File    ：prometheus.py
@Author  ：PySuper
@Date    ：2024/12/24 17:18 
@Desc    ：Speedy prometheus.py
"""

from prometheus_client import Counter, Gauge, Histogram

# Prometheus指标
REQUEST_COUNT = Counter(
    "http_requests_total",
    "Total HTTP requests",
    ["method", "endpoint", "status"],
)

REQUEST_LATENCY = Histogram(
    "http_request_duration_seconds",
    "HTTP request duration in seconds",
    ["method", "endpoint"],
)

REQUESTS_IN_PROGRESS = Gauge(
    "http_requests_in_progress",
    "Number of HTTP requests in progress",
    ["method", "endpoint"],
)

RATE_LIMIT_EXCEEDED = Counter(
    "rate_limit_exceeded_total",
    "Number of requests that exceeded the rate limit",
    ["method", "endpoint"],
)
