"""字幕影响试算与对齐详情的专用路由。

通用 CRUD 仍由 resource 路由处理；这里只承载试算、并发更正合并、确认和版本复查。
路径同时提供连字符资源名和下划线模块名别名，方便不同调用方接入。
"""
from __future__ import annotations

from typing import Any

from fastapi import APIRouter, Request

from app.services.alignment_trial import alignment_trial_service as service

router = APIRouter(prefix="/api", tags=["字幕试算与对齐详情"])


async def _payload(request: Request) -> dict[str, Any]:
    try:
        value = await request.json()
        return value if isinstance(value, dict) else {}
    except Exception:  # noqa: BLE001 - 空 body 时使用题设默认值
        return {}


@router.get("/alignment-trial")
@router.get("/alignment-trials")
@router.get("/alignment-trial/preview")
@router.get("/timeline_mark/trial")
@router.get("/timeline-marks/trial")
def trial_preview_get(client_revision: int | None = None, mark_ref: str | None = None) -> dict[str, Any]:
    return service.preview({"client_revision": client_revision, "mark_ref": mark_ref})


@router.get("/timeline-marks/{mark_ref}/trial")
@router.get("/timeline_mark/{mark_ref}/trial")
def mark_trial_preview(mark_ref: str, client_revision: int | None = None) -> dict[str, Any]:
    preview = service.preview({"client_revision": client_revision, "mark_ref": mark_ref})
    preview["requested_mark_ref"] = mark_ref
    return preview


@router.get("/subtitle_align/trial")
@router.get("/subtitle-align/trial")
@router.get("/alignment-impact")
@router.get("/trial")
def subtitle_trial_alias(client_revision: int | None = None, mark_ref: str | None = None) -> dict[str, Any]:
    return service.preview({"client_revision": client_revision, "mark_ref": mark_ref})


@router.post("/alignment-trial/preview")
async def trial_preview_post(request: Request) -> dict[str, Any]:
    return service.preview(await _payload(request))


@router.get("/alignment-trial/trials")
def list_trials() -> dict[str, Any]:
    preview = service.preview()
    return {"ok": True, "items": [preview], "total": 1}


@router.get("/alignment-trial/trials/{trial_id}")
def get_trial(trial_id: str) -> dict[str, Any]:
    return service.preview({"trial_id": trial_id})


@router.post("/alignment-trial/confirm")
@router.post("/alignment-trials/confirm")
@router.post("/subtitle_align/trial/confirm")
@router.post("/subtitle-align/trial/confirm")
@router.post("/alignment-impact/confirm")
@router.post("/trial/confirm")
async def confirm_trial(request: Request) -> dict[str, Any]:
    return service.confirm(await _payload(request))


@router.post("/alignment-trial/trials/{trial_id}/confirm")
async def confirm_named_trial(trial_id: str, request: Request) -> dict[str, Any]:
    payload = await _payload(request)
    payload.setdefault("trial_id", trial_id)
    return service.confirm(payload)


@router.post("/alignment-trial/lines/{ref}/confirm")
async def confirm_line(ref: str, request: Request) -> dict[str, Any]:
    payload = await _payload(request)
    payload["line_number"] = ref
    return service.confirm(payload)


@router.post("/alignment-trial/corrections")
@router.post("/alignment-trials/corrections")
@router.post("/subtitle_align/corrections")
@router.post("/subtitle-align/corrections")
@router.post("/trial/corrections")
async def register_correction(request: Request) -> dict[str, Any]:
    return service.arrive_correction(await _payload(request))


@router.post("/alignment-trial/lines/{ref}/corrections")
async def register_line_correction(ref: str, request: Request) -> dict[str, Any]:
    payload = await _payload(request)
    payload["line_number"] = ref
    return service.arrive_correction(payload)


@router.post("/alignment-trial/reset")
def reset_trial() -> dict[str, Any]:
    state = service.reset()
    return {"ok": True, "message": "题设试算已重置", "state": state}


@router.post("/alignment-trial/scenario/b-correction")
def arrive_b_correction() -> dict[str, Any]:
    return service.arrive_correction({
        "line_number": 5,
        "delta_ms": -80,
        "reviewer": "乙",
        "source_id": "CRLP-YI-L5-80",
        "note": "乙对第 5 行的 80ms 更正刚到，按回调 80ms 处理",
    })


@router.post("/alignment-trial/lines/{ref}/complete-review")
async def complete_line_review(ref: str, request: Request) -> dict[str, Any]:
    payload = await _payload(request)
    return service.complete_review(ref, str(payload.get("reviewer") or payload.get("operator") or "再审人"))


@router.get("/alignment-trial/lines")
def list_trial_lines(version: str | None = None) -> dict[str, Any]:
    return service.list_lines(version)


@router.get("/alignment-trial/lines/{ref}")
def get_trial_line(ref: str, version: str | None = None) -> dict[str, Any]:
    detail = service.line_detail(ref, version, lookup="line")
    if detail is None:
        return {"ok": False, "message": f"找不到字幕行 {ref}"}
    return detail


@router.get("/alignment-trial/entries/{entry_id}")
def get_trial_entry(entry_id: int, version: str | None = None) -> dict[str, Any]:
    detail = service.line_detail(entry_id, version, lookup="entry")
    if detail is None:
        return {"ok": False, "message": f"找不到对齐记录 {entry_id}"}
    return detail


@router.get("/subtitle-alignments/{ref}")
@router.get("/subtitle-align/{ref}")
@router.get("/subtitle-align/{ref}/detail")
@router.get("/subtitle_align/{ref}/detail")
@router.get("/subtitle_align/detail/{ref}")
@router.get("/subtitle_align/line/{ref}")
def subtitle_alignment_detail(ref: str, version: str | None = None) -> dict[str, Any]:
    detail = service.line_detail(ref, version, lookup="auto")
    if detail is None:
        return {"ok": False, "message": f"找不到字幕对齐行 {ref}"}
    return detail
