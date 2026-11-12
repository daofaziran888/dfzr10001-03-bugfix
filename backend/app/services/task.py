"""采集任务业务规则：状态流转、字段校验与筛选口径都收在这里。

状态机：草稿 → 待执行 → 执行中 → 已完成，只能依次前进，不允许回退或跳级。
暂停/恢复只是执行现场的开关：暂停期间状态冻结不推进，恢复后回到暂停前状态。
取消立即终止任务，主状态按取消时的结果留档，之后任何动作（包括晚到的恢复）都不再生效。
每次状态变化都会追加一条执行日志（只增不改），并向调度编排同步唯一一条运行记录。
"""
from __future__ import annotations

import threading
from datetime import datetime
from typing import Any

from app.store import store

MODULE = "task"
REQUIRED_FIELDS = ["任务编号", "任务名称", "关联源端"]
STATUS_ORDER = ["草稿", "待执行", "执行中", "已完成"]

ACTION_SUBMIT = "提交执行"
ACTION_PAUSE = "暂停任务"
ACTION_RESUME = "恢复任务"
ACTION_CANCEL = "取消任务"
ACTIONS = (ACTION_SUBMIT, ACTION_PAUSE, ACTION_RESUME, ACTION_CANCEL)

# 只有已提交且未终止的任务可以暂停/取消
ACTIVE_STATUSES = ("待执行", "执行中")

# 动作串行化：并发提交只保留第一次，"校验 + 流转 + 同步日志/调度"在同一把锁里原子完成
ACTION_LOCK = threading.Lock()


def _now() -> str:
    return datetime.now().strftime("%Y-%m-%d %H:%M:%S")


def _next_code(rows: list[dict[str, Any]], field: str, prefix: str) -> str:
    suffix = 0
    for row in rows:
        code = str(row.get(field, ""))
        if code.startswith(prefix) and code[len(prefix):].isdigit():
            suffix = max(suffix, int(code[len(prefix):]))
    return f"{prefix}{suffix + 1:04d}"


def _status_snapshot(entry: dict[str, Any]) -> str:
    """留档用的状态快照：主状态叠加暂停/终止标记。"""
    status = str(entry.get("status", ""))
    if entry.get("cancelled"):
        return f"{status}（已取消）"
    if entry.get("paused"):
        return f"{status}（已暂停）"
    return status


class TaskService:
    def list_entries(
        self,
        *,
        keyword: str | None = None,
        status: str | None = None,
        page: int = 1,
        size: int = 20,
    ) -> tuple[list[dict[str, Any]], int]:
        rows = store.rows(MODULE)
        if keyword:
            rows = [row for row in rows if keyword in str(row.get("任务编号", ""))]
        if status:
            rows = [row for row in rows if row.get("status") == status]
        total = len(rows)
        start = max(page - 1, 0) * size
        return rows[start:start + size], total

    def get_entry(self, entry_id: int) -> dict[str, Any] | None:
        return store.find(MODULE, entry_id)

    def create_entry(self, values: dict[str, Any]) -> tuple[dict[str, Any] | None, list[str]]:
        missing = [field for field in REQUIRED_FIELDS if not str(values.get(field) or "").strip()]
        if missing:
            return None, missing
        rows = store.rows(MODULE)
        entry = {"id": max((int(row.get("id", 0)) for row in rows), default=0) + 1}
        entry.update({field: values.get(field) for field in REQUIRED_FIELDS})
        entry["status"] = STATUS_ORDER[0]
        entry["pending"] = True
        entry["abnormal"] = False
        entry["paused"] = False
        entry["cancelled"] = False
        rows.append(entry)
        return entry, []

    def run_action(self, entry_id: int, action: str) -> tuple[dict[str, Any] | None, str]:
        with ACTION_LOCK:
            entry = store.find(MODULE, entry_id)
            if entry is None:
                return None, f"采集任务 {entry_id} 不存在或已归档"
            if action not in ACTIONS:
                return None, f"动作「{action}」不属于采集任务可执行范围"
            error = self._guard(entry, action)
            if error is not None:
                return None, error
            message = self._apply(entry, action)
            self._append_log(entry, action)
            return entry, message

    def _guard(self, entry: dict[str, Any], action: str) -> str | None:
        """动作前置校验：返回 None 表示放行，否则给出可读的拒绝原因。"""
        status = str(entry.get("status", ""))
        if entry.get("cancelled"):
            return f"采集任务已取消并留档，「{action}」不再生效"
        if action == ACTION_SUBMIT:
            if entry.get("paused"):
                return "采集任务处于暂停状态，请先恢复再提交执行"
            if status != STATUS_ORDER[0]:
                return f"采集任务当前状态为「{status}」，已提交过，本次重复提交被拦截，未生成新的运行记录"
            return None
        if action == ACTION_PAUSE:
            if status not in ACTIVE_STATUSES:
                return f"采集任务当前状态为「{status}」，只有待执行或执行中的任务才能暂停"
            if entry.get("paused"):
                return "采集任务已处于暂停状态，请勿重复暂停"
            return None
        if action == ACTION_RESUME:
            if not entry.get("paused"):
                return "采集任务未处于暂停状态，恢复请求被拒绝"
            return None
        if action == ACTION_CANCEL:
            if status not in ACTIVE_STATUSES:
                return f"采集任务当前状态为「{status}」，无需取消"
            return None
        return None

    def _apply(self, entry: dict[str, Any], action: str) -> str:
        """执行状态流转：只动状态与标记位，批次大小、执行窗口、关联源端等业务字段保持原样。"""
        if action == ACTION_SUBMIT:
            entry["status"] = "待执行"
            entry["pending"] = True
            entry["abnormal"] = False
            self._ensure_schedule_record(entry)
            return "采集任务已提交，进入待执行队列"
        if action == ACTION_PAUSE:
            entry["paused"] = True
            entry["pending"] = True
            return "采集任务已暂停，状态冻结在当前节点，恢复前不会推进"
        if action == ACTION_RESUME:
            entry["paused"] = False
            return "采集任务已恢复，回到暂停前状态继续执行"
        if action == ACTION_CANCEL:
            entry["paused"] = False
            entry["cancelled"] = True
            entry["pending"] = False
            entry["abnormal"] = True
            self._close_schedule_record(entry)
            return "采集任务已取消，状态按取消时结果留档"
        return "动作已执行"

    def _ensure_schedule_record(self, entry: dict[str, Any]) -> None:
        """提交执行时同步调度运行记录：同一任务编号只保留一条，重复提交不再新增。"""
        code = str(entry.get("任务编号", ""))
        rows = store.rows("schedule")
        for row in rows:
            if str(row.get("关联任务", "")) == code:
                return
        rows.append({
            "id": max((int(row.get("id", 0)) for row in rows), default=0) + 1,
            "status": "已启用",
            "pending": False,
            "abnormal": False,
            "计划编号": _next_code(rows, "计划编号", "SCHE-"),
            "关联任务": code,
            "调度表达式": str(entry.get("采集频率", "")),
            "优先级": "默认",
            "超时阈值": "30分钟",
            "失败策略": "记录后跳过",
            "通知渠道": "站内信",
            "是否启用": "是",
        })

    def _close_schedule_record(self, entry: dict[str, Any]) -> None:
        """任务取消时把对应调度运行记录停用，调度页同步反映执行终止。"""
        code = str(entry.get("任务编号", ""))
        for row in store.rows("schedule"):
            if str(row.get("关联任务", "")) == code:
                row["status"] = "已停用"
                row["是否启用"] = "否"

    def _append_log(self, entry: dict[str, Any], action: str) -> None:
        """每次状态变化追加一条执行日志：只增不改，旧日志不会被新结果覆盖。"""
        rows = store.rows("log")
        now = _now()
        cancelled = action == ACTION_CANCEL
        rows.append({
            "id": max((int(row.get("id", 0)) for row in rows), default=0) + 1,
            "status": "部分失败" if cancelled else "成功",
            "pending": False,
            "abnormal": cancelled,
            "日志编号": _next_code(rows, "日志编号", "LOG-"),
            "关联任务": str(entry.get("任务编号", "")),
            "开始时间": now,
            "结束时间": now,
            "采集行数": "0",
            "成功条数": "0",
            "失败条数": "0",
            "错误信息": "任务被取消" if cancelled else "",
            "动作": action,
            "任务状态": _status_snapshot(entry),
        })
