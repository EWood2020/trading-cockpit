"""
Weekly Scoreboard Generator
===========================

Un generador, dos salidas:
1. Telegram scoreboard (lunes) - #5 punto 3
2. S2-8 weekly report

Nota: Al activar este sistema, retirar la revisión-interina del lunes de Claude.
Avisar al director para que borre la tarea programada.
"""

import json
from dataclasses import dataclass, field
from datetime import datetime, timedelta, timezone
from typing import List, Dict, Optional, Any
from enum import Enum


class OutputFormat(Enum):
    """Output formats for the weekly report."""
    TELEGRAM = "telegram"
    S2_8 = "s2_8"
    BOTH = "both"


@dataclass
class BookPerformance:
    """Performance metrics for a trading book."""
    book_name: str
    equity: float
    pnl_week: float
    pnl_week_pct: float
    alpha_vs_spy: float
    trades_week: int
    win_rate: float
    drawdown: float
    
    @property
    def beating_spy(self) -> bool:
        return self.alpha_vs_spy > 0


@dataclass
class WeeklyMetrics:
    """Aggregated weekly metrics."""
    week_start: str
    week_end: str
    books: List[BookPerformance] = field(default_factory=list)
    spy_return: float = 0.0
    total_pnl: float = 0.0
    total_trades: int = 0
    best_book: Optional[str] = None
    worst_book: Optional[str] = None
    pipeline_errors: int = 0
    ai_cost: float = 0.0


class WeeklyScoreboardGenerator:
    """
    Generates weekly reports in multiple formats.
    
    Single source of truth for:
    - Monday Telegram scoreboard (#5 punto 3)
    - S2-8 weekly workflow output
    
    Al usar este sistema:
    - Retirar la revisión-interina del lunes de Claude
    - Avisar al director para borrar tarea programada
    """
    
    def __init__(self, data_source: Optional[Any] = None):
        self.data_source = data_source
        self._cache: Dict[str, WeeklyMetrics] = {}
    
    def fetch_metrics(self, week_of: Optional[datetime] = None) -> WeeklyMetrics:
        """
        Fetch metrics for a specific week.
        
        Args:
            week_of: Any date in the target week. Defaults to current week.
        
        Returns:
            WeeklyMetrics for the specified week.
        """
        if week_of is None:
            week_of = datetime.now(timezone.utc)
        
        monday = week_of - timedelta(days=week_of.weekday())
        sunday = monday + timedelta(days=6)
        
        week_key = monday.strftime("%Y-%W")
        if week_key in self._cache:
            return self._cache[week_key]
        
        metrics = WeeklyMetrics(
            week_start=monday.strftime("%Y-%m-%d"),
            week_end=sunday.strftime("%Y-%m-%d"),
        )
        
        self._cache[week_key] = metrics
        return metrics
    
    def generate(
        self,
        metrics: WeeklyMetrics,
        output_format: OutputFormat = OutputFormat.BOTH,
    ) -> Dict[str, str]:
        """
        Generate reports in specified format(s).
        
        Args:
            metrics: The weekly metrics to report
            output_format: TELEGRAM, S2_8, or BOTH
        
        Returns:
            Dict with format name as key and report content as value.
        """
        results = {}
        
        if output_format in (OutputFormat.TELEGRAM, OutputFormat.BOTH):
            results["telegram"] = self._format_telegram(metrics)
        
        if output_format in (OutputFormat.S2_8, OutputFormat.BOTH):
            results["s2_8"] = self._format_s2_8(metrics)
        
        return results
    
    def _format_telegram(self, metrics: WeeklyMetrics) -> str:
        """Format for Telegram scoreboard (Monday notification)."""
        lines = [
            f"📊 *Scoreboard Semanal*",
            f"_{metrics.week_start} → {metrics.week_end}_",
            "",
        ]
        
        lines.append(f"💰 *P&L Total:* {metrics.total_pnl:+.0f}€")
        lines.append(f"📈 *S&P 500:* {metrics.spy_return:+.2f}%")
        lines.append("")
        
        if metrics.books:
            lines.append("*Por libro:*")
            for book in sorted(metrics.books, key=lambda b: -b.pnl_week):
                emoji = "🟢" if book.pnl_week >= 0 else "🔴"
                spy_status = "✓" if book.beating_spy else "✗"
                lines.append(
                    f"{emoji} {book.book_name}: {book.pnl_week:+.0f}€ "
                    f"({book.pnl_week_pct:+.1f}%) {spy_status}SPY"
                )
            lines.append("")
        
        lines.append(f"📉 *Max DD:* {max((b.drawdown for b in metrics.books), default=0):.1f}%")
        lines.append(f"🎯 *Trades:* {metrics.total_trades}")
        
        if metrics.pipeline_errors > 0:
            lines.append(f"⚠️ *Errores:* {metrics.pipeline_errors}")
        
        lines.append("")
        lines.append("_Generado automáticamente · [cockpit](https://...)_")
        
        return "\n".join(lines)
    
    def _format_s2_8(self, metrics: WeeklyMetrics) -> str:
        """Format for S2-8 weekly workflow output."""
        report = {
            "report_type": "S2-8_weekly",
            "generated_at": datetime.now(timezone.utc).isoformat(),
            "period": {
                "start": metrics.week_start,
                "end": metrics.week_end,
            },
            "summary": {
                "total_pnl_eur": metrics.total_pnl,
                "spy_return_pct": metrics.spy_return,
                "total_trades": metrics.total_trades,
                "best_book": metrics.best_book,
                "worst_book": metrics.worst_book,
            },
            "books": [
                {
                    "name": b.book_name,
                    "equity": b.equity,
                    "pnl_week": b.pnl_week,
                    "pnl_week_pct": b.pnl_week_pct,
                    "alpha_vs_spy": b.alpha_vs_spy,
                    "trades": b.trades_week,
                    "win_rate": b.win_rate,
                    "drawdown": b.drawdown,
                    "beating_spy": b.beating_spy,
                }
                for b in metrics.books
            ],
            "operations": {
                "pipeline_errors": metrics.pipeline_errors,
                "ai_cost_usd": metrics.ai_cost,
            },
        }
        
        return json.dumps(report, indent=2, ensure_ascii=False)


DEPRECATION_NOTE = """
AVISO DE DEPRECACIÓN
====================

Al activar este sistema de scoreboard unificado:

1. RETIRAR la revisión-interina del lunes de Claude
2. AVISAR al director para que borre la tarea programada
   (la automatización manual queda reemplazada por weekly.yml)

Este generador es ahora la única fuente de verdad para:
- Telegram scoreboard del lunes (#5 punto 3)
- S2-8 weekly report

Fecha de activación: 2026-08-20
"""
