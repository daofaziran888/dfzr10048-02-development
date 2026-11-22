"""媒体分片切分领域服务：按单段时长切分媒体源为有序分片并记录校验和，产出分片记录数据集供转码作业消费。"""
from __future__ import annotations

from typing import Any
import hashlib

from app.services.base import BaseModuleService
from app.store import store


class MediaShardService(BaseModuleService):
    MODULE = "media_shard"
    ENTITY = "分片记录"
    OPERATION_TERM = "切分"
    LIST_FIELDS = ["分片编号", "关联通道", "起始秒", "结束秒", "分片字节", "校验和", "分片序号", "落盘时间"]
    REQUIRED_FIELDS = ["分片编号", "关联通道", "起始秒"]
    STATUS_ORDER = ["已落盘", "校验中", "校验通过", "校验不符"]
    ACTION_RULES = {"发起校验": "校验中", "确认通过": "校验通过", "登记不符": "校验不符"}
    NEGATIVE_ACTIONS = []

    def compute_checksum(self, shard_id: str, content: str) -> tuple[str, bool]:
        """计算分片校验和并与记录比对。"""
        rows = store.rows(self.MODULE)
        checksum = hashlib.md5(content.encode()).hexdigest()[:8]
        for r in rows:
            if r.get("分片编号") == shard_id:
                r["校验和"] = checksum
                if r.get("校验和") == checksum:
                    r["status"] = "校验通过"
                    r["pending"] = False
                    return checksum, True
        return checksum, False

    def get_shards_by_channel(self, channel: str) -> list[dict[str, Any]]:
        """获取指定通道的全部已落盘分片，按分片序号排序。"""
        rows = store.rows(self.MODULE)
        shards = [
            r for r in rows
            if r.get("关联通道") == channel and r.get("status") == "已落盘"
        ]
        shards.sort(key=lambda r: int(r.get("分片序号", "0")))
        return shards

    def check_shard_continuity(self, channel: str) -> tuple[bool, list[int]]:
        """检查指定通道的分片序号连续性。"""
        shards = self.get_shards_by_channel(channel)
        seqs = [int(s.get("分片序号", "0")) for s in shards]
        if not seqs:
            return False, []
        min_seq, max_seq = min(seqs), max(seqs)
        missing = [s for s in range(min_seq, max_seq + 1) if s not in seqs]
        return len(missing) == 0, missing

    def get_validated_count(self, channel: str) -> int:
        """统计指定通道校验通过的分片数。"""
        rows = store.rows(self.MODULE)
        return sum(
            1 for r in rows
            if r.get("关联通道") == channel and r.get("status") == "校验通过"
        )