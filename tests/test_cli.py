"""Tests for CLI date parsing and helper functions."""

import pytest

from dida.cli import _parse_date


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
