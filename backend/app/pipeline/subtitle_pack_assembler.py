"""字幕包装配器：按生效版本组装并绑定版本引用。

核心行为：
- 按生效转写版本导出字幕包
- 字幕包绑定版本号，保证可追溯
- 被引用版本不得静默覆盖
- 纠错合入触发字幕包重算
"""
from __future__ import annotations

from typing import Any
import hashlib


class SubtitlePackEntry:
    """字幕包条目：记录版本绑定与内容校验。"""

    def __init__(
        self, pack_id: str, media_id: str, bound_version: str,
        line_count: int, duration_seconds: float, export_format: str,
    ):
        self.pack_id = pack_id
        self.media_id = media_id
        self.bound_version = bound_version
        self.line_count = line_count
        self.duration_seconds = duration_seconds
        self.export_format = export_format
        self.checksum = ""
        self.available = False
        self.recompute_needed = False

    def compute_checksum(self, content: str) -> str:
        """计算字幕内容校验和。"""
        self.checksum = hashlib.md5(content.encode()).hexdigest()[:8]
        return self.checksum

    def to_dict(self) -> dict[str, Any]:
        return {
            "pack_id": self.pack_id,
            "media_id": self.media_id,
            "bound_version": self.bound_version,
            "line_count": self.line_count,
            "duration_seconds": self.duration_seconds,
            "export_format": self.export_format,
            "checksum": self.checksum,
            "available": self.available,
            "recompute_needed": self.recompute_needed,
        }


class SubtitlePackAssembler:
    """字幕包装配器。"""

    def __init__(self) -> None:
        self._packs: list[SubtitlePackEntry] = []
        self._version_pack_map: dict[str, list[str]] = {}

    def create_pack(
        self, pack_id: str, media_id: str, version_id: str,
        line_count: int, duration_seconds: float, export_format: str,
        content: str,
    ) -> SubtitlePackEntry:
        """创建字幕包并绑定版本。"""
        entry = SubtitlePackEntry(
            pack_id=pack_id, media_id=media_id,
            bound_version=version_id, line_count=line_count,
            duration_seconds=duration_seconds, export_format=export_format,
        )
        entry.compute_checksum(content)
        entry.available = True
        self._packs.append(entry)
        self._version_pack_map.setdefault(version_id, []).append(pack_id)
        return entry

    def has_reference(self, version_id: str) -> bool:
        """检查版本是否被字幕包引用。"""
        return version_id in self._version_pack_map and len(self._version_pack_map[version_id]) > 0

    def get_ref_count(self, version_id: str) -> int:
        """获取版本的引用数量。"""
        return len(self._version_pack_map.get(version_id, []))

    def mark_recompute(self, version_id: str) -> list[str]:
        """标记需要重算的字幕包（纠错合入后）。"""
        pack_ids = self._version_pack_map.get(version_id, [])
        for entry in self._packs:
            if entry.pack_id in pack_ids:
                entry.recompute_needed = True
                entry.available = False
        return pack_ids

    def get_packs_by_version(self, version_id: str) -> list[SubtitlePackEntry]:
        """获取绑定到指定版本的全部字幕包。"""
        pack_ids = self._version_pack_map.get(version_id, [])
        return [p for p in self._packs if p.pack_id in pack_ids]

    def snapshot(self) -> dict[str, Any]:
        return {
            "packs": [p.to_dict() for p in self._packs],
            "total_packs": len(self._packs),
            "available_count": sum(1 for p in self._packs if p.available),
        }