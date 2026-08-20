"""Tests for weekly scoreboard generator."""

import pytest
import json
from datetime import datetime
from src.reports.weekly_scoreboard import (
    WeeklyScoreboardGenerator,
    WeeklyMetrics,
    BookPerformance,
    OutputFormat,
    DEPRECATION_NOTE,
)


class TestBookPerformance:
    """Tests for BookPerformance dataclass."""
    
    def test_beating_spy_positive_alpha(self):
        """Book with positive alpha should beat SPY."""
        book = BookPerformance(
            book_name="test",
            equity=10500,
            pnl_week=500,
            pnl_week_pct=5.0,
            alpha_vs_spy=2.5,
            trades_week=3,
            win_rate=0.67,
            drawdown=3.0,
        )
        assert book.beating_spy is True
    
    def test_not_beating_spy_negative_alpha(self):
        """Book with negative alpha should not beat SPY."""
        book = BookPerformance(
            book_name="test",
            equity=9800,
            pnl_week=-200,
            pnl_week_pct=-2.0,
            alpha_vs_spy=-1.5,
            trades_week=2,
            win_rate=0.5,
            drawdown=5.0,
        )
        assert book.beating_spy is False


class TestWeeklyMetrics:
    """Tests for WeeklyMetrics dataclass."""
    
    def test_default_values(self):
        """Test default values are set correctly."""
        metrics = WeeklyMetrics(
            week_start="2026-08-17",
            week_end="2026-08-23",
        )
        assert metrics.books == []
        assert metrics.spy_return == 0.0
        assert metrics.total_pnl == 0.0


class TestWeeklyScoreboardGenerator:
    """Tests for WeeklyScoreboardGenerator."""
    
    def test_initialization(self):
        """Test generator initializes correctly."""
        gen = WeeklyScoreboardGenerator()
        assert gen.data_source is None
        assert gen._cache == {}
    
    def test_fetch_metrics_returns_weekly_metrics(self):
        """fetch_metrics should return WeeklyMetrics."""
        gen = WeeklyScoreboardGenerator()
        metrics = gen.fetch_metrics()
        
        assert isinstance(metrics, WeeklyMetrics)
        assert metrics.week_start is not None
        assert metrics.week_end is not None
    
    def test_generate_both(self):
        """Generate should return both formats when specified."""
        gen = WeeklyScoreboardGenerator()
        metrics = WeeklyMetrics(
            week_start="2026-08-17",
            week_end="2026-08-23",
        )
        
        result = gen.generate(metrics, OutputFormat.BOTH)
        
        assert "telegram" in result
        assert "s2_8" in result


class TestTelegramFormat:
    """Tests for Telegram output format."""
    
    def test_telegram_contains_header(self):
        """Telegram output should have header."""
        gen = WeeklyScoreboardGenerator()
        metrics = WeeklyMetrics(
            week_start="2026-08-17",
            week_end="2026-08-23",
        )
        
        result = gen.generate(metrics, OutputFormat.TELEGRAM)
        
        assert "Scoreboard Semanal" in result["telegram"]


class TestS28Format:
    """Tests for S2-8 output format."""
    
    def test_s2_8_is_valid_json(self):
        """S2-8 output should be valid JSON."""
        gen = WeeklyScoreboardGenerator()
        metrics = WeeklyMetrics(
            week_start="2026-08-17",
            week_end="2026-08-23",
        )
        
        result = gen.generate(metrics, OutputFormat.S2_8)
        parsed = json.loads(result["s2_8"])
        
        assert "report_type" in parsed
        assert parsed["report_type"] == "S2-8_weekly"


class TestDeprecationNote:
    """Tests for deprecation documentation."""
    
    def test_deprecation_note_exists(self):
        """Deprecation note should be documented."""
        assert "RETIRAR" in DEPRECATION_NOTE
        assert "revisión-interina" in DEPRECATION_NOTE
        assert "Claude" in DEPRECATION_NOTE
