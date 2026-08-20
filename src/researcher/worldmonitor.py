"""
worldmonitor como contexto - Fase 1
====================================

Integración con worldmonitor.app para obtener contexto macro en el brief.

LICENCIA: worldmonitor es AGPL. Solo consumimos la API hospedada.
NUNCA incorporar código de worldmonitor al repositorio.

PROPÓSITO: Contexto para tesis, JAMÁS señal directa.

MEDICIÓN: A 60 días, evaluar si las tesis con contexto macro sobreviven
mejor al triage. Si no mueve la aguja → fuera.

Attribution: Data provided by worldmonitor.app
"""

import json
import logging
from dataclasses import dataclass, field
from datetime import datetime, timedelta, timezone
from typing import Optional, Dict, List, Any
from urllib.request import Request, urlopen
from urllib.error import URLError, HTTPError


logger = logging.getLogger(__name__)

WORLDMONITOR_BASE_URL = "https://api.worldmonitor.app/v1"
ATTRIBUTION = "Macro context provided by worldmonitor.app"


@dataclass
class MacroIndicator:
    """A single macro indicator from worldmonitor."""
    name: str
    value: float
    previous_value: Optional[float]
    change_pct: Optional[float]
    unit: str
    region: str
    last_updated: str
    trend: str  # "improving", "deteriorating", "stable"


@dataclass
class MacroContext:
    """Macro context for thesis writing."""
    timestamp: str
    indicators: List[MacroIndicator] = field(default_factory=list)
    summary: str = ""
    risk_level: str = "neutral"  # "low", "neutral", "elevated", "high"
    key_events: List[str] = field(default_factory=list)
    attribution: str = ATTRIBUTION
    
    def to_brief_section(self) -> str:
        """Format as a brief section for thesis context."""
        lines = [
            "## Macro Context",
            f"_As of {self.timestamp} | {self.attribution}_",
            "",
            f"**Risk Environment**: {self.risk_level.upper()}",
            "",
        ]
        
        if self.summary:
            lines.extend([self.summary, ""])
        
        if self.indicators:
            lines.append("### Key Indicators")
            for ind in self.indicators:
                trend_icon = {"improving": "📈", "deteriorating": "📉", "stable": "➡️"}.get(ind.trend, "")
                change = f" ({ind.change_pct:+.1f}%)" if ind.change_pct is not None else ""
                lines.append(f"- **{ind.name}** ({ind.region}): {ind.value}{ind.unit}{change} {trend_icon}")
            lines.append("")
        
        if self.key_events:
            lines.append("### Upcoming Events")
            for event in self.key_events:
                lines.append(f"- {event}")
            lines.append("")
        
        lines.append("---")
        lines.append("_Context only. Not a trading signal._")
        
        return "\n".join(lines)


class WorldMonitorClient:
    """
    Client for worldmonitor.app API.
    
    IMPORTANT: This is a pure API consumer. We do not embed any worldmonitor
    code. The worldmonitor project is AGPL licensed - consuming their hosted
    API is permitted and does not trigger copyleft obligations.
    """
    
    def __init__(
        self,
        api_key: Optional[str] = None,
        base_url: str = WORLDMONITOR_BASE_URL,
        timeout: int = 30,
    ):
        self.api_key = api_key
        self.base_url = base_url.rstrip("/")
        self.timeout = timeout
        self._cache: Dict[str, Any] = {}
        self._cache_ttl = timedelta(hours=1)
    
    def _make_request(self, endpoint: str) -> Dict[str, Any]:
        """Make an API request to worldmonitor."""
        url = f"{self.base_url}/{endpoint.lstrip('/')}"
        
        headers = {
            "Accept": "application/json",
            "User-Agent": "TradingDesk/1.0 (context-consumer)",
        }
        if self.api_key:
            headers["Authorization"] = f"Bearer {self.api_key}"
        
        try:
            req = Request(url, headers=headers)
            with urlopen(req, timeout=self.timeout) as response:
                return json.loads(response.read().decode("utf-8"))
        except HTTPError as e:
            logger.error(f"worldmonitor API error: {e.code} - {e.reason}")
            raise WorldMonitorError(f"API request failed: {e.code}") from e
        except URLError as e:
            logger.error(f"worldmonitor connection error: {e.reason}")
            raise WorldMonitorError(f"Connection failed: {e.reason}") from e
        except json.JSONDecodeError as e:
            logger.error(f"worldmonitor response parse error: {e}")
            raise WorldMonitorError("Invalid response format") from e
    
    def get_macro_snapshot(self, regions: Optional[List[str]] = None) -> MacroContext:
        """
        Get current macro context snapshot.
        
        Args:
            regions: List of regions to include (e.g., ["US", "EU", "GLOBAL"])
                    If None, returns global indicators.
        
        Returns:
            MacroContext with current indicators and summary.
        """
        regions = regions or ["GLOBAL"]
        
        try:
            data = self._make_request("/macro/snapshot")
            return self._parse_snapshot(data, regions)
        except WorldMonitorError:
            logger.warning("Failed to fetch macro context, returning empty context")
            return MacroContext(
                timestamp=datetime.now(timezone.utc).isoformat(),
                summary="Macro context unavailable - worldmonitor API unreachable.",
            )
    
    def _parse_snapshot(self, data: Dict[str, Any], regions: List[str]) -> MacroContext:
        """Parse API response into MacroContext."""
        indicators = []
        
        for item in data.get("indicators", []):
            if item.get("region") not in regions and "GLOBAL" not in regions:
                continue
            
            prev = item.get("previous_value")
            current = item.get("value", 0)
            change = ((current - prev) / prev * 100) if prev and prev != 0 else None
            
            indicators.append(MacroIndicator(
                name=item.get("name", "Unknown"),
                value=current,
                previous_value=prev,
                change_pct=change,
                unit=item.get("unit", ""),
                region=item.get("region", "GLOBAL"),
                last_updated=item.get("updated_at", ""),
                trend=item.get("trend", "stable"),
            ))
        
        return MacroContext(
            timestamp=data.get("timestamp", datetime.now(timezone.utc).isoformat()),
            indicators=indicators,
            summary=data.get("summary", ""),
            risk_level=data.get("risk_level", "neutral"),
            key_events=data.get("events", []),
        )
    
    def get_calendar(self, days_ahead: int = 7) -> List[Dict[str, Any]]:
        """
        Get economic calendar events.
        
        Args:
            days_ahead: Number of days to look ahead.
        
        Returns:
            List of upcoming economic events.
        """
        try:
            return self._make_request(f"/calendar?days={days_ahead}").get("events", [])
        except WorldMonitorError:
            logger.warning("Failed to fetch calendar, returning empty list")
            return []


class WorldMonitorError(Exception):
    """Exception for worldmonitor API errors."""
    pass


class MacroContextProvider:
    """
    Provides macro context for thesis writing.
    
    This is the main interface for researchers to get macro context.
    It wraps the worldmonitor client with caching and formatting.
    
    Usage:
        provider = MacroContextProvider()
        context = provider.get_context_for_thesis(symbol="AAPL", sector="technology")
        brief_section = context.to_brief_section()
    """
    
    def __init__(self, api_key: Optional[str] = None):
        self.client = WorldMonitorClient(api_key=api_key)
        self._thesis_contexts: Dict[str, Dict] = {}
    
    def get_context_for_thesis(
        self,
        symbol: str,
        sector: Optional[str] = None,
        regions: Optional[List[str]] = None,
    ) -> MacroContext:
        """
        Get macro context relevant for a specific thesis.
        
        The context is tailored to the symbol/sector but NEVER provides
        a trading signal. It's purely informational context.
        
        Args:
            symbol: Stock/asset symbol the thesis is about
            sector: Sector classification (for relevant indicators)
            regions: Geographic regions of interest
        
        Returns:
            MacroContext for the brief
        """
        regions = regions or ["US", "GLOBAL"]
        context = self.client.get_macro_snapshot(regions)
        
        self._thesis_contexts[symbol] = {
            "timestamp": context.timestamp,
            "risk_level": context.risk_level,
            "indicator_count": len(context.indicators),
        }
        
        return context
    
    def get_tracked_theses(self) -> Dict[str, Dict]:
        """Get metadata about theses that received macro context."""
        return self._thesis_contexts.copy()


MEASUREMENT_CRITERIA = """
Medición a 60 días (desde 2026-08-20):
=====================================

Pregunta: ¿Las tesis con contexto macro sobreviven mejor al triage?

Grupos:
- Control: Tesis sin sección macro (antes de esta feature)
- Tratamiento: Tesis con sección macro (después de esta feature)

Métricas:
1. Tasa de supervivencia al triage (% que pasan la primera revisión)
2. Duración media en pipeline (días desde creación hasta cierre)
3. Ratio de tesis que llegaron a trade vs descartadas

Umbral de éxito:
- Tratamiento debe mostrar ≥15% mejora en supervivencia al triage
- O ≥10% mejora en ratio de conversión a trade

Si no mueve la aguja → fuera.

Fecha de evaluación: 2026-10-19 (60 días desde implementación)
"""
