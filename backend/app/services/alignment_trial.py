"""原片标注 → 字幕偏移试算领域服务。

时间轴标注保留原片毫秒与批注原文；试算、并发更正合并和版本快照都在服务端完成。
区间归属统一使用左闭右开 ``[start_ms, end_ms)``，因此恰好踩在交界毫秒上的标注
只会命中右侧区间一次，不会在相邻区间重复计算。
"""
from __future__ import annotations

from typing import Any, ClassVar

from app.store import store

MEDIA_ID = "MEDI-4000"
TRIAL_ID = "AT-4000"
MARK_ID = "TLMK-4000"
RELEASED_VERSION = "ORIG-RELEASE"
WORKING_VERSION = "WORKING"
TIMELINE_SHIFT_MS = 120
B_CORRECTION_MS = -80

# 题设样片的第 4–6 行。通用种子已有第 1–3 行，这里补齐到六行；第 5、6 行受标注影响。
LINE_FIXTURES: list[dict[str, Any]] = [
    {"n": 4, "start": 3300, "end": 3900, "text": "四秒交界前，主持人完成最后引入"},
    {"n": 5, "start": 4100, "end": 4460, "text": "四秒交界之后，时间轴需要保留明确转场点"},
    {"n": 6, "start": 4520, "end": 4980, "text": "转场完成后，嘉宾继续说明影响范围"},
]

INTERVAL_FIXTURES: list[dict[str, Any]] = [
    {"interval_id": "IV-2800-4000", "start_ms": 2800, "end_ms": 4000, "label": "交界前区间"},
    {"interval_id": "IV-4000-5200", "start_ms": 4000, "end_ms": 5200, "label": "四秒标注区间"},
]


def _to_int(value: Any, default: int = 0) -> int:
    try:
        if value in (None, ""):
            return default
        return int(float(value))
    except (TypeError, ValueError):
        return default


def _default_state() -> dict[str, Any]:
    return {
        "trial_id": TRIAL_ID,
        "media_id": MEDIA_ID,
        "mark_id": MARK_ID,
        "boundary_ms": 4000,
        "shift_ms": TIMELINE_SHIFT_MS,
        "affected_line_numbers": [5, 6],
        "revision": 1,
        "late_correction_arrived": False,
        "b_correction_arrived": False,
        "status": "试算中",
        "created_at": "2026-11-26 15:40:00",
    }


class AlignmentTrialService:
    """以内存 store 保存业务行，试算修订状态保存在类级单例中。"""

    MEDIA_ID = MEDIA_ID
    TRIAL_ID = TRIAL_ID
    MARK_ID = MARK_ID
    state_data: ClassVar[dict[str, Any]] = _default_state()

    def __init__(self) -> None:
        self.ensure_fixture()

    # ------------------------------------------------------------------
    # 种子与状态定位
    # ------------------------------------------------------------------
    def reset(self) -> dict[str, Any]:
        """清理题设数据并重新播种；主要给隔离测试使用。"""
        AlignmentTrialService.state_data = _default_state()
        store._tables["subtitle_align"] = [  # noqa: SLF001 - 测试隔离需要
            row for row in store.rows("subtitle_align") if row.get("关联媒体源") != MEDIA_ID
        ]
        store._tables["timeline_mark"] = [  # noqa: SLF001
            row for row in store.rows("timeline_mark") if row.get("标注点编号") != MARK_ID
        ]
        self.ensure_fixture()
        return self.state_data

    def ensure_fixture(self) -> dict[str, Any]:
        state = AlignmentTrialService.state_data

        marks = store.rows("timeline_mark")
        if not any(row.get("标注点编号") == MARK_ID for row in marks):
            marks.append({
                "id": 4,
                "status": "已复核",
                "pending": False,
                "abnormal": False,
                "标注点编号": MARK_ID,
                "关联媒体源": MEDIA_ID,
                "标注毫秒": "4000",
                "标注类别": "交界/转场/偏移说明",
                "标注文本": "4000ms 交界：四秒标注区间内第 5、6 行统一后移 120ms",
                "批注原文": (
                    "导演批注原文：这里有个 120ms 转场，区间里的字幕整体往后让；"
                    "4000ms 这个交界点只能归一个区间，别重复计算。"
                ),
                "区间起始毫秒": "4000",
                "区间结束毫秒": "5200",
                "建议偏移毫秒": "120",
                "标注人标识": "director_lin",
                "关联分段数": "2",
                "创建时间": "2026-11-26",
            })

        rows = store.rows("subtitle_align")
        for spec in LINE_FIXTURES:
            n = spec["n"]
            align_id = f"SALN-M4000-{n:02d}"
            row = next((item for item in rows if item.get("对齐编号") == align_id), None)
            if row is not None:
                continue
            affected = n in (5, 6)
            timeline_adjustments: list[dict[str, Any]] = []
            if affected:
                timeline_adjustments.append({
                    "adjustment_id": f"ADJ-TLMK-4000-L{n}",
                    "source_type": "timeline_annotation",
                    "source": "timeline_annotation",
                    "source_id": MARK_ID,
                    "source_label": f"原片标注 {MARK_ID}",
                    "author": "director_lin",
                    "delta_start_ms": TIMELINE_SHIFT_MS,
                    "delta_end_ms": TIMELINE_SHIFT_MS,
                    "delta_ms": TIMELINE_SHIFT_MS,
                    "mode": "add",
                    "status": "proposed",
                    "revision": 1,
                    "arrived_at": "2026-11-26 15:40:00",
                    "note": "按原片毫秒命中四秒标注区间，开始/结束一并后移 120ms",
                })
            rows.append({
                "id": n,
                "status": "待对齐",
                "pending": True,
                "abnormal": False,
                "对齐编号": align_id,
                "关联分段": f"SPCH-M4000-{n:02d}",
                "字幕行号": str(n),
                "对齐起始毫秒": str(spec["start"]),
                "对齐结束毫秒": str(spec["end"]),
                "偏移毫秒": "0",
                "对齐方式": "原发行字幕",
                "对齐行数": "1",
                "关联媒体源": MEDIA_ID,
                "媒体标识": MEDIA_ID,
                "line_number": n,
                "字幕文本": spec["text"],
                "original_start_ms": spec["start"],
                "original_end_ms": spec["end"],
                "released_start_ms": spec["start"],
                "released_end_ms": spec["end"],
                "base_start_ms": spec["start"],
                "base_end_ms": spec["end"],
                "current_start_ms": spec["start"],
                "current_end_ms": spec["end"],
                "actual_start_ms": spec["start"],
                "actual_end_ms": spec["end"],
                "net_delta_ms": 0,
                "adopted": False,
                "confirmed": False,
                "needs_review": False,
                "review_required": False,
                "adjustments": timeline_adjustments,
                "source_records": [],
                "confirmation_records": [],
                "version_values": {
                    RELEASED_VERSION: {
                        "version": RELEASED_VERSION,
                        "label": "原发行版本",
                        "start_ms": spec["start"],
                        "end_ms": spec["end"],
                        "delta_ms": 0,
                        "boundary_start_ms": spec["start"],
                        "boundary_end_ms": spec["end"],
                    },
                },
            })
        return state

    def state(self) -> dict[str, Any]:
        self.ensure_fixture()
        return AlignmentTrialService.state_data

    def intervals(self) -> list[dict[str, Any]]:
        return [dict(item) for item in INTERVAL_FIXTURES]

    def assign_boundary(
        self, mark_ms: int = 4000, intervals: list[dict[str, Any]] | None = None,
    ) -> dict[str, Any]:
        """把交界标注分配给唯一区间；默认左闭右开，交界点归右侧区间。"""
        ivs = intervals or self.intervals()
        matched = [
            item for item in ivs
            if _to_int(item.get("start_ms")) <= mark_ms < _to_int(item.get("end_ms"))
        ]
        if len(matched) == 1:
            assigned = matched[0]
            rule = f"{assigned['start_ms']} <= {mark_ms} < {assigned['end_ms']}"
        else:
            right = next((item for item in ivs if _to_int(item.get("start_ms")) == mark_ms), None)
            left = next((item for item in ivs if _to_int(item.get("end_ms")) == mark_ms), None)
            assigned = right or left
            rule = "交界点按左闭右开策略归右侧区间" if right else "末点交界归最后一个区间"
        assigned_id = assigned.get("interval_id") if assigned else None
        return {
            "mark_ms": mark_ms,
            "boundary_ms": mark_ms,
            "policy": "left_closed_right_open",
            "rule": rule,
            "assigned_interval_id": assigned_id,
            "interval_id": assigned_id,
            "match_count": 1 if assigned_id else 0,
            "matched_interval_ids": [assigned_id] if assigned_id else [],
            "duplicated": False,
        }

    # ------------------------------------------------------------------
    # 行定位与计算
    # ------------------------------------------------------------------
    def all_scenario_lines(self) -> list[dict[str, Any]]:
        self.ensure_fixture()
        rows = [
            row for row in store.rows("subtitle_align")
            if row.get("关联媒体源") == MEDIA_ID or row.get("媒体标识") == MEDIA_ID
        ]
        return sorted(rows, key=lambda r: (_to_int(r.get("original_start_ms")), _to_int(r.get("line_number"))))

    def find_line(
        self, ref: Any, media_id: str = MEDIA_ID, *, lookup: str = "auto",
    ) -> dict[str, Any] | None:
        self.ensure_fixture()
        text = str(ref)
        rows = store.rows("subtitle_align")

        def find_entry() -> dict[str, Any] | None:
            if isinstance(ref, int) or (isinstance(ref, str) and ref.isdigit()):
                entry = store.find("subtitle_align", int(ref))
                if entry is not None:
                    return entry
            if text.startswith("SALN"):
                return next((item for item in rows if item.get("对齐编号") == text), None)
            return None

        def find_by_number() -> dict[str, Any] | None:
            number = _to_int(ref, default=-1)
            candidates = [
                row for row in rows
                if _to_int(row.get("line_number"), default=-1) == number
                or _to_int(row.get("字幕行号"), default=-1) == number
            ]
            return next(
                (row for row in candidates if row.get("关联媒体源") == media_id),
                candidates[0] if candidates else None,
            )

        if lookup == "entry":
            return find_entry()
        if lookup == "line":
            return find_by_number() or find_entry()
        return find_entry() or find_by_number()

    def _adjustments(self, row: dict[str, Any]) -> list[dict[str, Any]]:
        value = row.get("adjustments")
        return value if isinstance(value, list) else []

    def _delta(
        self, row: dict[str, Any], *, max_revision: int | None = None,
        statuses: set[str] | None = None,
    ) -> tuple[int, int]:
        start = end = 0
        for adj in self._adjustments(row):
            if max_revision is not None and _to_int(adj.get("revision"), 1) > max_revision:
                continue
            if statuses is not None and str(adj.get("status") or "") not in statuses:
                continue
            start += _to_int(adj.get("delta_start_ms", adj.get("delta_ms")))
            end += _to_int(adj.get("delta_end_ms", adj.get("delta_ms")))
        return start, end

    def _interval_for_row(self, row: dict[str, Any]) -> dict[str, Any]:
        start = _to_int(row.get("original_start_ms", row.get("对齐起始毫秒")))
        end = _to_int(row.get("original_end_ms", row.get("对齐结束毫秒")))
        interval = next(
            (item for item in self.intervals()
             if item["start_ms"] <= start and end <= item["end_ms"]),
            None,
        )
        boundary = self.assign_boundary(4000)
        return {
            "interval_id": interval.get("interval_id") if interval else None,
            "label": interval.get("label") if interval else None,
            "start_ms": interval.get("start_ms") if interval else None,
            "end_ms": interval.get("end_ms") if interval else None,
            "contained_by_original_interval": interval is not None,
            "membership_basis": "使用原发行毫秒判断，不使用试算或更正后的时间重新归区间",
            "boundary_assignment": boundary,
        }

    def _public_source(self, adj: dict[str, Any]) -> dict[str, Any]:
        delta = _to_int(adj.get("delta_ms"), None) if adj.get("delta_ms") is not None else _to_int(adj.get("delta_start_ms"))
        return {
            **adj,
            "origin": adj.get("source_type") or adj.get("source"),
            "source": adj.get("source_type") or adj.get("source"),
            "label": adj.get("source_label") or adj.get("source_id"),
            "delta_ms": delta,
            "signed_delta_ms": delta,
            "direction": "后移" if delta > 0 else "前移" if delta < 0 else "不变",
        }

    def _original_bounds(self, row: dict[str, Any]) -> tuple[int, int]:
        start = row.get("released_start_ms", row.get("original_start_ms", row.get("对齐起始毫秒", 0)))
        end = row.get("released_end_ms", row.get("original_end_ms", row.get("对齐结束毫秒", 0)))
        return _to_int(start), _to_int(end)

    def _recompute_row(self, row: dict[str, Any]) -> dict[str, Any]:
        base_start, base_end = self._original_bounds(row)
        delta_start, delta_end = self._delta(row)
        actual_start = base_start + delta_start
        actual_end = base_end + delta_end
        row["base_start_ms"] = base_start
        row["base_end_ms"] = base_end
        row["net_delta_ms"] = delta_start
        row["current_start_ms"] = actual_start
        row["current_end_ms"] = actual_end
        row["actual_start_ms"] = actual_start
        row["actual_end_ms"] = actual_end
        row["对齐起始毫秒"] = str(actual_start)
        row["对齐结束毫秒"] = str(actual_end)
        row["偏移毫秒"] = str(delta_start)
        row["actual_values"] = {
            "start_ms": actual_start,
            "end_ms": actual_end,
            "delta_start_ms": delta_start,
            "delta_end_ms": delta_end,
        }
        sources = [self._public_source(adj) for adj in self._adjustments(row)]
        row["source_records"] = sources
        row["采纳来源"] = "；".join(
            f"{item['source_label'] if 'source_label' in item else item.get('label')}({item['delta_ms']:+d}ms)"
            for item in self._adjustments(row)
        )
        versions = row.setdefault("version_values", {})
        working = versions.setdefault(WORKING_VERSION, {"version": WORKING_VERSION, "label": "当前采纳版本"})
        working.update({
            "start_ms": actual_start,
            "end_ms": actual_end,
            "delta_ms": delta_start,
            "boundary_start_ms": actual_start,
            "boundary_end_ms": actual_end,
            "adopted": bool(row.get("adopted")),
        })
        return row

    # ------------------------------------------------------------------
    # 试算视图
    # ------------------------------------------------------------------
    def preview(self, payload: dict[str, Any] | None = None) -> dict[str, Any]:
        state = self.state()
        payload = payload or {}
        max_revision = payload.get("client_revision", payload.get("base_revision"))
        max_revision = _to_int(max_revision, default=state["revision"]) if max_revision is not None else None
        if max_revision == 0:
            max_revision = None

        mark_ref = payload.get("mark_ref") or payload.get("mark_id")
        mark: dict[str, Any] | None = None
        if mark_ref not in (None, ""):
            if isinstance(mark_ref, int) or (isinstance(mark_ref, str) and mark_ref.isdigit()):
                mark = store.find("timeline_mark", int(mark_ref))
            if mark is None:
                mark = next(
                    (row for row in store.rows("timeline_mark") if row.get("标注点编号") == mark_ref),
                    None,
                )
        if mark is None:
            marks = store.rows("timeline_mark")
            same_boundary = [row for row in marks if _to_int(row.get("标注毫秒")) == 4000]
            if same_boundary:
                mark = max(same_boundary, key=lambda row: _to_int(row.get("id")))
            else:
                mark = next(
                    (row for row in marks if row.get("标注点编号") == MARK_ID),
                    {},
                )

        boundary_ms = _to_int(mark.get("标注毫秒"), _to_int(state.get("boundary_ms"), 4000))
        boundary_assignment = self.assign_boundary(boundary_ms)
        rows = []
        for row in self.all_scenario_lines():
            if _to_int(row.get("line_number")) not in state["affected_line_numbers"]:
                continue
            original_start = _to_int(row.get("original_start_ms"))
            original_end = _to_int(row.get("original_end_ms"))
            trial_delta_start, trial_delta_end = self._delta(row, max_revision=1)
            server_delta_start, server_delta_end = self._delta(row)
            client_delta_start, client_delta_end = self._delta(row, max_revision=max_revision)
            interval = self._interval_for_row(row)
            rows.append({
                "line_number": _to_int(row.get("line_number")),
                "align_id": row.get("对齐编号"),
                "entry_id": row.get("id"),
                "text": row.get("字幕文本"),
                "sort_ms": original_start,
                "original_start_ms": original_start,
                "original_end_ms": original_end,
                "before_start_ms": original_start,
                "before_end_ms": original_end,
                "trial_delta_ms": trial_delta_start,
                "trial_start_ms": original_start + trial_delta_start,
                "trial_end_ms": original_end + trial_delta_end,
                "after_120_start_ms": original_start + TIMELINE_SHIFT_MS,
                "after_120_end_ms": original_end + TIMELINE_SHIFT_MS,
                "client_revision": max_revision,
                "client_start_ms": original_start + client_delta_start,
                "client_end_ms": original_end + client_delta_end,
                "server_revision": state["revision"],
                "server_delta_ms": server_delta_start,
                "server_start_ms": original_start + server_delta_start,
                "server_end_ms": original_end + server_delta_end,
                "after_start_ms": original_start + server_delta_start,
                "after_end_ms": original_end + server_delta_end,
                "has_late_correction": any(
                    _to_int(adj.get("revision"), 1) > 1 for adj in self._adjustments(row)
                ),
                "adopted": bool(row.get("adopted")),
                "needs_review": bool(row.get("needs_review")),
                "status": row.get("status"),
                "interval": interval,
                "original_interval": interval,
                "sources": [self._public_source(adj) for adj in self._adjustments(row)],
            })
        rows.sort(key=lambda item: (item["sort_ms"], item["line_number"]))
        return {
            "ok": True,
            "trial_id": TRIAL_ID,
            "id": TRIAL_ID,
            "media_id": MEDIA_ID,
            "calculation_basis": "original_film_milliseconds",
            "calculation_note": "服务端始终按原片毫秒计算区间和偏移，已变动的字幕时间不会反过来改变区间归属。",
            "revision": state["revision"],
            "server_revision": state["revision"],
            "mark_ref": mark_ref or MARK_ID,
            "boundary_ms": boundary_ms,
            "mark": mark,
            "timeline_mark": mark,
            "annotation_text": mark.get("标注文本"),
            "annotation_comment_original": mark.get("批注原文"),
            "boundary_assignment": boundary_assignment,
            "intervals": self.intervals(),
            "rows": rows,
            "items": rows,
        }

    # ------------------------------------------------------------------
    # 并发更正
    # ------------------------------------------------------------------
    def _parse_correction_delta(self, payload: dict[str, Any]) -> tuple[int, str | None]:
        for key in ("delta_start_ms", "delta_ms", "signed_delta_ms", "offset_delta_ms"):
            if payload.get(key) is not None:
                return _to_int(payload.get(key)), None

        raw = None
        for key in ("correction_ms", "adjustment_ms", "change_ms", "更正毫秒", "更正量", "偏移更正毫秒"):
            if payload.get(key) is not None:
                raw = _to_int(payload.get(key))
                break
        if raw is None:
            return B_CORRECTION_MS, "default_b_correction"

        direction = str(payload.get("direction") or payload.get("方向") or payload.get("type") or "")
        if any(token in direction for token in ("前", "earlier", "minus", "reduce", "回调", "收回", "negative")):
            return -abs(raw), direction
        if any(token in direction for token in ("后", "later", "plus", "delay", "positive")):
            return abs(raw), direction
        # “乙的 80ms 更正刚到”在题设中是把 +120 的试算值回调 80ms。
        if payload.get("callback") is True or payload.get("回调") is True:
            return -abs(raw), "callback"
        return raw, direction

    def arrive_correction(self, payload: dict[str, Any] | None = None) -> dict[str, Any]:
        payload = dict(payload or {})
        self.ensure_fixture()
        ref = (
            payload.get("line_number") or payload.get("line") or payload.get("字幕行号")
            or payload.get("ref") or 5
        )
        row = self.find_line(ref)
        if row is None:
            return {"ok": False, "message": f"找不到第 {ref} 行字幕"}

        line_number = _to_int(row.get("line_number", row.get("字幕行号")), 5)
        delta, direction = self._parse_correction_delta(payload)
        source_id = str(payload.get("source_id") or payload.get("correction_id") or f"CRLP-YI-L{line_number}-80")
        author = str(payload.get("reviewer") or payload.get("author") or payload.get("operator") or payload.get("更正人") or "乙")

        existing = next(
            (adj for adj in self._adjustments(row) if adj.get("source_id") == source_id),
            None,
        )
        state = self.state()
        if existing is None:
            state["revision"] = _to_int(state.get("revision"), 1) + 1
            adj = {
                "adjustment_id": f"ADJ-{source_id}",
                "source_type": "manual_correction",
                "source": "manual_correction",
                "source_id": source_id,
                "source_label": f"{author}的字幕更正 {source_id}",
                "author": author,
                "delta_start_ms": delta,
                "delta_end_ms": delta,
                "delta_ms": delta,
                "mode": "add",
                "status": "arrived" if not row.get("adopted") else "adopted",
                "revision": state["revision"],
                "arrived_at": "2026-11-26 15:46:00",
                "direction_hint": direction,
                "late": True,
                "note": payload.get("note") or f"{author}的 {abs(delta)}ms 更正送达；作为独立来源保留",
            }
            row.setdefault("adjustments", []).append(adj)
            state["late_correction_arrived"] = True
            if line_number == 5:
                state["b_correction_arrived"] = True

        self._recompute_row(row)
        if row.get("adopted"):
            # 若确认恰好先于更正落库，更正到达后仍重算并把该行打回再审。
            row["needs_review"] = True
            row["review_required"] = True
            row["abnormal"] = True
            row["pending"] = True
            row["status"] = "待再审"
            row["对齐方式"] = "确认后并发更正重算"
            row["是否需再审"] = "是"
            row["再审原因"] = "已采纳后收到新的人工更正，需要复核多源合并结果"
            self._recompute_row(row)

        detail = self.line_detail(line_number)
        return {
            "ok": True,
            "message": f"{author}对第 {line_number} 行的 {abs(delta)}ms 更正已送达",
            "revision": state["revision"],
            "line_number": line_number,
            "delta_ms": delta,
            "detail": detail,
        }

    # ------------------------------------------------------------------
    # 确认与生效
    # ------------------------------------------------------------------
    def _extract_refs(self, payload: dict[str, Any]) -> list[Any]:
        for key in ("line_numbers", "lines", "selected_lines", "selected", "refs", "ids", "entry_ids"):
            value = payload.get(key)
            if isinstance(value, list) and value:
                return value
            if value not in (None, "") and not isinstance(value, list):
                return [value]
        for key in ("line_number", "line", "字幕行号", "ref", "entry_id", "id"):
            if payload.get(key) not in (None, ""):
                return [payload.get(key)]
        return [5, 6]

    def confirm(self, payload: dict[str, Any] | None = None) -> dict[str, Any]:
        payload = dict(payload or {})
        self.ensure_fixture()
        refs = self._extract_refs(payload)
        reviewer = str(payload.get("reviewer") or payload.get("operator") or payload.get("confirmer") or "甲")
        client_revision = payload.get("client_revision", payload.get("base_revision", payload.get("opened_revision")))
        client_revision = _to_int(client_revision, default=1) if client_revision is not None else None
        state = self.state()

        results = []
        missing = []
        for ref in refs:
            row = self.find_line(ref)
            if row is None:
                missing.append(ref)
                continue
            results.append(self._confirm_row(row, reviewer, client_revision, state))

        ok = not missing and bool(results)
        if len(results) == 1:
            message = results[0]["message"]
        elif results:
            message = f"已确认 {len(results)} 行；第 " + "、".join(str(item["line_number"]) for item in results if item["needs_review"]) + " 行需再审"
        else:
            message = "没有可确认的字幕行"
        return {
            "ok": ok,
            "message": message,
            "results": results,
            "missing": missing,
            "revision": state["revision"],
            "entry": results[0].get("entry") if results else None,
        }

    def _confirm_row(
        self, row: dict[str, Any], reviewer: str, client_revision: int | None, state: dict[str, Any],
    ) -> dict[str, Any]:
        line_number = _to_int(row.get("line_number", row.get("字幕行号")))
        server_revision = _to_int(state.get("revision"), 1)
        stale = client_revision is not None and client_revision < server_revision
        late_sources = [
            adj for adj in self._adjustments(row)
            if _to_int(adj.get("revision"), 1) > (client_revision or 0)
        ]
        has_manual = any((adj.get("source_type") or "").startswith("manual") for adj in self._adjustments(row))
        has_late_manual = any(
            (adj.get("source_type") or "").startswith("manual") and _to_int(adj.get("revision"), 1) > 1
            for adj in self._adjustments(row)
        )
        needs_review = bool((stale and late_sources) or has_late_manual or (has_manual and stale))
        self._recompute_row(row)
        actual_start = _to_int(row["actual_start_ms"])
        actual_end = _to_int(row["actual_end_ms"])
        base_start = _to_int(row["released_start_ms"])
        base_end = _to_int(row["released_end_ms"])
        delta = _to_int(row["net_delta_ms"])

        for adj in self._adjustments(row):
            adj["status"] = "adopted"
            adj["adopted_by"] = reviewer

        row["adopted"] = True
        row["confirmed"] = True
        row["needs_review"] = needs_review
        row["review_required"] = needs_review
        row["是否需再审"] = "是" if needs_review else "否"
        row["pending"] = needs_review
        row["abnormal"] = needs_review
        row["status"] = "待再审" if needs_review else "已对齐"
        row["对齐方式"] = "多源合并确认" if needs_review else "标注试算确认"
        row["实际采纳起始毫秒"] = str(actual_start)
        row["实际采纳结束毫秒"] = str(actual_end)
        row["实际采纳偏移毫秒"] = str(delta)
        row["确认人"] = reviewer
        row["确认结果"] = (
            f"已采纳实际起止 {actual_start}-{actual_end}ms（净偏移 {delta:+d}ms）；"
            "检测到确认期间到达的并发更正，需再次审阅"
            if needs_review else
            f"已采纳实际起止 {actual_start}-{actual_end}ms（偏移 {delta:+d}ms），可单独生效"
        )
        if needs_review:
            row["再审原因"] = "甲打开的试算版本之后，乙的 80ms 更正到达；两笔变化均需可追溯"
        else:
            row["再审原因"] = "-"

        record = {
            "confirmation_id": f"AC-L{line_number}-R{server_revision}",
            "reviewer": reviewer,
            "confirmed_by": reviewer,
            "client_revision": client_revision,
            "server_revision": server_revision,
            "stale_submission": stale,
            "concurrent_update": bool(late_sources),
            "before": {"start_ms": base_start, "end_ms": base_end},
            "requested_trial": {"delta_ms": TIMELINE_SHIFT_MS if line_number in (5, 6) else delta},
            "after": {"start_ms": actual_start, "end_ms": actual_end, "delta_ms": delta},
            "actual_values": {"start_ms": actual_start, "end_ms": actual_end},
            "sources": [self._public_source(adj) for adj in self._adjustments(row)],
            "needs_review": needs_review,
            "result": row["确认结果"],
            "confirmed_at": "2026-11-26 15:48:00",
        }
        row.setdefault("confirmation_records", []).append(record)
        latest = row["confirmation_records"][-1]
        row["latest_confirmation"] = latest
        self._recompute_row(row)

        message = (
            f"第 {line_number} 行已合并确认：实际 {actual_start}-{actual_end}ms，需再审"
            if needs_review else
            f"第 {line_number} 行已单独生效：实际 {actual_start}-{actual_end}ms"
        )
        return {
            "line_number": line_number,
            "entry_id": row.get("id"),
            "align_id": row.get("对齐编号"),
            "ok": True,
            "message": message,
            "needs_review": needs_review,
            "review_required": needs_review,
            "actual_start_ms": actual_start,
            "actual_end_ms": actual_end,
            "net_delta_ms": delta,
            "stale": stale,
            "sources": record["sources"],
            "confirmation": latest,
            "entry": row,
        }

    def complete_review(self, ref: Any, reviewer: str = "再审人") -> dict[str, Any]:
        row = self.find_line(ref)
        if row is None:
            return {"ok": False, "message": f"找不到字幕行 {ref}"}
        line_number = _to_int(row.get("line_number", row.get("字幕行号")))
        row["needs_review"] = False
        row["review_required"] = False
        row["是否需再审"] = "否"
        row["pending"] = False
        row["abnormal"] = False
        row["status"] = "已对齐"
        row["对齐方式"] = "多源合并后再审通过"
        row["再审原因"] = "-"
        record = {
            "confirmation_id": f"RV-L{line_number}",
            "reviewer": reviewer,
            "reviewed_by": reviewer,
            "result": "再审通过，实际起止值保持为服务端合并值",
            "reviewed_at": "2026-11-26 16:05:00",
        }
        row.setdefault("confirmation_records", []).append(record)
        self._recompute_row(row)
        return {"ok": True, "message": f"第 {line_number} 行再审已完成", "entry": row}

    # ------------------------------------------------------------------
    # 详情 / 版本
    # ------------------------------------------------------------------
    def _version_key(self, version: str | None) -> str:
        text = str(version or WORKING_VERSION)
        normalized = text.strip().lower().replace("_", "-")
        released_keys = {"released", "original", "origin", "orig-release", "release", "v1"}
        if normalized in released_keys or "原发行" in text or "发行版本" in text:
            return RELEASED_VERSION
        return WORKING_VERSION

    def line_detail(
        self, ref: Any, version: str | None = None, *, lookup: str = "auto",
    ) -> dict[str, Any] | None:
        row = self.find_line(ref, lookup=lookup)
        if row is None:
            return None
        self._recompute_row(row)
        line_number = _to_int(row.get("line_number", row.get("字幕行号")))
        version_key = self._version_key(version)
        released_start, released_end = self._original_bounds(row)
        working_start = _to_int(row.get("actual_start_ms", row.get("对齐起始毫秒", released_start)))
        working_end = _to_int(row.get("actual_end_ms", row.get("对齐结束毫秒", released_end)))
        working_review = bool(row.get("needs_review"))

        if version_key == RELEASED_VERSION:
            view_start, view_end, view_delta = released_start, released_end, 0
            version_notice = "正在按原发行版本复查：显示发行当时的边界，不包含后续试算采纳值。"
            version_needs_review = False
            adopted_in_version = False
        else:
            view_start, view_end = working_start, working_end
            view_delta = _to_int(row.get("net_delta_ms"))
            version_notice = "当前字幕对齐页实际采纳的确认结果。"
            version_needs_review = working_review
            adopted_in_version = bool(row.get("adopted"))

        interval = self._interval_for_row(row)
        sources = [self._public_source(adj) for adj in self._adjustments(row)]
        confirmations = row.get("confirmation_records") if isinstance(row.get("confirmation_records"), list) else []
        return {
            "ok": True,
            "line_number": line_number,
            "entry_id": row.get("id"),
            "align_id": row.get("对齐编号"),
            "media_id": row.get("关联媒体源", MEDIA_ID),
            "text": row.get("字幕文本"),
            "version": version_key,
            "requested_version": version,
            "version_label": "原发行版本" if version_key == RELEASED_VERSION else "当前采纳版本",
            "available_versions": [
                {"key": WORKING_VERSION, "label": "当前采纳版本"},
                {"key": RELEASED_VERSION, "label": "原发行版本"},
            ],
            "version_notice": version_notice,
            # 多组别名，方便页面与接口调用方按命名习惯读取。
            "original_start_ms": released_start,
            "original_end_ms": released_end,
            "released_start_ms": released_start,
            "released_end_ms": released_end,
            "before_start_ms": released_start,
            "before_end_ms": released_end,
            "current_start_ms": view_start,
            "current_end_ms": view_end,
            "actual_start_ms": view_start,
            "actual_end_ms": view_end,
            "start_ms": view_start,
            "end_ms": view_end,
            "boundary_start_ms": view_start,
            "boundary_end_ms": view_end,
            "net_delta_ms": view_delta,
            "offset_ms": view_delta,
            "adopted": adopted_in_version,
            "confirmed": bool(row.get("confirmed")),
            "needs_review": version_needs_review,
            "review_required": version_needs_review,
            "working_needs_review": working_review,
            "是否需再审": "是" if version_needs_review else "否",
            "status": row.get("status"),
            "alignment_method": row.get("对齐方式"),
            "adoption_summary": row.get("确认结果"),
            "sources": sources,
            "source_records": sources,
            "origins": sources,
            "confirmations": confirmations,
            "confirmation_records": confirmations,
            "latest_confirmation": row.get("latest_confirmation"),
            "interval": interval,
            "original_interval": interval,
            "boundary_assignment": interval.get("boundary_assignment"),
            "mark": next((r for r in store.rows("timeline_mark") if r.get("标注点编号") == MARK_ID), {}),
            "entry": row,
        }

    def list_lines(self, version: str | None = None) -> dict[str, Any]:
        lines = [self.line_detail(row.get("id"), version) for row in self.all_scenario_lines()]
        return {
            "ok": True,
            "media_id": MEDIA_ID,
            "version": self._version_key(version),
            "items": lines,
            "rows": lines,
            "total": len(lines),
        }


alignment_trial_service = AlignmentTrialService()
