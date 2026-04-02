"""
Agent Manager: Spawns and manages SIMP agents as separate processes

Handles agent lifecycle, inter-process communication, and monitoring.
"""

import multiprocessing as mp
import subprocess
import time
import logging
from dataclasses import dataclass
from typing import Dict, Optional, Any, List, Callable
from datetime import datetime
import json
import signal
import os


@dataclass
class RemoteAgent:
    """Information about a remote agent"""
    agent_id: str
    agent_type: str
    process: Optional[mp.Process] = None
    port: int = 0
    pid: Optional[int] = None
    status: str = "stopped"  # stopped, starting, running, failed
    started_at: Optional[str] = None
    error_message: Optional[str] = None
    metrics: Dict[str, Any] = None

    def __post_init__(self):
        if self.metrics is None:
            self.metrics = {}

    def is_alive(self) -> bool:
        """Check if process is alive"""
        if self.process is None:
            return False
        return self.process.is_alive()


class AgentManager:
    """
    Manages SIMP agents as separate processes

    Spawns agents, monitors their health, and handles crashes.
    """

    def __init__(self, broker_config: Dict[str, Any] = None):
        """Initialize agent manager"""
        self.logger = logging.getLogger("SIMP.AgentManager")
        self.agents: Dict[str, RemoteAgent] = {}
        self.broker_config = broker_config or {}
        self.base_port = 5001  # Starting port for agents
        self.next_port = self.base_port

        self.logger.info("✅ Agent Manager initialized")

    def _get_next_port(self) -> int:
        """Get next available port"""
        port = self.next_port
        self.next_port += 1
        return port

    def spawn_agent(
        self,
        agent_id: str,
        agent_type: str,
        agent_class: str,  # e.g., "simp.agents.KloutbotAgent"
        agent_module: str,  # e.g., "simp.agents.kloutbot_agent"
        args: Optional[Dict[str, Any]] = None,
    ) -> Optional[RemoteAgent]:
        """
        Spawn an agent as a separate process

        Args:
            agent_id: Unique agent identifier
            agent_type: Type of agent (e.g., "grok", "vision")
            agent_class: Fully qualified class name
            agent_module: Module containing the agent
            args: Arguments to pass to agent constructor

        Returns:
            RemoteAgent instance, or None if spawn failed
        """
        if agent_id in self.agents:
            self.logger.error(f"❌ Agent '{agent_id}' already spawned")
            return None

        port = self._get_next_port()
        args = args or {}

        self.logger.info(
            f"🚀 Spawning agent: {agent_id} ({agent_type}) on port {port}"
        )

        # Create agent process
        remote_agent = RemoteAgent(
            agent_id=agent_id,
            agent_type=agent_type,
            port=port,
            status="starting",
            started_at=datetime.utcnow().isoformat(),
        )

        try:
            # Spawn process via subprocess for better isolation
            script = self._generate_agent_script(
                agent_id, agent_type, agent_class, agent_module, port, args
            )

            # Write script to temp file
            script_path = f"/tmp/simp_agent_{agent_id}_{port}.py"
            with open(script_path, "w") as f:
                f.write(script)

            # Spawn process
            process = mp.Process(
                target=self._run_agent_process,
                args=(script_path, agent_id, port),
                name=f"simp-{agent_type}-{agent_id}",
            )
            process.start()

            remote_agent.process = process
            remote_agent.pid = process.pid
            remote_agent.status = "running"

            self.agents[agent_id] = remote_agent

            self.logger.info(
                f"✅ Agent spawned: {agent_id} (PID: {process.pid}, Port: {port})"
            )

            return remote_agent

        except Exception as e:
            remote_agent.status = "failed"
            remote_agent.error_message = str(e)
            self.agents[agent_id] = remote_agent

            self.logger.error(f"❌ Failed to spawn agent '{agent_id}': {str(e)}")
            return None

    def _generate_agent_script(
        self,
        agent_id: str,
        agent_type: str,
        agent_class: str,
        agent_module: str,
        port: int,
        args: Dict[str, Any],
    ) -> str:
        """Generate Python script for agent process"""
        script = f'''
import sys
import logging
sys.path.insert(0, '/sessions/fervent-elegant-johnson/projects/simp')

from {agent_module} import {agent_class.split('.')[-1]}
from simp.server.agent_client import SimpAgentClient

# Setup logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger("Agent.{agent_id}")

logger.info("🚀 Agent {{agent_id}} starting on port {{port}}")

try:
    # Create agent instance
    agent = {agent_class.split('.')[-1]}(
        agent_id="{agent_id}",
        **{repr(args)}
    )
    logger.info("✅ Agent instance created")

    # Create SIMP client
    client = SimpAgentClient(
        agent_id="{agent_id}",
        agent_type="{agent_type}",
        port={port},
        broker_host="127.0.0.1",
        broker_port=5555
    )

    logger.info("✅ SIMP client initialized")

    # Register with broker
    client.register()
    logger.info("✅ Registered with SIMP broker")

    # Start listening for intents
    logger.info("▶️ Agent listening for intents...")
    client.listen(agent)

except Exception as e:
    logger.error(f"❌ Agent failed: {{e}}", exc_info=True)
    sys.exit(1)
'''
        return script

    @staticmethod
    def _run_agent_process(script_path: str, agent_id: str, port: int) -> None:
        """Run agent in subprocess"""
        try:
            import subprocess

            subprocess.run([sys.executable, script_path], check=True)
        except Exception as e:
            logging.error(f"Agent {agent_id} error: {e}")

    def get_agent(self, agent_id: str) -> Optional[RemoteAgent]:
        """Get agent by ID"""
        return self.agents.get(agent_id)

    def list_agents(self) -> Dict[str, RemoteAgent]:
        """List all spawned agents"""
        return dict(self.agents)

    def stop_agent(self, agent_id: str, timeout: int = 5) -> bool:
        """Stop an agent"""
        agent = self.get_agent(agent_id)
        if not agent:
            self.logger.warning(f"⚠️ Agent '{agent_id}' not found")
            return False

        if agent.process is None or not agent.process.is_alive():
            agent.status = "stopped"
            self.logger.info(f"✅ Agent stopped: {agent_id}")
            return True

        try:
            agent.process.terminate()
            agent.process.join(timeout=timeout)

            if agent.process.is_alive():
                agent.process.kill()
                agent.process.join()

            agent.status = "stopped"
            self.logger.info(f"✅ Agent terminated: {agent_id}")
            return True

        except Exception as e:
            self.logger.error(f"❌ Error stopping agent '{agent_id}': {e}")
            return False

    def stop_all_agents(self, timeout: int = 5) -> Dict[str, bool]:
        """Stop all agents"""
        results = {}
        for agent_id in list(self.agents.keys()):
            results[agent_id] = self.stop_agent(agent_id, timeout)
        return results

    def get_health_status(self) -> Dict[str, Any]:
        """Get health status of all agents"""
        status = {
            "total_agents": len(self.agents),
            "running": 0,
            "stopped": 0,
            "failed": 0,
            "agents": {},
        }

        for agent_id, agent in self.agents.items():
            agent_status = {
                "status": agent.status,
                "type": agent.agent_type,
                "port": agent.port,
                "pid": agent.pid,
                "is_alive": agent.is_alive(),
                "started_at": agent.started_at,
                "error": agent.error_message,
            }
            status["agents"][agent_id] = agent_status

            if agent.status == "running":
                status["running"] += 1
            elif agent.status == "stopped":
                status["stopped"] += 1
            elif agent.status == "failed":
                status["failed"] += 1

        return status

    def restart_agent(self, agent_id: str) -> Optional[RemoteAgent]:
        """Restart an agent"""
        agent = self.get_agent(agent_id)
        if not agent:
            return None

        self.logger.info(f"🔄 Restarting agent: {agent_id}")
        self.stop_agent(agent_id)
        time.sleep(1)

        # Note: Full restart would require storing spawn parameters
        self.logger.warning(
            f"⚠️ Agent restart requires full spawn (parameters not stored)"
        )
        return None
