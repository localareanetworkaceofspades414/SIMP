"""SIMP Integration Modules

Provides integration layers for external systems like KashClaw trading organs,
Kloutbot code generation, and quantumArb arbitrage trading.
"""

from simp.integrations.trading_organ import (
    TradingOrgan,
    TradeExecution,
    OrganExecutionResult,
    OrganType,
    ExecutionStatus
)
from simp.integrations.kashclaw_shim import (
    KashClawSimpAgent,
    KashClawRegistry,
    get_registry
)

__all__ = [
    "TradingOrgan",
    "TradeExecution",
    "OrganExecutionResult",
    "OrganType",
    "ExecutionStatus",
    "KashClawSimpAgent",
    "KashClawRegistry",
    "get_registry"
]
