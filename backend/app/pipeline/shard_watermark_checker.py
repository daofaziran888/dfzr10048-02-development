"""分片水位检查器：连续性校验与推进策略。

核心行为：
- 检查分片序号连续性，只有全部连续产出才推进水位
- 滞后分片触发失败重投登记
- 水位推进前后状态可追溯
"""
from __future__ import annotations

from typing import Any


class ShardWatermarkLine:
    """单条媒体源的水位线：记录已处理分片和滞后信息。"""

    def __init__(self, media_id: str, total_shards: int):
        self.media_id = media_id
        self.total_shards = total_shards
        self.processed: set[int] = set()
        self.last_advanced_seq: int = 0
        self.lag_shards: set[int] = set()

    def mark_processed(self, shard_seq: int) -> None:
        """标记一个分片为已处理。"""
        self.processed.add(shard_seq)
        self.lag_shards.discard(shard_seq)

    def mark_failed(self, shard_seq: int) -> None:
        """标记一个分片为失败（加入滞后集合）。"""
        self.lag_shards.add(shard_seq)

    def check_continuity(self) -> tuple[bool, int]:
        """检查从 1 开始的连续已处理分片序号，返回 (是否可推进, 最大连续序号)。"""
        seq = 0
        for s in range(1, self.total_shards + 1):
            if s not in self.processed:
                break
            seq = s
        can_advance = seq == self.total_shards
        return can_advance, seq

    def advance(self) -> tuple[bool, str]:
        """尝试推进水位：只有全部连续产出才允许推进。"""
        can_advance, max_seq = self.check_continuity()
        if can_advance:
            self.last_advanced_seq = max_seq
            return True, f"媒体源 {self.media_id} 水位推进至分片 {max_seq}/{self.total_shards}"
        missing = sorted(set(range(1, self.total_shards + 1)) - self.processed)
        return False, (
            f"媒体源 {self.media_id} 分片不连续，"
            f"当前最大连续 {max_seq}/{self.total_shards}，缺失分片: {missing}"
        )

    def to_dict(self) -> dict[str, Any]:
        return {
            "media_id": self.media_id,
            "total_shards": self.total_shards,
            "processed_count": len(self.processed),
            "last_advanced_seq": self.last_advanced_seq,
            "lag_count": len(self.lag_shards),
            "lag_shards": sorted(self.lag_shards),
        }


class ShardWatermarkChecker:
    """分片水位检查器：管理全部媒体源的水位线。"""

    def __init__(self) -> None:
        self._lines: dict[str, ShardWatermarkLine] = {}

    def register_media(self, media_id: str, total_shards: int) -> ShardWatermarkLine:
        if media_id not in self._lines:
            self._lines[media_id] = ShardWatermarkLine(media_id, total_shards)
        return self._lines[media_id]

    def get_line(self, media_id: str) -> ShardWatermarkLine | None:
        return self._lines.get(media_id)

    def try_advance(self, media_id: str) -> tuple[bool, str]:
        """尝试推进指定媒体源的水位。"""
        line = self._lines.get(media_id)
        if line is None:
            return False, f"媒体源 {media_id} 未注册水位线"
        return line.advance()

    def snapshot(self) -> dict[str, Any]:
        return {
            "lines": {k: v.to_dict() for k, v in self._lines.items()},
        }