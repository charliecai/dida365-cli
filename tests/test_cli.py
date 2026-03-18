"""Tests for CLI date parsing and helper functions."""

import pytest

from dida.cli import _parse_date, _parse_priority_list, _parse_status_list


class TestParseDate:
    """Tests for _parse_date helper."""

    def test_today(self) -> None:
        result = _parse_date("today")
        assert "T23:59:00" in result

    def test_tomorrow(self) -> None:
        result = _parse_date("tomorrow")
        assert "T23:59:00" in result

    def test_iso_date(self) -> None:
        result = _parse_date("2026-03-15")
        assert result.startswith("2026-03-15")

    def test_iso_datetime(self) -> None:
        result = _parse_date("2026-03-15T14:30")
        assert "2026-03-15" in result
        assert "14:30" in result

    def test_invalid_date(self) -> None:
        with pytest.raises(ValueError, match="无法解析日期"):
            _parse_date("not-a-date")

    def test_case_insensitive(self) -> None:
        result = _parse_date("TODAY")
        assert "T23:59:00" in result


class TestParseStatusList:
    """Tests for _parse_status_list helper."""

    def test_single_normal(self) -> None:
        assert _parse_status_list("normal") == [0]

    def test_single_completed(self) -> None:
        assert _parse_status_list("completed") == [2]

    def test_multiple_statuses(self) -> None:
        assert _parse_status_list("normal,completed") == [0, 2]

    def test_with_whitespace(self) -> None:
        assert _parse_status_list(" normal , completed ") == [0, 2]

    def test_case_insensitive(self) -> None:
        assert _parse_status_list("Normal") == [0]
        assert _parse_status_list("COMPLETED") == [2]

    def test_invalid_status(self) -> None:
        with pytest.raises(ValueError, match="Invalid status 'invalid'"):
            _parse_status_list("invalid")

    def test_mixed_valid_invalid(self) -> None:
        with pytest.raises(ValueError, match="Invalid status 'bad'"):
            _parse_status_list("normal,bad")


class TestParsePriorityList:
    """Tests for _parse_priority_list helper."""

    def test_single_none(self) -> None:
        assert _parse_priority_list("none") == [0]

    def test_single_low(self) -> None:
        assert _parse_priority_list("low") == [1]

    def test_single_medium(self) -> None:
        assert _parse_priority_list("medium") == [3]

    def test_single_high(self) -> None:
        assert _parse_priority_list("high") == [5]

    def test_multiple_priorities(self) -> None:
        assert _parse_priority_list("high,medium,low") == [5, 3, 1]

    def test_with_whitespace(self) -> None:
        assert _parse_priority_list(" high , low ") == [5, 1]

    def test_invalid_priority(self) -> None:
        with pytest.raises(ValueError):
            _parse_priority_list("urgent")
