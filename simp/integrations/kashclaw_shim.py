"""
KashClaw SIMP Integration Shim

This module provides the integration layer between KashClaw trading organs
and the SIMP protocol. It wraps trading organs as SIMP agents, enabling
them to communicate via standardized SIMP intents and responses.

The shim handles:
- Intent routing to appropriate organs
- Parameter validation and transformation
- Result serialization for SIMP responses
- Error handling and recovery
- Execution tracking and audit logging
"""

import asyncio
import uuid
from datetime import datetime
from typing import Dict, Any, List, Optional, Callable
import json

from simp.agent import SimpAgent
from simp.intent import Intent, SimpResponse
from simp.integrations.trading_organ import (
    TradingOrgan, OrganType, OrganExecutionResult, ExecutionStatus
)


class KashClawSimpAgent(SimpAgent):
    """
    SIMP Agent wrapper for KashClaw trading organs.

    This agent acts as a gateway between the SIMP protocol and trading organs.
    When it receives a trade intent, it:
    1. Routes to the appropriate organ
    2. Validates parameters
    3. Executes the trade
    4. Returns results as a SIMP response
    """

    def __init__(
        self,
        agent_id: str = "kashclaw:agent",
        organization: str = "kashclaw.trading",
        organs: Optional[Dict[str, TradingOrgan]] = None
    ):
        """
        Initialize KashClaw SIMP Agent.

        Args:
            agent_id: Unique identifier for this agent
            organization: Organization namespace
            organs: Dictionary of organ_id -> TradingOrgan instance
        """
        super().__init__(agent_id, organization)
        self.organs: Dict[str, TradingOrgan] = organs or {}
        self.execution_log: List[Dict[str, Any]] = []

        # Register intent handlers
        self.register_handler("trade", self.handle_trade)
        self.register_handler("validate_trade", self.handle_validate_trade)
        self.register_handler("organ_status", self.handle_organ_status)
        self.register_handler("execution_history", self.handle_execution_history)

    def register_organ(self, organ: TradingOrgan):
        """
        Register a trading organ with this agent.

        Args:
            organ: TradingOrgan instance to register
        """
        self.organs[organ.organ_id] = organ
        print(f"✅ Registered organ: {organ.organ_id} ({organ.organ_type.value})")

    async def handle_trade(self, params: Dict[str, Any]) -> Dict[str, Any]:
        """
        Execute a trading intent.

        Intent parameters:
        {
            "organ_id": "spot:001",              # Which organ to use
            "asset_pair": "SOL/USDC",            # What to trade
            "side": "BUY" | "SELL",              # Buy or sell
            "quantity": 10.5,                    # How much
            "price": 150.0,                      # Optional: limit price
            "slippage_tolerance": 0.01,          # Optional: max slippage
            "strategy_params": {...}             # Organ-specific params
        }
        """
        try:
            # Extract parameters
            organ_id = params.get("organ_id")
            if not organ_id:
                return {
                    "status": "error",
                    "error_code": "MISSING_ORGAN_ID",
                    "error_message": "organ_id is required"
                }

            # Find organ
            if organ_id not in self.organs:
                return {
                    "status": "error",
                    "error_code": "ORGAN_NOT_FOUND",
                    "error_message": f"Organ '{organ_id}' not registered"
                }

            organ = self.organs[organ_id]

            # Validate parameters
            is_valid = await organ.validate_params(params)
            if not is_valid:
                return {
                    "status": "error",
                    "error_code": "INVALID_PARAMS",
                    "error_message": f"Invalid parameters for {organ.organ_type.value}"
                }

            # Execute trade
            intent_id = params.get("intent_id", str(uuid.uuid4()))
            result: OrganExecutionResult = await organ.execute(params, intent_id)

            # Log execution
            await self._log_execution(result)

            # Return standardized result
            return {
                "status": "success",
                "execution": result.to_dict(),
                "timestamp": datetime.utcnow().isoformat()
            }

        except Exception as e:
            return {
                "status": "error",
                "error_code": "EXECUTION_FAILED",
                "error_message": str(e)
            }

    async def handle_validate_trade(self, params: Dict[str, Any]) -> Dict[str, Any]:
        """
        Validate trade parameters without executing.

        Returns validation status and any warnings.
        """
        try:
            organ_id = params.get("organ_id")
            if not organ_id or organ_id not in self.organs:
                return {
                    "valid": False,
                    "error": f"Organ '{organ_id}' not found"
                }

            organ = self.organs[organ_id]
            is_valid = await organ.validate_params(params)

            return {
                "valid": is_valid,
                "organ_id": organ_id,
                "organ_type": organ.organ_type.value,
                "timestamp": datetime.utcnow().isoformat()
            }
        except Exception as e:
            return {
                "valid": False,
                "error": str(e)
            }

    async def handle_organ_status(self, params: Dict[str, Any]) -> Dict[str, Any]:
        """
        Get status of one or all organs.

        If organ_id is provided, returns status of that organ.
        Otherwise returns status of all registered organs.
        """
        try:
            organ_id = params.get("organ_id")

            if organ_id:
                # Single organ status
                if organ_id not in self.organs:
                    return {
                        "status": "error",
                        "error": f"Organ '{organ_id}' not found"
                    }
                organ = self.organs[organ_id]
                organ_status = await organ.get_status()
                return {
                    "organ_id": organ_id,
                    "organ_type": organ.organ_type.value,
                    "status": organ_status
                }
            else:
                # All organs status
                statuses = {}
                for oid, organ in self.organs.items():
                    organ_status = await organ.get_status()
                    statuses[oid] = {
                        "organ_type": organ.organ_type.value,
                        "status": organ_status
                    }
                return {
                    "total_organs": len(self.organs),
                    "organs": statuses
                }

        except Exception as e:
            return {
                "status": "error",
                "error": str(e)
            }

    async def handle_execution_history(self, params: Dict[str, Any]) -> Dict[str, Any]:
        """
        Retrieve execution history.

        Optional parameters:
        - organ_id: Get history for specific organ
        - limit: Maximum number of records to return
        - offset: Skip this many records
        """
        try:
            organ_id = params.get("organ_id")
            limit = params.get("limit", 100)
            offset = params.get("offset", 0)

            if organ_id:
                # History for single organ
                if organ_id not in self.organs:
                    return {
                        "error": f"Organ '{organ_id}' not found"
                    }
                organ = self.organs[organ_id]
                history = organ.get_execution_history()
            else:
                # Execution log from this agent
                history = self.execution_log

            # Apply limit and offset
            sliced = history[offset:offset + limit]

            return {
                "total_records": len(history),
                "returned": len(sliced),
                "offset": offset,
                "limit": limit,
                "history": [
                    e.to_dict() if hasattr(e, 'to_dict') else e
                    for e in sliced
                ]
            }
        except Exception as e:
            return {
                "error": str(e)
            }

    async def _log_execution(self, result: OrganExecutionResult):
        """Log execution for audit trail"""
        self.execution_log.append(result.to_dict())
        if len(self.execution_log) > 1000:
            # Keep only recent 1000 executions in memory
            self.execution_log = self.execution_log[-1000:]


class KashClawRegistry:
    """
    Central registry for all KashClaw organs and agents.

    Manages organ registration, agent instantiation, and inter-organ communication.
    """

    def __init__(self):
        self.organs: Dict[str, TradingOrgan] = {}
        self.agents: Dict[str, KashClawSimpAgent] = {}

    def register_organ(self, organ: TradingOrgan):
        """Register a trading organ"""
        self.organs[organ.organ_id] = organ

    def register_agent(self, agent: KashClawSimpAgent):
        """Register a SIMP agent"""
        self.agents[agent.agent_id] = agent

    def create_agent(
        self,
        agent_id: str,
        organ_ids: Optional[List[str]] = None
    ) -> KashClawSimpAgent:
        """
        Create a new KashClaw SIMP agent with specified organs.

        Args:
            agent_id: Unique agent identifier
            organ_ids: List of organ IDs to attach to this agent

        Returns:
            KashClawSimpAgent instance
        """
        organ_dict = {}
        if organ_ids:
            for oid in organ_ids:
                if oid in self.organs:
                    organ_dict[oid] = self.organs[oid]

        agent = KashClawSimpAgent(agent_id=agent_id, organs=organ_dict)
        self.register_agent(agent)
        return agent

    def get_agent(self, agent_id: str) -> Optional[KashClawSimpAgent]:
        """Get agent by ID"""
        return self.agents.get(agent_id)

    def get_organ(self, organ_id: str) -> Optional[TradingOrgan]:
        """Get organ by ID"""
        return self.organs.get(organ_id)

    def list_organs(self) -> List[Dict[str, str]]:
        """List all registered organs"""
        return [
            {
                "organ_id": organ.organ_id,
                "organ_type": organ.organ_type.value
            }
            for organ in self.organs.values()
        ]

    def list_agents(self) -> List[Dict[str, Any]]:
        """List all registered agents"""
        return [
            {
                "agent_id": agent.agent_id,
                "organization": agent.organization,
                "attached_organs": len(agent.organs)
            }
            for agent in self.agents.values()
        ]


# Global registry instance
_global_registry = KashClawRegistry()


def get_registry() -> KashClawRegistry:
    """Get the global KashClaw registry"""
    return _global_registry
