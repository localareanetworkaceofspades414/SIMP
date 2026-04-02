"""
Trading Organ Interface for KashClaw Integration

This module defines the abstract interface that all trading organs must implement
to be compatible with the SIMP protocol. Organs are modular trading components that
can execute specific strategies (spot trading, margin trading, liquidation, etc.)

An organ takes trading parameters and returns execution results in a standardized format.
"""

from abc import ABC, abstractmethod
from dataclasses import dataclass
from enum import Enum
from typing import Dict, Any, Optional, List
from datetime import datetime


class OrganType(str, Enum):
    """Enumeration of KashClaw trading organ types"""
    SPOT_TRADING = "spot_trading"          # Buy/sell at market price
    MARGIN_TRADING = "margin_trading"      # Leveraged trading with collateral
    LIQUIDATION = "liquidation"            # Liquidate positions at risk
    ARBITRAGE = "arbitrage"                # Cross-exchange price differences
    SCALPING = "scalping"                  # High-frequency small trades
    HEDGING = "hedging"                    # Risk mitigation strategies
    ALGORITHMIC = "algorithmic"            # Complex multi-step strategies


class ExecutionStatus(str, Enum):
    """Execution status codes for trading operations"""
    PENDING = "pending"
    EXECUTING = "executing"
    COMPLETED = "completed"
    FAILED = "failed"
    CANCELLED = "cancelled"
    PARTIAL = "partial"


@dataclass
class TradeExecution:
    """Result of a single trade execution"""
    trade_id: str
    organ_type: OrganType
    asset_pair: str  # e.g., "SOL/USDC", "ETH/USD"
    side: str  # "BUY" or "SELL"
    quantity: float
    price: float
    execution_time: str  # ISO format timestamp
    status: ExecutionStatus
    fee: float = 0.0
    slippage: float = 0.0
    profit_loss: Optional[float] = None
    metadata: Dict[str, Any] = None

    def to_dict(self) -> dict:
        """Convert execution to dictionary"""
        return {
            "trade_id": self.trade_id,
            "organ_type": self.organ_type.value,
            "asset_pair": self.asset_pair,
            "side": self.side,
            "quantity": self.quantity,
            "price": self.price,
            "execution_time": self.execution_time,
            "status": self.status.value,
            "fee": self.fee,
            "slippage": self.slippage,
            "profit_loss": self.profit_loss,
            "metadata": self.metadata or {}
        }


@dataclass
class OrganExecutionResult:
    """Complete result from organ execution"""
    organ_id: str
    organ_type: OrganType
    intent_id: str  # Link back to originating SIMP intent
    status: ExecutionStatus
    executions: List[TradeExecution]
    total_pnl: float  # Total profit/loss
    timestamp: str  # ISO format
    error_message: Optional[str] = None
    gas_used: Optional[float] = None  # For blockchain transactions
    blockchain: Optional[str] = None  # e.g., "Solana", "Ethereum"

    def to_dict(self) -> dict:
        """Convert result to dictionary"""
        return {
            "organ_id": self.organ_id,
            "organ_type": self.organ_type.value,
            "intent_id": self.intent_id,
            "status": self.status.value,
            "executions": [e.to_dict() for e in self.executions],
            "total_pnl": self.total_pnl,
            "timestamp": self.timestamp,
            "error_message": self.error_message,
            "gas_used": self.gas_used,
            "blockchain": self.blockchain
        }


class TradingOrgan(ABC):
    """
    Abstract base class for all KashClaw trading organs.

    Organs are modular, composable trading components that implement
    specific trading strategies. Each organ:
    - Receives trading parameters via execute() method
    - Returns standardized TradeExecution results
    - Can be chained with other organs for complex strategies
    - Operates asynchronously and reports results via SIMP
    """

    def __init__(self, organ_id: str, organ_type: OrganType):
        """
        Initialize a trading organ.

        Args:
            organ_id: Unique identifier for this organ instance
            organ_type: Type of trading strategy this organ implements
        """
        self.organ_id = organ_id
        self.organ_type = organ_type
        self.execution_history: List[TradeExecution] = []

    @abstractmethod
    async def execute(
        self,
        params: Dict[str, Any],
        intent_id: str
    ) -> OrganExecutionResult:
        """
        Execute a trading operation with the given parameters.

        Args:
            params: Trading parameters specific to this organ:
                - asset_pair (str): e.g., "SOL/USDC"
                - side (str): "BUY" or "SELL"
                - quantity (float): Amount to trade
                - price (float, optional): Limit price
                - leverage (float, optional): For margin trading
                - slippage_tolerance (float, optional): Max acceptable slippage
                - Additional organ-specific parameters

            intent_id: The SIMP intent ID that triggered this execution

        Returns:
            OrganExecutionResult: Standardized result object

        Raises:
            ValueError: If parameters are invalid
            RuntimeError: If execution fails
        """
        pass

    @abstractmethod
    async def validate_params(self, params: Dict[str, Any]) -> bool:
        """
        Validate that parameters are acceptable for this organ.

        Args:
            params: Parameters to validate

        Returns:
            True if valid, False otherwise
        """
        pass

    @abstractmethod
    async def get_status(self) -> Dict[str, Any]:
        """
        Get current status of this organ.

        Returns:
            Dictionary containing:
                - is_operational (bool)
                - last_execution_time (str, ISO format)
                - total_trades (int)
                - current_positions (dict)
                - available_capital (float)
                - error_state (str, optional)
        """
        pass

    async def add_execution(self, execution: TradeExecution):
        """Record a successful execution"""
        self.execution_history.append(execution)

    def get_execution_history(self) -> List[TradeExecution]:
        """Get all recorded executions"""
        return self.execution_history.copy()
