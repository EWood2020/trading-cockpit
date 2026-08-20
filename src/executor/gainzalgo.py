"""
LAB_001: GainzAlgo - Candidato 1 del Laboratorio de Estrategias
==============================================================

Estrategia casera de EMA con confirmación de vela y TP/SL fijo 2:1.

PRE-REGISTRO (antes de correr):
- Predicción: SUSPENDE T1
- Fecha registro: 2026-08-20
- Arnés: #13 (T1 completo)

Componentes:
- EMA rápida (9 periodos) / EMA lenta (21 periodos)
- Confirmación de vela (cierre en dirección del cruce)
- Take Profit / Stop Loss ratio fijo 2:1
"""

from dataclasses import dataclass
from enum import Enum
from typing import Optional, List
import math


class Signal(Enum):
    LONG = "LONG"
    SHORT = "SHORT"
    NEUTRAL = "NEUTRAL"


@dataclass
class Candle:
    """OHLCV candle data."""
    timestamp: str
    open: float
    high: float
    low: float
    close: float
    volume: float


@dataclass
class Position:
    """Open position with TP/SL levels."""
    entry_price: float
    direction: Signal
    stop_loss: float
    take_profit: float
    size: float
    entry_time: str


@dataclass
class TradeResult:
    """Result of a closed trade."""
    entry_price: float
    exit_price: float
    direction: Signal
    pnl_pct: float
    exit_reason: str  # "TP", "SL", "SIGNAL"


class GainzAlgo:
    """
    GainzAlgo: EMA crossover with candle confirmation and fixed 2:1 R:R.
    
    Entry Rules:
    - LONG: EMA9 crosses above EMA21 AND current candle closes green
    - SHORT: EMA9 crosses below EMA21 AND current candle closes red
    
    Exit Rules:
    - Take Profit at 2R (twice the risk distance)
    - Stop Loss at 1R (ATR-based or fixed percentage)
    - Exit on opposite signal
    
    Risk Management:
    - Fixed 2:1 reward-to-risk ratio
    - Position sizing based on account risk % (default 1%)
    """
    
    def __init__(
        self,
        ema_fast: int = 9,
        ema_slow: int = 21,
        risk_pct: float = 0.01,  # 1% account risk per trade
        atr_period: int = 14,
        atr_multiplier: float = 1.5,  # SL = ATR * multiplier
    ):
        self.ema_fast = ema_fast
        self.ema_slow = ema_slow
        self.risk_pct = risk_pct
        self.atr_period = atr_period
        self.atr_multiplier = atr_multiplier
        
        self._prices: List[float] = []
        self._candles: List[Candle] = []
        self._ema_fast_val: Optional[float] = None
        self._ema_slow_val: Optional[float] = None
        self._prev_ema_fast: Optional[float] = None
        self._prev_ema_slow: Optional[float] = None
        self._atr: Optional[float] = None
        
        self.position: Optional[Position] = None
        self.trades: List[TradeResult] = []
    
    def _calculate_ema(self, price: float, period: int, prev_ema: Optional[float]) -> float:
        """Calculate EMA using the standard formula."""
        if prev_ema is None:
            return price
        multiplier = 2 / (period + 1)
        return (price - prev_ema) * multiplier + prev_ema
    
    def _calculate_atr(self, candles: List[Candle]) -> Optional[float]:
        """Calculate Average True Range."""
        if len(candles) < self.atr_period + 1:
            return None
        
        true_ranges = []
        for i in range(1, len(candles)):
            c = candles[i]
            prev_c = candles[i - 1]
            tr = max(
                c.high - c.low,
                abs(c.high - prev_c.close),
                abs(c.low - prev_c.close)
            )
            true_ranges.append(tr)
        
        if len(true_ranges) < self.atr_period:
            return None
        
        return sum(true_ranges[-self.atr_period:]) / self.atr_period
    
    def _is_bullish_candle(self, candle: Candle) -> bool:
        """Check if candle closed green (bullish)."""
        return candle.close > candle.open
    
    def _is_bearish_candle(self, candle: Candle) -> bool:
        """Check if candle closed red (bearish)."""
        return candle.close < candle.open
    
    def _detect_crossover(self) -> Signal:
        """Detect EMA crossover."""
        if (self._prev_ema_fast is None or self._prev_ema_slow is None or
            self._ema_fast_val is None or self._ema_slow_val is None):
            return Signal.NEUTRAL
        
        # Bullish crossover: fast crosses above slow
        if (self._prev_ema_fast <= self._prev_ema_slow and 
            self._ema_fast_val > self._ema_slow_val):
            return Signal.LONG
        
        # Bearish crossover: fast crosses below slow
        if (self._prev_ema_fast >= self._prev_ema_slow and 
            self._ema_fast_val < self._ema_slow_val):
            return Signal.SHORT
        
        return Signal.NEUTRAL
    
    def update(self, candle: Candle) -> Optional[Signal]:
        """
        Process a new candle and return a signal if entry conditions are met.
        
        Returns:
            Signal if entry/exit conditions are met, None otherwise
        """
        self._candles.append(candle)
        self._prices.append(candle.close)
        
        # Update EMAs
        self._prev_ema_fast = self._ema_fast_val
        self._prev_ema_slow = self._ema_slow_val
        self._ema_fast_val = self._calculate_ema(candle.close, self.ema_fast, self._ema_fast_val)
        self._ema_slow_val = self._calculate_ema(candle.close, self.ema_slow, self._ema_slow_val)
        
        # Update ATR
        self._atr = self._calculate_atr(self._candles)
        
        # Need enough data for signals
        if len(self._candles) < max(self.ema_slow, self.atr_period) + 1:
            return None
        
        crossover = self._detect_crossover()
        
        # Check for entry with candle confirmation
        if crossover == Signal.LONG and self._is_bullish_candle(candle):
            return Signal.LONG
        elif crossover == Signal.SHORT and self._is_bearish_candle(candle):
            return Signal.SHORT
        
        return None
    
    def calculate_position_size(self, account_equity: float, entry_price: float, stop_loss: float) -> float:
        """Calculate position size based on risk percentage."""
        risk_amount = account_equity * self.risk_pct
        risk_per_unit = abs(entry_price - stop_loss)
        if risk_per_unit == 0:
            return 0
        return risk_amount / risk_per_unit
    
    def open_position(
        self,
        signal: Signal,
        entry_price: float,
        account_equity: float,
        entry_time: str
    ) -> Position:
        """Open a new position with calculated TP/SL."""
        if self._atr is None:
            raise ValueError("ATR not calculated yet - need more data")
        
        risk_distance = self._atr * self.atr_multiplier
        
        if signal == Signal.LONG:
            stop_loss = entry_price - risk_distance
            take_profit = entry_price + (risk_distance * 2)  # 2:1 R:R
        else:  # SHORT
            stop_loss = entry_price + risk_distance
            take_profit = entry_price - (risk_distance * 2)  # 2:1 R:R
        
        size = self.calculate_position_size(account_equity, entry_price, stop_loss)
        
        self.position = Position(
            entry_price=entry_price,
            direction=signal,
            stop_loss=stop_loss,
            take_profit=take_profit,
            size=size,
            entry_time=entry_time
        )
        
        return self.position
    
    def check_exit(self, current_price: float, current_time: str) -> Optional[TradeResult]:
        """Check if position should be closed."""
        if self.position is None:
            return None
        
        exit_reason = None
        exit_price = current_price
        
        if self.position.direction == Signal.LONG:
            if current_price >= self.position.take_profit:
                exit_reason = "TP"
                exit_price = self.position.take_profit
            elif current_price <= self.position.stop_loss:
                exit_reason = "SL"
                exit_price = self.position.stop_loss
        else:  # SHORT
            if current_price <= self.position.take_profit:
                exit_reason = "TP"
                exit_price = self.position.take_profit
            elif current_price >= self.position.stop_loss:
                exit_reason = "SL"
                exit_price = self.position.stop_loss
        
        if exit_reason:
            return self._close_position(exit_price, exit_reason)
        
        return None
    
    def close_on_signal(self, new_signal: Signal, current_price: float) -> Optional[TradeResult]:
        """Close position if opposite signal is generated."""
        if self.position is None:
            return None
        
        if (self.position.direction == Signal.LONG and new_signal == Signal.SHORT) or \
           (self.position.direction == Signal.SHORT and new_signal == Signal.LONG):
            return self._close_position(current_price, "SIGNAL")
        
        return None
    
    def _close_position(self, exit_price: float, exit_reason: str) -> TradeResult:
        """Close the current position and record the trade."""
        if self.position is None:
            raise ValueError("No position to close")
        
        if self.position.direction == Signal.LONG:
            pnl_pct = (exit_price - self.position.entry_price) / self.position.entry_price
        else:
            pnl_pct = (self.position.entry_price - exit_price) / self.position.entry_price
        
        result = TradeResult(
            entry_price=self.position.entry_price,
            exit_price=exit_price,
            direction=self.position.direction,
            pnl_pct=pnl_pct,
            exit_reason=exit_reason
        )
        
        self.trades.append(result)
        self.position = None
        
        return result
    
    def get_stats(self) -> dict:
        """Get trading statistics."""
        if not self.trades:
            return {
                "total_trades": 0,
                "win_rate": 0,
                "avg_pnl": 0,
                "profit_factor": 0,
                "expectancy": 0,
            }
        
        wins = [t for t in self.trades if t.pnl_pct > 0]
        losses = [t for t in self.trades if t.pnl_pct < 0]
        
        total_wins = sum(t.pnl_pct for t in wins)
        total_losses = abs(sum(t.pnl_pct for t in losses))
        
        return {
            "total_trades": len(self.trades),
            "win_rate": len(wins) / len(self.trades) if self.trades else 0,
            "avg_pnl": sum(t.pnl_pct for t in self.trades) / len(self.trades),
            "profit_factor": total_wins / total_losses if total_losses > 0 else float('inf'),
            "expectancy": sum(t.pnl_pct for t in self.trades) / len(self.trades),
            "tp_exits": len([t for t in self.trades if t.exit_reason == "TP"]),
            "sl_exits": len([t for t in self.trades if t.exit_reason == "SL"]),
            "signal_exits": len([t for t in self.trades if t.exit_reason == "SIGNAL"]),
        }


# Pre-registro del candidato
LAB_CANDIDATE = {
    "id": "LAB_001",
    "name": "GainzAlgo",
    "type": "casero",
    "prediction": "SUSPENDE T1",
    "registered": "2026-08-20",
    "harness": "#13",
    "tier": "T1",
}
