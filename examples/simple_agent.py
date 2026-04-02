import asyncio
import sys
sys.path.insert(0, '..')

from simp import SimpAgent, Intent

class EchoAgent(SimpAgent):
    """Simple agent that echoes back messages"""

    def __init__(self):
        super().__init__("echo:agent", "simp.example")
        self.register_handler("echo", self.handle_echo)

    async def handle_echo(self, params: dict):
        """Echo handler"""
        message = params.get("message", "")
        return {
            "echo": message,
            "received_ok": True
        }

if __name__ == "__main__":
    print("🚀 Creating EchoAgent...")
    agent = EchoAgent()

    print("📝 Creating intent...")
    intent = agent.create_intent("echo", {"message": "Hello, SIMP!"})
    print(f"✅ Intent created: {intent.id}")

    print("\n⚙️ Handling intent...")
    response = asyncio.run(agent.handle_intent(intent))
    print(f"✅ Response: {response.to_json()}")

    print("\n🎉 SUCCESS - SIMP is working!")
