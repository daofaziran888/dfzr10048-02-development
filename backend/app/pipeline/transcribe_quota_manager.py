"""转写配额管理器：超额排队而非丢弃已完成转写。

核心行为：
- 按渠道与引擎维护日配额分钟与已用量
- 超额时排队等待结算窗口重置，不丢弃已完成的转写结果
- 配额恢复时放行排队中的任务
"""
from __future__ import annotations

from typing import Any
from collections import deque


class QuotaSlot:
    """单个配额槽位：记录渠道+引擎的配额状态。"""

    def __init__(
        self, channel: str, engine: str, daily_limit_minutes: int,
    ):
        self.channel = channel
        self.engine = engine
        self.daily_limit = daily_limit_minutes
        self.used_minutes = 0
        self.queued_tasks: deque[str] = deque()
        self.frozen = False

    def try_consume(self, task_id: str, minutes_needed: int) -> tuple[bool, str]:
        """尝试消费配额：充足则扣减，不足则排队。"""
        if self.frozen:
            self.queued_tasks.append(task_id)
            return False, f"配额已冻结，任务 {task_id} 进入排队"

        if self.used_minutes + minutes_needed <= self.daily_limit:
            self.used_minutes += minutes_needed
            return True, f"配额扣减 {minutes_needed} 分钟，剩余 {self.daily_limit - self.used_minutes}"
        else:
            self.queued_tasks.append(task_id)
            return False, (
                f"配额不足：已用 {self.used_minutes}/{self.daily_limit}，"
                f"任务 {task_id} 进入排队"
            )

    def release_queued(self, released_minutes: int) -> list[str]:
        """释放配额并放行排队任务。"""
        self.used_minutes = max(0, self.used_minutes - released_minutes)
        released: list[str] = []
        while self.queued_tasks and self.used_minutes < self.daily_limit:
            task = self.queued_tasks.popleft()
            released.append(task)
        return released

    def to_dict(self) -> dict[str, Any]:
        return {
            "channel": self.channel,
            "engine": self.engine,
            "daily_limit": self.daily_limit,
            "used_minutes": self.used_minutes,
            "queued_count": len(self.queued_tasks),
            "frozen": self.frozen,
        }


class TranscribeQuotaManager:
    """转写配额管理器。"""

    def __init__(self) -> None:
        self._slots: dict[str, QuotaSlot] = {}

    def _slot_key(self, channel: str, engine: str) -> str:
        return f"{channel}::{engine}"

    def register_slot(
        self, channel: str, engine: str, daily_limit_minutes: int,
    ) -> QuotaSlot:
        key = self._slot_key(channel, engine)
        if key not in self._slots:
            self._slots[key] = QuotaSlot(channel, engine, daily_limit_minutes)
        return self._slots[key]

    def consume(
        self, channel: str, engine: str, task_id: str, minutes: int,
    ) -> tuple[bool, str]:
        """消费配额：扣减已用分钟或进入排队。"""
        key = self._slot_key(channel, engine)
        if key not in self._slots:
            self.register_slot(channel, engine, 300)
        return self._slots[key].try_consume(task_id, minutes)

    def reset_window(self, channel: str, engine: str) -> tuple[bool, str]:
        """重置计量窗口：释放全部已用分钟并放行排队任务。"""
        key = self._slot_key(channel, engine)
        if key not in self._slots:
            return False, f"配额槽位 {channel}/{engine} 不存在"
        slot = self._slots[key]
        slot.used_minutes = 0
        released = slot.release_queued(slot.daily_limit)
        return True, f"配额已重置，放行 {len(released)} 个排队任务"

    def snapshot(self) -> dict[str, Any]:
        return {
            "slots": [s.to_dict() for s in self._slots.values()],
            "total_queued": sum(len(s.queued_tasks) for s in self._slots.values()),
        }