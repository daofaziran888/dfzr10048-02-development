"""原片标注试算、并发更正合并与发行版本快照测试。"""
from __future__ import annotations

from app.services.alignment_trial import alignment_trial_service


class TestAlignmentTrial:
    def setup_method(self) -> None:
        alignment_trial_service.reset()

    def test_preview_orders_lines_by_original_film_time(self) -> None:
        preview = alignment_trial_service.preview()

        assert preview["ok"] is True
        assert preview["annotation_comment_original"]
        assert "4000ms" in preview["annotation_comment_original"] or "4000ms" in str(preview["mark"])
        assert [row["line_number"] for row in preview["rows"]] == [5, 6]
        assert [row["sort_ms"] for row in preview["rows"]] == sorted(
            row["sort_ms"] for row in preview["rows"]
        )
        assert all(row["trial_delta_ms"] == 120 for row in preview["rows"])
        assert [(row["trial_start_ms"], row["trial_end_ms"]) for row in preview["rows"]] == [
            (4220, 4580),
            (4640, 5100),
        ]

    def test_boundary_mark_is_assigned_to_exactly_one_interval(self) -> None:
        result = alignment_trial_service.assign_boundary(4000)

        assert result["match_count"] == 1
        assert result["duplicated"] is False
        assert result["assigned_interval_id"] == "IV-4000-5200"
        assert result["matched_interval_ids"] == ["IV-4000-5200"]

    def test_line_six_can_be_confirmed_independently(self) -> None:
        result = alignment_trial_service.confirm({
            "line_number": 6,
            "reviewer": "甲",
            "client_revision": 1,
        })

        line_six = result["results"][0]
        assert line_six["ok"] is True
        assert (line_six["actual_start_ms"], line_six["actual_end_ms"]) == (4640, 5100)
        assert line_six["needs_review"] is False

        line_five = alignment_trial_service.line_detail(5)
        assert line_five is not None
        assert line_five["adopted"] is False

    def test_late_b_correction_is_kept_as_separate_source_and_flags_review(self) -> None:
        arrived = alignment_trial_service.arrive_correction({})
        assert arrived["ok"] is True
        assert arrived["delta_ms"] == -80

        result = alignment_trial_service.confirm({
            "line_number": 5,
            "reviewer": "甲",
            "client_revision": 1,
        })
        line_five = result["results"][0]

        assert (line_five["actual_start_ms"], line_five["actual_end_ms"]) == (4140, 4500)
        assert line_five["net_delta_ms"] == 40
        assert line_five["needs_review"] is True
        assert [(source["source_id"], source["delta_ms"]) for source in line_five["sources"]] == [
            ("TLMK-4000", 120),
            ("CRLP-YI-L5-80", -80),
        ]

        detail = alignment_trial_service.line_detail(5)
        assert detail is not None
        assert detail["interval"]["contained_by_original_interval"] is True
        assert detail["working_needs_review"] is True

    def test_released_version_keeps_original_boundaries(self) -> None:
        alignment_trial_service.arrive_correction({})
        alignment_trial_service.confirm({"line_numbers": [5, 6], "client_revision": 1})

        released_five = alignment_trial_service.line_detail(5, "released")
        released_six = alignment_trial_service.line_detail(6, "原发行版本")
        working_five = alignment_trial_service.line_detail(5)

        assert released_five is not None and released_six is not None
        assert (released_five["actual_start_ms"], released_five["actual_end_ms"]) == (4100, 4460)
        assert (released_six["actual_start_ms"], released_six["actual_end_ms"]) == (4520, 4980)
        assert released_five["needs_review"] is False
        assert working_five is not None
        assert (working_five["actual_start_ms"], working_five["actual_end_ms"]) == (4140, 4500)
