"""KashClaw Trading Organs

Modular trading components that implement specific strategies.
Each organ can be wrapped as a SIMP agent for protocol communication.
"""

from simp.organs.spot_trading_organ import SpotTradingOrgan

__all__ = ["SpotTradingOrgan"]
