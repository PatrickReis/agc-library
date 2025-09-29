"""
Orchestration module for AgentCore - Multi-framework support

This module provides multiple orchestration options:
- CrewAI for complex multi-agent scenarios (recommended)
- LangGraph for simple workflows
- AutoGen for conversational agents
- Hybrid approaches
"""

from .crew_orchestrator import CrewOrchestrator, create_crew_agent
from .langgraph_orchestrator import LangGraphOrchestrator, create_agent_graph
from .autogen_orchestrator import AutoGenOrchestrator
from .orchestrator_factory import OrchestratorFactory, get_orchestrator

__all__ = [
    "CrewOrchestrator",
    "create_crew_agent",
    "LangGraphOrchestrator",
    "create_agent_graph",
    "AutoGenOrchestrator",
    "OrchestratorFactory",
    "get_orchestrator"
]