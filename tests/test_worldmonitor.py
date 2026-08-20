"""Tests for worldmonitor context provider."""

import pytest
from unittest.mock import patch, MagicMock
from src.researcher.worldmonitor import (
    WorldMonitorClient,
    MacroContextProvider,
    MacroContext,
    MacroIndicator,
    WorldMonitorError,
    ATTRIBUTION,
    MEASUREMENT_CRITERIA,
)


class TestMacroIndicator:
    """Tests for MacroIndicator dataclass."""
    
    def test_create_indicator(self):
        """Test creating a macro indicator."""
        indicator = MacroIndicator(
            name="CPI YoY",
            value=3.2,
            previous_value=3.5,
            change_pct=-8.6,
            unit="%",
            region="US",
            last_updated="2026-08-20",
            trend="improving"
        )
        assert indicator.name == "CPI YoY"
        assert indicator.value == 3.2
        assert indicator.trend == "improving"


class TestMacroContext:
    """Tests for MacroContext dataclass."""
    
    def test_to_brief_section_basic(self):
        """Test brief section generation."""
        context = MacroContext(
            timestamp="2026-08-20T10:00:00Z",
            summary="Markets cautious ahead of Fed meeting.",
            risk_level="elevated",
        )
        section = context.to_brief_section()
        
        assert "## Macro Context" in section
        assert "ELEVATED" in section
        assert ATTRIBUTION in section
        assert "Markets cautious" in section
        assert "Not a trading signal" in section
    
    def test_to_brief_section_with_indicators(self):
        """Test brief section with indicators."""
        context = MacroContext(
            timestamp="2026-08-20T10:00:00Z",
            indicators=[
                MacroIndicator(
                    name="CPI YoY",
                    value=3.2,
                    previous_value=3.5,
                    change_pct=-8.6,
                    unit="%",
                    region="US",
                    last_updated="2026-08-20",
                    trend="improving"
                )
            ],
            risk_level="neutral",
        )
        section = context.to_brief_section()
        
        assert "CPI YoY" in section
        assert "3.2%" in section
        assert "📈" in section  # improving trend
    
    def test_attribution_always_present(self):
        """Attribution must always be included."""
        context = MacroContext(timestamp="2026-08-20")
        assert context.attribution == ATTRIBUTION


class TestWorldMonitorClient:
    """Tests for WorldMonitorClient."""
    
    def test_initialization(self):
        """Test client initialization."""
        client = WorldMonitorClient(api_key="test-key")
        assert client.api_key == "test-key"
        assert "worldmonitor.app" in client.base_url
    
    @patch('src.researcher.worldmonitor.urlopen')
    def test_get_macro_snapshot_success(self, mock_urlopen):
        """Test successful macro snapshot fetch."""
        mock_response = MagicMock()
        mock_response.read.return_value = b'{"timestamp": "2026-08-20", "indicators": [], "risk_level": "low"}'
        mock_response.__enter__ = MagicMock(return_value=mock_response)
        mock_response.__exit__ = MagicMock(return_value=False)
        mock_urlopen.return_value = mock_response
        
        client = WorldMonitorClient()
        context = client.get_macro_snapshot()
        
        assert isinstance(context, MacroContext)
        assert context.risk_level == "low"
    
    def test_get_macro_snapshot_failure_returns_empty_context(self):
        """Test graceful degradation on API failure."""
        client = WorldMonitorClient(base_url="https://invalid.example.com")
        context = client.get_macro_snapshot()
        
        assert isinstance(context, MacroContext)
        assert "unavailable" in context.summary.lower()


class TestMacroContextProvider:
    """Tests for MacroContextProvider."""
    
    def test_initialization(self):
        """Test provider initialization."""
        provider = MacroContextProvider()
        assert provider.client is not None
    
    def test_tracked_theses_empty_initially(self):
        """Test no theses tracked initially."""
        provider = MacroContextProvider()
        assert provider.get_tracked_theses() == {}
    
    @patch.object(WorldMonitorClient, 'get_macro_snapshot')
    def test_get_context_tracks_thesis(self, mock_snapshot):
        """Test that getting context tracks the thesis."""
        mock_snapshot.return_value = MacroContext(
            timestamp="2026-08-20",
            risk_level="neutral"
        )
        
        provider = MacroContextProvider()
        provider.get_context_for_thesis(symbol="AAPL", sector="technology")
        
        tracked = provider.get_tracked_theses()
        assert "AAPL" in tracked
        assert tracked["AAPL"]["risk_level"] == "neutral"


class TestMeasurementCriteria:
    """Tests for measurement criteria documentation."""
    
    def test_measurement_criteria_exists(self):
        """Ensure measurement criteria is documented."""
        assert "60 días" in MEASUREMENT_CRITERIA
        assert "sobreviven mejor al triage" in MEASUREMENT_CRITERIA
        assert "Si no mueve la aguja" in MEASUREMENT_CRITERIA
    
    def test_measurement_date_specified(self):
        """Ensure evaluation date is specified."""
        assert "2026-10-19" in MEASUREMENT_CRITERIA


class TestContextNeverSignal:
    """Tests ensuring context is never used as signal."""
    
    def test_brief_section_has_disclaimer(self):
        """Every brief section must have the disclaimer."""
        context = MacroContext(timestamp="2026-08-20")
        section = context.to_brief_section()
        assert "Not a trading signal" in section
    
    def test_no_buy_sell_recommendation_in_context(self):
        """Context should never contain buy/sell language."""
        context = MacroContext(
            timestamp="2026-08-20",
            summary="Test summary",
            risk_level="high"
        )
        section = context.to_brief_section().lower()
        
        forbidden_terms = ["buy", "sell", "long", "short", "recommend", "should trade"]
        for term in forbidden_terms:
            assert term not in section, f"Found forbidden term: {term}"
