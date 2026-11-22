"""抽样质检闸：字错率阈值校验与阻断放行。

核心行为：
- 抽样统计字错率
- 字错率超限时阻断版本生效
- 阻断后触发纠错回路
- 放行后才允许版本过渡至生效
"""
from __future__ import annotations

from typing import Any


class SampleQcRecord:
    """质检样本记录。"""

    def __init__(
        self, sample_id: str, task_id: str, segment_count: int,
        error_count: int, error_rate: float, threshold: float,
    ):
        self.sample_id = sample_id
        self.task_id = task_id
        self.segment_count = segment_count
        self.error_count = error_count
        self.error_rate = error_rate
        self.threshold = threshold
        self.blocked = self.error_rate > self.threshold
        self.correction_triggered = False

    def to_dict(self) -> dict[str, Any]:
        return {
            "sample_id": self.sample_id,
            "task_id": self.task_id,
            "segment_count": self.segment_count,
            "error_count": self.error_count,
            "error_rate": self.error_rate,
            "threshold": self.threshold,
            "blocked": self.blocked,
            "correction_triggered": self.correction_triggered,
        }


class SampleQcGate:
    """抽样质检闸门。"""

    def __init__(self, default_threshold: float = 0.05) -> None:
        self.default_threshold = default_threshold
        self._records: list[SampleQcRecord] = []
        self._blocked_tasks: set[str] = set()

    def evaluate(
        self, task_id: str, segment_count: int,
        error_count: int, threshold: float | None = None,
    ) -> SampleQcRecord:
        """评估字错率并决定是否阻断。"""
        thresh = threshold if threshold is not None else self.default_threshold
        error_rate = error_count / max(segment_count, 1)
        record = SampleQcRecord(
            sample_id=f"QC-{task_id}-{len(self._records) + 1:04d}",
            task_id=task_id,
            segment_count=segment_count,
            error_count=error_count,
            error_rate=error_rate,
            threshold=thresh,
        )
        self._records.append(record)
        if record.blocked:
            self._blocked_tasks.add(task_id)
        return record

    def is_blocked(self, task_id: str) -> bool:
        """检查任务是否被阻断。"""
        return task_id in self._blocked_tasks

    def get_blocked_tasks(self) -> set[str]:
        """获取所有被阻断的任务 ID。"""
        return set(self._blocked_tasks)

    def clear_block(self, task_id: str) -> tuple[bool, str]:
        """清除阻断标记（纠错回路完成后）。"""
        if task_id in self._blocked_tasks:
            self._blocked_tasks.discard(task_id)
            for rec in self._records:
                if rec.task_id == task_id:
                    rec.correction_triggered = True
            return True, f"任务 {task_id} 阻断已清除"
        return False, f"任务 {task_id} 未被阻断"

    def snapshot(self) -> dict[str, Any]:
        return {
            "records": [r.to_dict() for r in self._records],
            "blocked_count": len(self._blocked_tasks),
            "blocked_tasks": sorted(self._blocked_tasks),
        }