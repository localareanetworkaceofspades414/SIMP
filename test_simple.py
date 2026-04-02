#!/usr/bin/env python3
import asyncio
import sys
sys.path.insert(0, '/sessions/fervent-elegant-johnson/projects/simp')

from simp.integrations.kashclaw_shim import KashClawSimpAgent
from simp.organs.spot_trading_organ import SpotTradingOrgan

async def test():
    organ = SpotTradingOrgan(organ_id="spot:001", initial_balance=10000.0)
    agent = KashClawSimpAgent(organs={"spot:001": organ})
    
    params = {
        "organ_id": "spot:001",
        "asset_pair": "SOL/USDC",
        "side": "BUY",
        "quantity": 100,
        "price": 150.0,
        "slippage_tolerance": 0.01,
        "intent_id": "intent:001"
    }
    
    print("Executing trade...")
    result = await agent.handle_trade(params)
    print(f"Result status: {result.get('status')}")
    if result.get('status') == 'error':
        print(f"Error: {result.get('error_message')}")
    else:
        print(f"Execution result: {result.get('execution')}")

asyncio.run(test())
