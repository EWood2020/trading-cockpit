"""Tests for LAB_001: GainzAlgo strategy."""

import pytest
from src.executor.gainzalgo import GainzAlgo, Candle, Signal, LAB_CANDIDATE


class TestGainzAlgoBasic:
    """Basic functionality tests."""
    
    def test_initialization(self):
        """Test algo initializes with correct defaults."""
        algo = GainzAlgo()
        assert algo.ema_fast == 9
        assert algo.ema_slow == 21
        assert algo.risk_pct == 0.01
        assert algo.position is None
        assert algo.trades == []
    
    def test_custom_parameters(self):
        """Test algo accepts custom parameters."""
        algo = GainzAlgo(ema_fast=5, ema_slow=15, risk_pct=0.02)
        assert algo.ema_fast == 5
        assert algo.ema_slow == 15
        assert algo.risk_pct == 0.02
    
    def test_bullish_candle_detection(self):
        """Test bullish candle detection."""
        algo = GainzAlgo()
        candle = Candle(
            timestamp="2026-08-20",
            open=100.0,
            high=105.0,
            low=99.0,
            close=104.0,
            volume=1000
        )
        assert algo._is_bullish_candle(candle) is True
        assert algo._is_bearish_candle(candle) is False
    
    def test_bearish_candle_detection(self):
        """Test bearish candle detection."""
        algo = GainzAlgo()
        candle = Candle(
            timestamp="2026-08-20",
            open=104.0,
            high=105.0,
            low=99.0,
            close=100.0,
            volume=1000
        )
        assert algo._is_bearish_candle(candle) is True
        assert algo._is_bullish_candle(candle) is False


class TestEMACalculation:
    """Tests for EMA calculation."""
    
    def test_first_ema_equals_price(self):
        """First EMA value should equal the price."""
        algo = GainzAlgo()
        ema = algo._calculate_ema(100.0, 9, None)
        assert ema == 100.0
    
    def test_ema_smoothing(self):
        """EMA should smooth prices appropriately."""
        algo = GainzAlgo()
        ema = algo._calculate_ema(110.0, 9, 100.0)
        # EMA = (price - prev_ema) * multiplier + prev_ema
        # multiplier = 2 / (9 + 1) = 0.2
        # EMA = (110 - 100) * 0.2 + 100 = 102
        assert ema == 102.0


class TestSignalGeneration:
    """Tests for signal generation."""
    
    def test_no_signal_without_enough_data(self):
        """Should return None without enough candles."""
        algo = GainzAlgo()
        candle = Candle(
            timestamp="2026-08-20",
            open=100.0,
            high=105.0,
            low=99.0,
            close=104.0,
            volume=1000
        )
        signal = algo.update(candle)
        assert signal is None
    
    def test_neutral_without_crossover(self):
        """Should detect NEUTRAL when no crossover."""
        algo = GainzAlgo()
        algo._prev_ema_fast = 100.0
        algo._prev_ema_slow = 95.0
        algo._ema_fast_val = 101.0
        algo._ema_slow_val = 96.0
        
        crossover = algo._detect_crossover()
        assert crossover == Signal.NEUTRAL


class TestPositionManagement:
    """Tests for position opening and closing."""
    
    def test_position_size_calculation(self):
        """Test position sizing based on risk."""
        algo = GainzAlgo(risk_pct=0.01)
        # Risk 1% of 10000 = 100
        # Risk per unit = |100 - 95| = 5
        # Size = 100 / 5 = 20 units
        size = algo.calculate_position_size(10000, 100.0, 95.0)
        assert size == 20.0
    
    def test_zero_risk_distance_returns_zero_size(self):
        """Position size should be 0 if entry equals stop."""
        algo = GainzAlgo()
        size = algo.calculate_position_size(10000, 100.0, 100.0)
        assert size == 0


class TestTradeStatistics:
    """Tests for trade statistics."""
    
    def test_empty_stats(self):
        """Stats should handle no trades."""
        algo = GainzAlgo()
        stats = algo.get_stats()
        assert stats["total_trades"] == 0
        assert stats["win_rate"] == 0
        assert stats["avg_pnl"] == 0


class TestLabCandidate:
    """Tests for lab candidate metadata."""
    
    def test_candidate_registration(self):
        """Verify pre-registration metadata."""
        assert LAB_CANDIDATE["id"] == "LAB_001"
        assert LAB_CANDIDATE["name"] == "GainzAlgo"
        assert LAB_CANDIDATE["prediction"] == "SUSPENDE T1"
        assert LAB_CANDIDATE["harness"] == "#13"
        assert LAB_CANDIDATE["tier"] == "T1"
    
    def test_prediction_exists(self):
        """Ensure prediction is registered before running."""
        assert "prediction" in LAB_CANDIDATE
        assert LAB_CANDIDATE["prediction"] in ["SUSPENDE T1", "PASA T1", "PASA T2"]
