#!/usr/bin/env python3
"""
KashClaw Trading Agent Example

Demonstrates how KashClaw trading organs integrate with SIMP protocol.
Shows the complete flow: Intent → Organ Execution → SIMP Response
"""

import asyncio
import sys
import json

# Add parent directory to path for imports
sys.path.insert(0, '/sessions/fervent-elegant-johnson')

from simp.integrations.kashclaw_shim import KashClawSimpAgent, get_registry
from simp.organs.spot_trading_organ import SpotTradingOrgan
from simp.intent import Intent


async def main():
    print("🚀 KashClaw Trading Agent - Day 2 Integration Demo")
    print("=" * 60)

    # Step 1: Create trading organs
    print("\n📦 Step 1: Creating trading organs...")
    spot_organ = SpotTradingOrgan(organ_id="spot:001", initial_balance=10000.0)
    print(f"✅ Created {spot_organ.organ_type.value} organ: {spot_organ.organ_id}")

    # Step 2: Create SIMP agent and register organ
    print("\n🔌 Step 2: Creating SIMP agent and registering organ...")
    agent = KashClawSimpAgent(
        agent_id="kashclaw:trading:001",
        organization="kashclaw.trading"
    )
    agent.register_organ(spot_organ)
    print(f"✅ SIMP Agent created: {agent.agent_id}")
    print(f"   Organization: {agent.organization}")

    # Step 3: Check initial status
    print("\n📊 Step 3: Checking organ status...")
    status_response = await agent.handle_organ_status({"organ_id": "spot:001"})
    initial_balance = status_response["status"]["available_capital"]
    print(f"✅ Organ Status:")
    print(f"   Balance: ${initial_balance:.2f}")
    print(f"   Trades: {status_response['status']['total_trades']}")

    # Step 4: Execute trades via SIMP intents
    print("\n💹 Step 4: Executing trades via SIMP intents...")
    print("-" * 60)

    # Trade 1: BUY
    print("\n📈 Trade 1: BUY 50 SOL at $150")
    buy_params = {
        "organ_id": "spot:001",
        "asset_pair": "SOL/USDC",
        "side": "BUY",
        "quantity": 50,
        "price": 150.0,
        "slippage_tolerance": 0.01,
        "intent_id": "intent:001"
    }

    buy_result = await agent.handle_trade(buy_params)

    if buy_result["status"] == "success" and buy_result["execution"]["status"] == "completed" and buy_result["execution"]["executions"]:
        execution = buy_result["execution"]["executions"][0]
        print(f"✅ Trade executed successfully!")
        print(f"   Trade ID: {execution['trade_id']}")
        print(f"   Quantity: {execution['quantity']} SOL")
        print(f"   Price: ${execution['price']:.2f}")
        print(f"   Fee: ${execution['fee']:.2f}")
        print(f"   Status: {execution['status']}")
    else:
        error_msg = buy_result.get('error_message') or buy_result.get('execution', {}).get('error_message', 'Unknown error')
        print(f"❌ Trade failed: {error_msg}")

    # Trade 2: SELL partial position
    print("\n📉 Trade 2: SELL 30 SOL at $155")
    sell_params = {
        "organ_id": "spot:001",
        "asset_pair": "SOL/USDC",
        "side": "SELL",
        "quantity": 30,
        "price": 155.0,
        "slippage_tolerance": 0.01,
        "intent_id": "intent:002"
    }

    sell_result = await agent.handle_trade(sell_params)

    if sell_result["status"] == "success" and sell_result["execution"]["status"] == "completed" and sell_result["execution"]["executions"]:
        execution = sell_result["execution"]["executions"][0]
        print(f"✅ Trade executed successfully!")
        print(f"   Trade ID: {execution['trade_id']}")
        print(f"   Quantity: {execution['quantity']} SOL")
        print(f"   Price: ${execution['price']:.2f}")
        print(f"   Fee: ${execution['fee']:.2f}")
        print(f"   Status: {execution['status']}")
    else:
        error_msg = sell_result.get('error_message') or sell_result.get('execution', {}).get('error_message', 'Unknown error')
        print(f"❌ Trade failed: {error_msg}")

    # Step 5: Check final status
    print("\n📊 Step 5: Final organ status...")
    status_response = await agent.handle_organ_status({"organ_id": "spot:001"})
    final_balance = status_response["status"]["available_capital"]
    positions = status_response["status"]["positions"]
    print(f"✅ Organ Status:")
    print(f"   Balance: ${final_balance:.2f}")
    print(f"   Positions: {positions}")
    print(f"   Trades: {status_response['status']['total_trades']}")
    print(f"   Balance Change: ${final_balance - initial_balance:+.2f}")

    # Step 6: Retrieve execution history
    print("\n📋 Step 6: Execution history...")
    history_response = await agent.handle_execution_history({
        "organ_id": "spot:001",
        "limit": 10
    })
    print(f"✅ Trade History ({history_response['total_records']} total):")
    for i, execution in enumerate(history_response["history"], 1):
        print(f"\n   Trade {i}:")
        print(f"   ID: {execution['trade_id']}")
        print(f"   Side: {execution['side']} {execution['quantity']} {execution['asset_pair']}")
        print(f"   Price: ${execution['price']:.2f}")
        print(f"   Time: {execution['execution_time']}")

    # Step 7: Validate trade parameters
    print("\n✔️  Step 7: Validating trade parameters...")
    valid_params = {
        "organ_id": "spot:001",
        "asset_pair": "ETH/USDC",
        "side": "BUY",
        "quantity": 50,
        "price": 3000
    }
    validation = await agent.handle_validate_trade(valid_params)
    print(f"✅ Validation result: {validation['valid']}")

    invalid_params = {
        "organ_id": "spot:001",
        "asset_pair": "BTC/USDC",
        "side": "INVALID",
        "quantity": -10,
        "price": 0
    }
    validation = await agent.handle_validate_trade(invalid_params)
    print(f"✅ Invalid params validation: {validation['valid']}")

    # Summary
    print("\n" + "=" * 60)
    print("🎉 KashClaw SIMP Integration Demo Complete!")
    print("=" * 60)
    print("\n✅ Demonstrated features:")
    print("   ✓ Organ creation and registration")
    print("   ✓ SIMP agent wrapping")
    print("   ✓ Intent-based trade execution")
    print("   ✓ Status monitoring")
    print("   ✓ Execution history")
    print("   ✓ Parameter validation")
    print("\n📌 Next steps (Day 3+):")
    print("   → Integrate Kloutbot Q_IntentCompiler")
    print("   → Connect quantumArb for real arbitrage")
    print("   → Add margin trading organ")
    print("   → Add liquidation organ")
    print("   → Production hardening")


if __name__ == "__main__":
    asyncio.run(main())
