"""
KashClaw Integration Tests

Tests for the SIMP-KashClaw integration layer including:
- Organ interface compliance
- SIMP agent wrapper functionality
- Trade execution flow
- Error handling and validation
"""

import asyncio
import pytest
import sys
import uuid
from datetime import datetime

sys.path.insert(0, '/sessions/fervent-elegant-johnson')

from simp.integrations.kashclaw_shim import (
    KashClawSimpAgent, KashClawRegistry, get_registry
)
from simp.organs.spot_trading_organ import SpotTradingOrgan
from simp.integrations.trading_organ import (
    OrganType, ExecutionStatus, TradingOrgan
)


class TestSpotTradingOrgan:
    """Test the spot trading organ implementation"""

    @pytest.fixture
    def organ(self):
        """Create a fresh organ for each test"""
        return SpotTradingOrgan(organ_id="test:spot:001", initial_balance=5000.0)

    @pytest.mark.asyncio
    async def test_organ_initialization(self, organ):
        """Test that organ initializes correctly"""
        assert organ.organ_id == "test:spot:001"
        assert organ.organ_type == OrganType.SPOT_TRADING
        assert organ.balance == 5000.0
        assert organ.total_trades == 0

    @pytest.mark.asyncio
    async def test_organ_buy_execution(self, organ):
        """Test executing a buy order"""
        params = {
            "asset_pair": "SOL/USDC",
            "side": "BUY",
            "quantity": 10.0,
            "price": 100.0,
            "slippage_tolerance": 0.01
        }

        result = await organ.execute(params, "test:intent:001")

        assert result.status == ExecutionStatus.COMPLETED
        assert len(result.executions) == 1
        assert result.executions[0].side == "BUY"
        assert result.executions[0].quantity == 10.0
        assert organ.balance < 5000.0  # Balance decreased
        assert "SOL" in organ.positions  # Position created

    @pytest.mark.asyncio
    async def test_organ_sell_execution(self, organ):
        """Test executing a sell order"""
        # First buy
        buy_params = {
            "asset_pair": "SOL/USDC",
            "side": "BUY",
            "quantity": 10.0,
            "price": 100.0,
            "slippage_tolerance": 0.01
        }
        await organ.execute(buy_params, "test:intent:001")

        # Then sell
        sell_params = {
            "asset_pair": "SOL/USDC",
            "side": "SELL",
            "quantity": 5.0,
            "price": 105.0,
            "slippage_tolerance": 0.01
        }

        result = await organ.execute(sell_params, "test:intent:002")

        assert result.status == ExecutionStatus.COMPLETED
        assert result.executions[0].side == "SELL"
        assert result.executions[0].quantity == 5.0
        assert organ.positions["SOL"] == 5.0  # Half of original position

    @pytest.mark.asyncio
    async def test_insufficient_balance(self, organ):
        """Test that buy fails with insufficient balance"""
        params = {
            "asset_pair": "BTC/USDC",
            "side": "BUY",
            "quantity": 1000.0,  # Too much
            "price": 100.0,
            "slippage_tolerance": 0.01
        }

        result = await organ.execute(params, "test:intent:001")

        assert result.status == ExecutionStatus.FAILED
        assert "Insufficient balance" in result.error_message

    @pytest.mark.asyncio
    async def test_insufficient_position(self, organ):
        """Test that sell fails with insufficient position"""
        params = {
            "asset_pair": "ETH/USDC",
            "side": "SELL",
            "quantity": 100.0,
            "price": 3000.0,
            "slippage_tolerance": 0.01
        }

        result = await organ.execute(params, "test:intent:001")

        assert result.status == ExecutionStatus.FAILED
        assert "Insufficient position" in result.error_message

    @pytest.mark.asyncio
    async def test_validate_params(self, organ):
        """Test parameter validation"""
        valid_params = {
            "asset_pair": "SOL/USDC",
            "side": "BUY",
            "quantity": 10.0,
            "price": 100.0
        }
        assert await organ.validate_params(valid_params) is True

        invalid_params = [
            {"side": "BUY", "quantity": 10.0, "price": 100.0},  # Missing asset_pair
            {"asset_pair": "SOL/USDC", "quantity": 10.0, "price": 100.0},  # Missing side
            {"asset_pair": "SOL/USDC", "side": "INVALID", "quantity": 10.0, "price": 100.0},
            {"asset_pair": "SOL/USDC", "side": "BUY", "quantity": -10.0, "price": 100.0},
            {"asset_pair": "SOL/USDC", "side": "BUY", "quantity": 10.0, "price": 0},
        ]

        for invalid in invalid_params:
            assert await organ.validate_params(invalid) is False

    @pytest.mark.asyncio
    async def test_organ_status(self, organ):
        """Test getting organ status"""
        status = await organ.get_status()

        assert status["is_operational"] is True
        assert status["available_capital"] == 5000.0
        assert status["total_trades"] == 0
        assert isinstance(status["positions"], dict)

    @pytest.mark.asyncio
    async def test_execution_history(self, organ):
        """Test execution history tracking"""
        # Execute a trade
        params = {
            "asset_pair": "SOL/USDC",
            "side": "BUY",
            "quantity": 5.0,
            "price": 100.0,
            "slippage_tolerance": 0.01
        }
        await organ.execute(params, "test:intent:001")

        # Check history
        history = organ.get_execution_history()
        assert len(history) == 1
        assert history[0].asset_pair == "SOL/USDC"


class TestKashClawSimpAgent:
    """Test the KashClaw SIMP agent wrapper"""

    @pytest.fixture
    def agent_with_organ(self):
        """Create agent with organ"""
        organ = SpotTradingOrgan(organ_id="spot:001", initial_balance=10000.0)
        agent = KashClawSimpAgent(organs={"spot:001": organ})
        return agent, organ

    @pytest.mark.asyncio
    async def test_agent_initialization(self, agent_with_organ):
        """Test agent initializes correctly"""
        agent, _ = agent_with_organ
        assert agent.agent_id == "kashclaw:agent"
        assert agent.organization == "kashclaw.trading"
        assert len(agent.organs) == 1

    @pytest.mark.asyncio
    async def test_register_organ(self):
        """Test registering an organ with agent"""
        agent = KashClawSimpAgent()
        organ = SpotTradingOrgan(organ_id="spot:002")

        agent.register_organ(organ)

        assert "spot:002" in agent.organs
        assert agent.organs["spot:002"] == organ

    @pytest.mark.asyncio
    async def test_trade_intent_successful(self, agent_with_organ):
        """Test handling a successful trade intent"""
        agent, organ = agent_with_organ

        params = {
            "organ_id": "spot:001",
            "asset_pair": "SOL/USDC",
            "side": "BUY",
            "quantity": 10.0,
            "price": 150.0,
            "slippage_tolerance": 0.01
        }

        result = await agent.handle_trade(params)

        assert result["status"] == "success"
        assert "execution" in result
        assert result["execution"]["status"] == ExecutionStatus.COMPLETED.value

    @pytest.mark.asyncio
    async def test_trade_intent_missing_organ(self, agent_with_organ):
        """Test trade intent with missing organ ID"""
        agent, _ = agent_with_organ

        params = {
            "asset_pair": "SOL/USDC",
            "side": "BUY",
            "quantity": 10.0,
            "price": 150.0
        }

        result = await agent.handle_trade(params)

        assert result["status"] == "error"
        assert result["error_code"] == "MISSING_ORGAN_ID"

    @pytest.mark.asyncio
    async def test_trade_intent_organ_not_found(self, agent_with_organ):
        """Test trade intent with non-existent organ"""
        agent, _ = agent_with_organ

        params = {
            "organ_id": "nonexistent:organ",
            "asset_pair": "SOL/USDC",
            "side": "BUY",
            "quantity": 10.0,
            "price": 150.0
        }

        result = await agent.handle_trade(params)

        assert result["status"] == "error"
        assert result["error_code"] == "ORGAN_NOT_FOUND"

    @pytest.mark.asyncio
    async def test_validate_trade_intent(self, agent_with_organ):
        """Test validating trade parameters"""
        agent, _ = agent_with_organ

        valid_params = {
            "organ_id": "spot:001",
            "asset_pair": "SOL/USDC",
            "side": "BUY",
            "quantity": 10.0,
            "price": 150.0
        }

        result = await agent.handle_validate_trade(valid_params)

        assert result["valid"] is True
        assert result["organ_id"] == "spot:001"

    @pytest.mark.asyncio
    async def test_organ_status_intent(self, agent_with_organ):
        """Test getting organ status via intent"""
        agent, _ = agent_with_organ

        result = await agent.handle_organ_status({"organ_id": "spot:001"})

        assert "organ_id" in result
        assert "status" in result
        assert result["status"]["is_operational"] is True

    @pytest.mark.asyncio
    async def test_execution_history_intent(self, agent_with_organ):
        """Test retrieving execution history via intent"""
        agent, organ = agent_with_organ

        # Execute a trade first
        params = {
            "organ_id": "spot:001",
            "asset_pair": "SOL/USDC",
            "side": "BUY",
            "quantity": 5.0,
            "price": 100.0
        }
        await agent.handle_trade(params)

        # Get history
        result = await agent.handle_execution_history({"organ_id": "spot:001"})

        assert result["total_records"] > 0
        assert len(result["history"]) > 0

    @pytest.mark.asyncio
    async def test_execution_logging(self, agent_with_organ):
        """Test that executions are logged in agent"""
        agent, _ = agent_with_organ

        # Execute trade
        params = {
            "organ_id": "spot:001",
            "asset_pair": "BTC/USDC",
            "side": "BUY",
            "quantity": 0.1,
            "price": 50000.0
        }
        await agent.handle_trade(params)

        # Check agent's execution log
        assert len(agent.execution_log) > 0


class TestKashClawRegistry:
    """Test the KashClaw registry"""

    @pytest.mark.asyncio
    async def test_registry_creation(self):
        """Test registry initialization"""
        registry = KashClawRegistry()
        assert len(registry.organs) == 0
        assert len(registry.agents) == 0

    @pytest.mark.asyncio
    async def test_register_organ(self):
        """Test registering organ with registry"""
        registry = KashClawRegistry()
        organ = SpotTradingOrgan(organ_id="spot:001")

        registry.register_organ(organ)

        assert "spot:001" in registry.organs

    @pytest.mark.asyncio
    async def test_create_agent(self):
        """Test creating agent with registry"""
        registry = KashClawRegistry()
        organ = SpotTradingOrgan(organ_id="spot:001")
        registry.register_organ(organ)

        agent = registry.create_agent("agent:001", organ_ids=["spot:001"])

        assert agent.agent_id == "agent:001"
        assert len(agent.organs) == 1

    @pytest.mark.asyncio
    async def test_list_organs(self):
        """Test listing organs"""
        registry = KashClawRegistry()
        organ1 = SpotTradingOrgan(organ_id="spot:001")
        organ2 = SpotTradingOrgan(organ_id="spot:002")

        registry.register_organ(organ1)
        registry.register_organ(organ2)

        organs_list = registry.list_organs()

        assert len(organs_list) == 2
        assert any(o["organ_id"] == "spot:001" for o in organs_list)

    @pytest.mark.asyncio
    async def test_list_agents(self):
        """Test listing agents"""
        registry = KashClawRegistry()
        organ = SpotTradingOrgan(organ_id="spot:001")
        registry.register_organ(organ)

        agent1 = registry.create_agent("agent:001", organ_ids=["spot:001"])
        agent2 = registry.create_agent("agent:002", organ_ids=["spot:001"])

        agents_list = registry.list_agents()

        assert len(agents_list) == 2


@pytest.mark.asyncio
async def test_integration_flow():
    """Test complete integration flow: Intent → Organ → Response"""
    # Setup
    organ = SpotTradingOrgan(organ_id="spot:001", initial_balance=10000.0)
    agent = KashClawSimpAgent(organs={"spot:001": organ})

    # Trade sequence
    trades = [
        {
            "organ_id": "spot:001",
            "asset_pair": "SOL/USDC",
            "side": "BUY",
            "quantity": 50.0,
            "price": 150.0,
            "slippage_tolerance": 0.01
        },
        {
            "organ_id": "spot:001",
            "asset_pair": "SOL/USDC",
            "side": "SELL",
            "quantity": 20.0,
            "price": 155.0,
            "slippage_tolerance": 0.01
        }
    ]

    for trade in trades:
        result = await agent.handle_trade(trade)
        assert result["status"] == "success"

    # Verify final state
    status = await agent.handle_organ_status({"organ_id": "spot:001"})
    assert status["status"]["total_trades"] == 2
    assert status["status"]["positions"]["SOL"] == 30.0  # 50 - 20

    # Verify history
    history = await agent.handle_execution_history({"organ_id": "spot:001"})
    assert history["total_records"] == 2


if __name__ == "__main__":
    # Run tests with: pytest tests/test_kashclaw_integration.py -v
    pytest.main([__file__, "-v"])
