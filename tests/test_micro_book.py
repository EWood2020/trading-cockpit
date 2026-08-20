"""Tests for #17: Micro Book 500€."""

import pytest
from decimal import Decimal
from src.executor.micro_book import (
    MicroBook,
    SizingTier,
    SIZING_CONFIG,
    MICRO_BOOK_CONFIG,
)


class TestSizingConfig:
    """Tests for S1-4 sizing configuration."""
    
    def test_all_tiers_configured(self):
        """All S1-4 tiers should be configured."""
        assert SizingTier.S1 in SIZING_CONFIG
        assert SizingTier.S2 in SIZING_CONFIG
        assert SizingTier.S3 in SIZING_CONFIG
        assert SizingTier.S4 in SIZING_CONFIG
    
    def test_risk_increases_with_tier(self):
        """Higher tiers should have higher risk."""
        s1_risk = SIZING_CONFIG[SizingTier.S1].risk_pct
        s2_risk = SIZING_CONFIG[SizingTier.S2].risk_pct
        s3_risk = SIZING_CONFIG[SizingTier.S3].risk_pct
        s4_risk = SIZING_CONFIG[SizingTier.S4].risk_pct
        
        assert s1_risk < s2_risk < s3_risk < s4_risk
    
    def test_s1_is_minimum_risk(self):
        """S1 should be the minimum risk tier."""
        s1 = SIZING_CONFIG[SizingTier.S1]
        assert s1.risk_pct == 0.01  # 1%


class TestMicroBookInitialization:
    """Tests for MicroBook initialization."""
    
    def test_default_capital(self):
        """Book should start with 500€ by default."""
        book = MicroBook()
        assert book.initial_capital == Decimal("500.00")
        assert book.cash == Decimal("500.00")
    
    def test_starts_at_s2(self):
        """Book should start at S2 (conservative)."""
        book = MicroBook()
        assert book.current_tier == SizingTier.S2
    
    def test_not_paused_initially(self):
        """Book should not be paused initially."""
        book = MicroBook()
        assert book._paused is False
    
    def test_custom_capital(self):
        """Book should accept custom capital."""
        book = MicroBook(capital=Decimal("1000.00"))
        assert book.initial_capital == Decimal("1000.00")


class TestPositionSizing:
    """Tests for position sizing calculations."""
    
    def test_calculate_size_basic(self):
        """Test basic position size calculation."""
        book = MicroBook(capital=Decimal("500.00"))
        book.current_tier = SizingTier.S1  # 1% risk
        
        shares = book.calculate_position_size(
            entry_price=Decimal("50.00"),
            stop_loss=Decimal("45.00"),  # $5 risk per share
        )
        
        assert shares == Decimal("1")
    
    def test_zero_risk_returns_zero_size(self):
        """Zero risk per share should return zero size."""
        book = MicroBook()
        shares = book.calculate_position_size(
            entry_price=Decimal("100.00"),
            stop_loss=Decimal("100.00"),
        )
        assert shares == Decimal("0")
    
    def test_paused_book_returns_zero(self):
        """Paused book should return zero size."""
        book = MicroBook()
        book._paused = True
        shares = book.calculate_position_size(
            entry_price=Decimal("50.00"),
            stop_loss=Decimal("45.00"),
        )
        assert shares == Decimal("0")


class TestDrawdownRules:
    """Tests for estado absorbente drawdown rules."""
    
    def test_soft_drawdown_forces_s1(self):
        """10% drawdown should force S1."""
        book = MicroBook(capital=Decimal("500.00"))
        book.current_tier = SizingTier.S4
        book._peak_equity = Decimal("500.00")
        book.cash = Decimal("440.00")  # 12% drawdown
        
        book._check_drawdown_rules()
        
        assert book.current_tier == SizingTier.S1
        assert book._paused is False
    
    def test_hard_drawdown_pauses_book(self):
        """15% drawdown should pause the book."""
        book = MicroBook(capital=Decimal("500.00"))
        book._peak_equity = Decimal("500.00")
        book.cash = Decimal("420.00")  # 16% drawdown
        
        book._check_drawdown_rules()
        
        assert book._paused is True


class TestTierAdjustment:
    """Tests for tier adjustment on streaks."""
    
    def test_three_wins_tier_up(self):
        """Three consecutive wins should tier up."""
        book = MicroBook()
        book.current_tier = SizingTier.S2
        
        for _ in range(3):
            book._adjust_tier_on_streak(win=True)
        
        assert book.current_tier == SizingTier.S3
    
    def test_three_losses_tier_down(self):
        """Three consecutive losses should tier down."""
        book = MicroBook()
        book.current_tier = SizingTier.S3
        
        for _ in range(3):
            book._adjust_tier_on_streak(win=False)
        
        assert book.current_tier == SizingTier.S2
    
    def test_win_resets_loss_streak(self):
        """A win should reset the loss streak."""
        book = MicroBook()
        book._consecutive_losses = 2
        
        book._adjust_tier_on_streak(win=True)
        
        assert book._consecutive_losses == 0
        assert book._consecutive_wins == 1
    
    def test_cannot_tier_below_s1(self):
        """Cannot go below S1."""
        book = MicroBook()
        book.current_tier = SizingTier.S1
        
        book._tier_down()
        
        assert book.current_tier == SizingTier.S1
    
    def test_cannot_tier_above_s4(self):
        """Cannot go above S4."""
        book = MicroBook()
        book.current_tier = SizingTier.S4
        
        book._tier_up()
        
        assert book.current_tier == SizingTier.S4


class TestPositionManagement:
    """Tests for opening and closing positions."""
    
    def test_open_position_deducts_cash(self):
        """Opening position should deduct cash."""
        book = MicroBook(capital=Decimal("500.00"))
        book.current_tier = SizingTier.S1
        
        position = book.open_position(
            symbol="TEST",
            entry_price=Decimal("50.00"),
            stop_loss=Decimal("45.00"),
            entry_date="2026-08-20",
        )
        
        assert position is not None
        assert book.cash < Decimal("500.00")
    
    def test_cannot_open_duplicate_position(self):
        """Cannot open duplicate position in same symbol."""
        book = MicroBook(capital=Decimal("500.00"))
        book.current_tier = SizingTier.S1
        
        book.open_position("TEST", Decimal("50"), Decimal("45"), "2026-08-20")
        result = book.open_position("TEST", Decimal("60"), Decimal("55"), "2026-08-20")
        
        assert result is None
    
    def test_close_position_adds_cash(self):
        """Closing position should add proceeds to cash."""
        book = MicroBook(capital=Decimal("500.00"))
        book.current_tier = SizingTier.S1
        
        book.open_position("TEST", Decimal("50"), Decimal("45"), "2026-08-20")
        cash_after_open = book.cash
        
        book.close_position("TEST", Decimal("55"), "2026-08-21", "TP")
        
        assert book.cash > cash_after_open


class TestBookConfig:
    """Tests for micro book configuration."""
    
    def test_config_has_required_fields(self):
        """Config should have all required fields."""
        assert MICRO_BOOK_CONFIG["id"] == "#17"
        assert MICRO_BOOK_CONFIG["initial_capital"] == 500
        assert MICRO_BOOK_CONFIG["sizing"] == "S1-4"
    
    def test_config_has_rules(self):
        """Config should define rules."""
        rules = MICRO_BOOK_CONFIG["rules"]
        assert "soft_drawdown" in rules
        assert "hard_drawdown" in rules
        assert rules["starting_tier"] == "S2"
