"""
#17: Micro Book 500€
====================

Libro de trading micro para validación con capital mínimo.
Nace con sizing S1-4 (position sizing por tiers).

Contexto: Si los gates no cayeron antes del 25 de agosto,
este libro se activa para demostrar edge con capital real mínimo.

Capital inicial: 500€
Sizing: S1-4 (escalonado)
"""

from dataclasses import dataclass
from enum import Enum
from typing import Optional, Dict, List
from decimal import Decimal, ROUND_DOWN
import logging


logger = logging.getLogger(__name__)


class SizingTier(Enum):
    """Position sizing tiers for micro book."""
    S1 = "S1"  # Mínimo - 1% risk
    S2 = "S2"  # Conservador - 1.5% risk
    S3 = "S3"  # Normal - 2% risk
    S4 = "S4"  # Máximo - 2.5% risk


@dataclass
class SizingRule:
    """Configuration for a sizing tier."""
    tier: SizingTier
    risk_pct: float
    max_position_pct: float  # Max % of portfolio in single position
    description: str


# S1-4 Sizing Configuration
SIZING_CONFIG: Dict[SizingTier, SizingRule] = {
    SizingTier.S1: SizingRule(
        tier=SizingTier.S1,
        risk_pct=0.01,  # 1% risk per trade
        max_position_pct=0.10,  # Max 10% in one position
        description="Tier mínimo: Para primeros trades o alta incertidumbre"
    ),
    SizingTier.S2: SizingRule(
        tier=SizingTier.S2,
        risk_pct=0.015,  # 1.5% risk per trade
        max_position_pct=0.15,  # Max 15% in one position
        description="Tier conservador: Señal clara pero sin track record"
    ),
    SizingTier.S3: SizingRule(
        tier=SizingTier.S3,
        risk_pct=0.02,  # 2% risk per trade
        max_position_pct=0.20,  # Max 20% in one position
        description="Tier normal: Señal clara con track record positivo"
    ),
    SizingTier.S4: SizingRule(
        tier=SizingTier.S4,
        risk_pct=0.025,  # 2.5% risk per trade
        max_position_pct=0.25,  # Max 25% in one position
        description="Tier máximo: Alta convicción con edge demostrado"
    ),
}


@dataclass
class Position:
    """A position in the micro book."""
    symbol: str
    entry_price: Decimal
    shares: Decimal
    stop_loss: Decimal
    tier: SizingTier
    entry_date: str
    cost_basis: Decimal
    
    @property
    def risk_amount(self) -> Decimal:
        """Amount at risk if stop loss hits."""
        return self.shares * (self.entry_price - self.stop_loss)


@dataclass
class Trade:
    """A completed trade."""
    symbol: str
    entry_price: Decimal
    exit_price: Decimal
    shares: Decimal
    entry_date: str
    exit_date: str
    pnl: Decimal
    pnl_pct: Decimal
    exit_reason: str
    tier: SizingTier


class MicroBook:
    """
    Micro Book de 500€ con sizing S1-4.
    
    Reglas del estado absorbente aplicadas en cada umbral:
    - Drawdown > 10%: Bajar a S1 obligatorio
    - Drawdown > 15%: Pausa y revisión
    - 3 pérdidas consecutivas: Bajar un tier
    - 3 ganancias consecutivas: Subir un tier (máx S4)
    
    El libro comienza en S2 (conservador) hasta demostrar edge.
    """
    
    INITIAL_CAPITAL = Decimal("500.00")
    MAX_DRAWDOWN_SOFT = Decimal("0.10")  # 10% - força S1
    MAX_DRAWDOWN_HARD = Decimal("0.15")  # 15% - pausa
    CONSECUTIVE_THRESHOLD = 3  # Trades para ajuste de tier
    
    def __init__(self, capital: Optional[Decimal] = None):
        self.initial_capital = capital or self.INITIAL_CAPITAL
        self.cash = self.initial_capital
        self.positions: Dict[str, Position] = {}
        self.trades: List[Trade] = []
        self.current_tier = SizingTier.S2  # Start conservative
        self._consecutive_wins = 0
        self._consecutive_losses = 0
        self._peak_equity = self.initial_capital
        self._paused = False
    
    @property
    def equity(self) -> Decimal:
        """Current total equity (cash + positions at cost)."""
        positions_value = sum(p.cost_basis for p in self.positions.values())
        return self.cash + positions_value
    
    @property
    def drawdown(self) -> Decimal:
        """Current drawdown from peak."""
        if self._peak_equity == 0:
            return Decimal("0")
        return (self._peak_equity - self.equity) / self._peak_equity
    
    def _update_peak(self) -> None:
        """Update peak equity if new high."""
        if self.equity > self._peak_equity:
            self._peak_equity = self.equity
    
    def _check_drawdown_rules(self) -> None:
        """Apply estado absorbente rules based on drawdown."""
        if self.drawdown >= self.MAX_DRAWDOWN_HARD:
            self._paused = True
            logger.warning(f"PAUSA: Drawdown {self.drawdown:.1%} >= {self.MAX_DRAWDOWN_HARD:.0%}")
        elif self.drawdown >= self.MAX_DRAWDOWN_SOFT:
            if self.current_tier != SizingTier.S1:
                logger.warning(f"Drawdown {self.drawdown:.1%}: Forzando S1")
                self.current_tier = SizingTier.S1
    
    def _adjust_tier_on_streak(self, win: bool) -> None:
        """Adjust tier based on consecutive wins/losses."""
        if win:
            self._consecutive_wins += 1
            self._consecutive_losses = 0
            if self._consecutive_wins >= self.CONSECUTIVE_THRESHOLD:
                self._consecutive_wins = 0
                self._tier_up()
        else:
            self._consecutive_losses += 1
            self._consecutive_wins = 0
            if self._consecutive_losses >= self.CONSECUTIVE_THRESHOLD:
                self._consecutive_losses = 0
                self._tier_down()
    
    def _tier_up(self) -> None:
        """Move up one tier (max S4)."""
        tiers = list(SizingTier)
        current_idx = tiers.index(self.current_tier)
        if current_idx < len(tiers) - 1:
            self.current_tier = tiers[current_idx + 1]
            logger.info(f"Tier up: {self.current_tier.value}")
    
    def _tier_down(self) -> None:
        """Move down one tier (min S1)."""
        tiers = list(SizingTier)
        current_idx = tiers.index(self.current_tier)
        if current_idx > 0:
            self.current_tier = tiers[current_idx - 1]
            logger.info(f"Tier down: {self.current_tier.value}")
    
    def calculate_position_size(
        self,
        entry_price: Decimal,
        stop_loss: Decimal,
        tier_override: Optional[SizingTier] = None,
    ) -> Decimal:
        """
        Calculate position size based on current tier and risk.
        
        Args:
            entry_price: Planned entry price
            stop_loss: Planned stop loss price
            tier_override: Override current tier (optional)
        
        Returns:
            Number of shares to buy (rounded down)
        """
        if self._paused:
            logger.warning("Book pausado - no se permiten nuevas posiciones")
            return Decimal("0")
        
        tier = tier_override or self.current_tier
        rule = SIZING_CONFIG[tier]
        
        risk_per_share = abs(entry_price - stop_loss)
        if risk_per_share == 0:
            return Decimal("0")
        
        risk_amount = self.equity * Decimal(str(rule.risk_pct))
        shares = (risk_amount / risk_per_share).quantize(Decimal("1"), rounding=ROUND_DOWN)
        
        max_position_value = self.equity * Decimal(str(rule.max_position_pct))
        max_shares = (max_position_value / entry_price).quantize(Decimal("1"), rounding=ROUND_DOWN)
        
        if self.cash < shares * entry_price:
            shares = (self.cash / entry_price).quantize(Decimal("1"), rounding=ROUND_DOWN)
        
        return min(shares, max_shares)
    
    def open_position(
        self,
        symbol: str,
        entry_price: Decimal,
        stop_loss: Decimal,
        entry_date: str,
        tier_override: Optional[SizingTier] = None,
    ) -> Optional[Position]:
        """Open a new position."""
        if self._paused:
            logger.warning("Book pausado")
            return None
        
        if symbol in self.positions:
            logger.warning(f"Ya existe posición en {symbol}")
            return None
        
        shares = self.calculate_position_size(entry_price, stop_loss, tier_override)
        if shares <= 0:
            logger.warning("Position size es 0")
            return None
        
        cost = shares * entry_price
        if cost > self.cash:
            logger.warning("Fondos insuficientes")
            return None
        
        tier = tier_override or self.current_tier
        position = Position(
            symbol=symbol,
            entry_price=entry_price,
            shares=shares,
            stop_loss=stop_loss,
            tier=tier,
            entry_date=entry_date,
            cost_basis=cost,
        )
        
        self.cash -= cost
        self.positions[symbol] = position
        
        logger.info(f"Abierta posición: {shares} {symbol} @ {entry_price} (tier {tier.value})")
        return position
    
    def close_position(
        self,
        symbol: str,
        exit_price: Decimal,
        exit_date: str,
        exit_reason: str = "manual",
    ) -> Optional[Trade]:
        """Close an existing position."""
        if symbol not in self.positions:
            logger.warning(f"No existe posición en {symbol}")
            return None
        
        position = self.positions.pop(symbol)
        proceeds = position.shares * exit_price
        pnl = proceeds - position.cost_basis
        pnl_pct = pnl / position.cost_basis if position.cost_basis > 0 else Decimal("0")
        
        trade = Trade(
            symbol=symbol,
            entry_price=position.entry_price,
            exit_price=exit_price,
            shares=position.shares,
            entry_date=position.entry_date,
            exit_date=exit_date,
            pnl=pnl,
            pnl_pct=pnl_pct,
            exit_reason=exit_reason,
            tier=position.tier,
        )
        
        self.trades.append(trade)
        self.cash += proceeds
        
        self._update_peak()
        self._adjust_tier_on_streak(pnl > 0)
        self._check_drawdown_rules()
        
        logger.info(f"Cerrada posición: {symbol} @ {exit_price}, PnL: {pnl:.2f}€ ({pnl_pct:.1%})")
        return trade
    
    def get_stats(self) -> Dict:
        """Get book statistics."""
        if not self.trades:
            return {
                "total_trades": 0,
                "equity": float(self.equity),
                "drawdown": float(self.drawdown),
                "current_tier": self.current_tier.value,
                "paused": self._paused,
            }
        
        wins = [t for t in self.trades if t.pnl > 0]
        total_pnl = sum(t.pnl for t in self.trades)
        
        return {
            "total_trades": len(self.trades),
            "wins": len(wins),
            "win_rate": len(wins) / len(self.trades),
            "total_pnl": float(total_pnl),
            "total_pnl_pct": float(total_pnl / self.initial_capital),
            "equity": float(self.equity),
            "drawdown": float(self.drawdown),
            "current_tier": self.current_tier.value,
            "consecutive_wins": self._consecutive_wins,
            "consecutive_losses": self._consecutive_losses,
            "paused": self._paused,
        }


MICRO_BOOK_CONFIG = {
    "id": "#17",
    "name": "Micro Book 500€",
    "initial_capital": 500,
    "currency": "EUR",
    "sizing": "S1-4",
    "created": "2026-08-20",
    "status": "active" if True else "pending",  # Gates check
    "rules": {
        "soft_drawdown": "10%",
        "hard_drawdown": "15%",
        "consecutive_adjustment": 3,
        "starting_tier": "S2",
    },
}
