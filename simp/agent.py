import asyncio
from typing import Dict, Callable, Optional
from simp.intent import Intent, SimpResponse, Agent
from simp.crypto import SimpCrypto

class SimpAgent:
    """Base class for SIMP agents"""

    def __init__(self, agent_id: str, organization: str, private_key_pem: Optional[bytes] = None):
        self.agent_id = agent_id
        self.organization = organization
        self.intent_handlers: Dict[str, Callable] = {}

        # Load or generate keys
        if private_key_pem:
            self.private_key = SimpCrypto.load_private_key(private_key_pem)
        else:
            self.private_key, public_key = SimpCrypto.generate_keypair()

        # Get public key
        public_key_pem = SimpCrypto.public_key_to_pem(self.private_key.public_key()).decode()
        self.public_key_pem = public_key_pem

    def register_handler(self, intent_type: str, handler: Callable):
        """Register a handler for an intent type"""
        self.intent_handlers[intent_type] = handler

    async def handle_intent(self, intent: Intent) -> SimpResponse:
        """Process an incoming intent"""
        intent_type = intent.intent_type

        if intent_type not in self.intent_handlers:
            return SimpResponse(
                intent_id=intent.id,
                status="error",
                error_code="UNKNOWN_INTENT_TYPE",
                error_message=f"No handler for: {intent_type}"
            )

        try:
            handler = self.intent_handlers[intent_type]
            result = await handler(intent.params) if asyncio.iscoroutinefunction(handler) else handler(intent.params)
            return SimpResponse(
                intent_id=intent.id,
                status="success",
                data=result
            )
        except Exception as e:
            return SimpResponse(
                intent_id=intent.id,
                status="error",
                error_code="HANDLER_ERROR",
                error_message=str(e)
            )

    def create_intent(self, intent_type: str, params: Dict) -> Intent:
        """Create a signed intent"""
        agent = Agent(
            id=self.agent_id,
            organization=self.organization,
            public_key=self.public_key_pem
        )

        intent = Intent(
            source_agent=agent,
            intent_type=intent_type,
            params=params
        )

        # Sign it
        intent.signature = SimpCrypto.sign_intent(intent.to_dict(), self.private_key)
        return intent
