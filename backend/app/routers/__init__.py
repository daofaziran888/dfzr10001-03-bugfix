"""业务模块路由汇总。

这里统一按别名导入再暴露 ROUTERS：模块名有可能和内置名撞车（某个业务模块就叫 dict、list
这种名字时），按名字直接 import 会把内置类型覆盖掉，函数注解在运行时求值就会报
'module' object is not subscriptable。
"""
from __future__ import annotations

from app.routers import source as router_source
from app.routers import website as router_website
from app.routers import task as router_task
from app.routers import schedule as router_schedule
from app.routers import increment as router_increment
from app.routers import rpa as router_rpa
from app.routers import log as router_log
from app.routers import retry as router_retry
from app.routers import proxy as router_proxy
from app.routers import parser as router_parser
from app.routers import dedup as router_dedup
from app.routers import release as router_release
from app.routers import alert as router_alert
from app.routers import dashboard as router_dashboard
from app.routers import storage as router_storage
from app.routers import audit as router_audit

ROUTERS = [router_source, router_website, router_task, router_schedule, router_increment, router_rpa, router_log, router_retry, router_proxy, router_parser, router_dedup, router_release, router_alert, router_dashboard, router_storage, router_audit]
