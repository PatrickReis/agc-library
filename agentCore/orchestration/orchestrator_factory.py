"""
Orchestrator Factory - Unified interface for all orchestration frameworks
"""

import os
from typing import Dict, Any, Optional, List, Union
from enum import Enum

from ..logger.logger import get_logger

logger = get_logger("orchestrator_factory")

class OrchestrationType(Enum):
    """Available orchestration types"""
    CREWAI = "crewai"
    LANGGRAPH = "langgraph"
    AUTOGEN = "autogen"
    AUTO = "auto"  # Auto-select best available

class OrchestratorFactory:
    """Factory for creating orchestration systems"""

    @staticmethod
    def get_available_orchestrators() -> Dict[str, Dict[str, Any]]:
        """Get information about available orchestrators"""
        orchestrators = {}

        # Check CrewAI availability
        try:
            import crewai
            orchestrators["crewai"] = {
                "available": True,
                "description": "CrewAI multi-agent framework",
                "best_for": ["complex_workflows", "role_based_agents", "enterprise"],
                "features": ["multi_agent", "role_based", "collaborative", "structured"]
            }
        except ImportError:
            orchestrators["crewai"] = {
                "available": False,
                "description": "CrewAI multi-agent framework (not installed)",
                "install_command": "pip install crewai"
            }

        # Check LangGraph availability (should always be available)
        try:
            import langgraph
            orchestrators["langgraph"] = {
                "available": True,
                "description": "LangGraph workflow orchestrator",
                "best_for": ["simple_workflows", "sequential_tasks", "basic_agents"],
                "features": ["graph_based", "flexible", "lightweight"]
            }
        except ImportError:
            orchestrators["langgraph"] = {
                "available": False,
                "description": "LangGraph workflow orchestrator (not installed)",
                "install_command": "pip install langgraph"
            }

        # Check AutoGen availability
        try:
            import autogen
            orchestrators["autogen"] = {
                "available": True,
                "description": "Microsoft AutoGen conversational AI",
                "best_for": ["conversational_agents", "code_generation", "research"],
                "features": ["conversational", "code_execution", "multi_modal"]
            }
        except ImportError:
            orchestrators["autogen"] = {
                "available": False,
                "description": "Microsoft AutoGen (not installed)",
                "install_command": "pip install pyautogen"
            }

        return orchestrators

    @staticmethod
    def recommend_orchestrator(use_case: str,
                              complexity: str = "medium",
                              team_size: str = "single") -> List[str]:
        """
        Recommend orchestrator based on use case

        Args:
            use_case: Use case type (enterprise, development, research, simple)
            complexity: Complexity level (low, medium, high)
            team_size: Team size (single, small, large)

        Returns:
            List of recommended orchestrator names
        """

        recommendations = {
            "enterprise": {
                "high": {
                    "large": ["crewai", "autogen", "langgraph"],
                    "small": ["crewai", "langgraph"],
                    "single": ["crewai", "langgraph"]
                },
                "medium": {
                    "large": ["crewai", "langgraph"],
                    "small": ["crewai", "langgraph"],
                    "single": ["langgraph", "crewai"]
                },
                "low": {
                    "large": ["langgraph", "crewai"],
                    "small": ["langgraph"],
                    "single": ["langgraph"]
                }
            },
            "research": {
                "high": {
                    "large": ["autogen", "crewai", "langgraph"],
                    "small": ["autogen", "crewai"],
                    "single": ["autogen", "langgraph"]
                },
                "medium": {
                    "large": ["crewai", "autogen"],
                    "small": ["autogen", "langgraph"],
                    "single": ["langgraph", "autogen"]
                },
                "low": {
                    "large": ["langgraph", "crewai"],
                    "small": ["langgraph"],
                    "single": ["langgraph"]
                }
            },
            "development": {
                "high": {
                    "large": ["crewai", "langgraph"],
                    "small": ["langgraph", "crewai"],
                    "single": ["langgraph"]
                },
                "medium": {
                    "large": ["langgraph", "crewai"],
                    "small": ["langgraph"],
                    "single": ["langgraph"]
                },
                "low": {
                    "large": ["langgraph"],
                    "small": ["langgraph"],
                    "single": ["langgraph"]
                }
            },
            "simple": {
                "high": ["langgraph", "crewai"],
                "medium": ["langgraph"],
                "low": ["langgraph"]
            }
        }

        # Simplify for simple use case
        if use_case == "simple":
            return recommendations[use_case].get(complexity, ["langgraph"])

        return recommendations.get(use_case, {}).get(complexity, {}).get(team_size, ["langgraph"])

    @staticmethod
    def create_orchestrator(orchestrator_type: str,
                           llm,
                           tools: Optional[List] = None,
                           config: Optional[Dict[str, Any]] = None,
                           **kwargs):
        """
        Create an orchestrator instance

        Args:
            orchestrator_type: Type of orchestrator to create
            llm: Language model instance
            tools: List of tools available to the orchestrator
            config: Configuration dictionary
            **kwargs: Additional configuration parameters

        Returns:
            Configured orchestrator instance
        """

        # Merge config with kwargs
        final_config = config or {}
        final_config.update(kwargs)

        if orchestrator_type == OrchestrationType.AUTO.value:
            return OrchestratorFactory._auto_select_orchestrator(llm, tools, final_config)

        elif orchestrator_type == OrchestrationType.CREWAI.value:
            return OrchestratorFactory._create_crewai_orchestrator(llm, tools, final_config)

        elif orchestrator_type == OrchestrationType.LANGGRAPH.value:
            return OrchestratorFactory._create_langgraph_orchestrator(llm, tools, final_config)

        elif orchestrator_type == OrchestrationType.AUTOGEN.value:
            return OrchestratorFactory._create_autogen_orchestrator(llm, tools, final_config)

        else:
            raise ValueError(f"Unsupported orchestrator type: {orchestrator_type}")

    @staticmethod
    def _auto_select_orchestrator(llm, tools: Optional[List], config: Dict[str, Any]):
        """Auto-select the best available orchestrator"""

        available = OrchestratorFactory.get_available_orchestrators()

        # Determine use case from config or default
        use_case = config.get('use_case', 'development')
        complexity = config.get('complexity', 'medium')
        team_size = config.get('team_size', 'single')

        recommendations = OrchestratorFactory.recommend_orchestrator(use_case, complexity, team_size)

        # Try recommendations in order
        for orchestrator_name in recommendations:
            if available.get(orchestrator_name, {}).get('available', False):
                logger.info(f"Auto-selected orchestrator: {orchestrator_name}")

                if orchestrator_name == "crewai":
                    return OrchestratorFactory._create_crewai_orchestrator(llm, tools, config)
                elif orchestrator_name == "langgraph":
                    return OrchestratorFactory._create_langgraph_orchestrator(llm, tools, config)
                elif orchestrator_name == "autogen":
                    return OrchestratorFactory._create_autogen_orchestrator(llm, tools, config)

        # Fallback to LangGraph (should always be available)
        logger.warning("No recommended orchestrators available, falling back to LangGraph")
        return OrchestratorFactory._create_langgraph_orchestrator(llm, tools, config)

    @staticmethod
    def _create_crewai_orchestrator(llm, tools: Optional[List], config: Dict[str, Any]):
        """Create CrewAI orchestrator"""
        try:
            from .crew_orchestrator import CrewOrchestrator, create_crew_agent

            # Check if user wants pre-configured crew
            if config.get('preconfigured', True):
                return create_crew_agent(
                    llm=llm,
                    tools=tools,
                    agents_config=config.get('agents_config'),
                    tasks_config=config.get('tasks_config')
                )
            else:
                return CrewOrchestrator(llm, tools)

        except ImportError:
            raise ImportError("CrewAI not available. Install with: pip install crewai")

    @staticmethod
    def _create_langgraph_orchestrator(llm, tools: Optional[List], config: Dict[str, Any]):
        """Create LangGraph orchestrator"""
        try:
            from .langgraph_orchestrator import LangGraphOrchestrator
            return LangGraphOrchestrator(llm, tools, config)
        except ImportError:
            # Fallback to legacy implementation
            from ..graphs.graph import create_agent_graph
            return create_agent_graph(llm, tools)

    @staticmethod
    def _create_autogen_orchestrator(llm, tools: Optional[List], config: Dict[str, Any]):
        """Create AutoGen orchestrator"""
        try:
            from .autogen_orchestrator import AutoGenOrchestrator
            return AutoGenOrchestrator(llm, tools, config)
        except ImportError:
            raise ImportError("AutoGen not available. Install with: pip install pyautogen")

def get_orchestrator(orchestrator_type: str = "auto",
                    llm=None,
                    tools: Optional[List] = None,
                    config: Optional[Dict[str, Any]] = None,
                    **kwargs):
    """
    Convenience function to get an orchestrator

    Args:
        orchestrator_type: Type of orchestrator (auto, crewai, langgraph, autogen)
        llm: Language model instance (if None, will create default)
        tools: List of tools
        config: Configuration dictionary
        **kwargs: Additional configuration

    Returns:
        Configured orchestrator instance

    Examples:
        # Auto-select best orchestrator
        orchestrator = get_orchestrator("auto", llm=my_llm, tools=my_tools)

        # Specific orchestrator
        orchestrator = get_orchestrator("crewai", llm=my_llm, tools=my_tools)

        # With configuration
        orchestrator = get_orchestrator(
            "crewai",
            llm=my_llm,
            tools=my_tools,
            config={"use_case": "enterprise", "complexity": "high"}
        )
    """

    # Get default LLM if not provided
    if llm is None:
        from ..providers.llm_providers import get_llm
        llm = get_llm()

    # Merge config
    final_config = config or {}
    final_config.update(kwargs)

    # Create orchestrator
    return OrchestratorFactory.create_orchestrator(
        orchestrator_type=orchestrator_type,
        llm=llm,
        tools=tools,
        config=final_config
    )

def list_available_orchestrators() -> None:
    """Print information about available orchestrators"""
    orchestrators = OrchestratorFactory.get_available_orchestrators()

    print("🤖 Available Orchestrators:")
    print("=" * 40)

    for name, info in orchestrators.items():
        status = "✅ Available" if info.get('available') else "❌ Not installed"
        print(f"\n{name.upper()}")
        print(f"  Status: {status}")
        print(f"  Description: {info['description']}")

        if info.get('available'):
            if 'best_for' in info:
                print(f"  Best for: {', '.join(info['best_for'])}")
            if 'features' in info:
                print(f"  Features: {', '.join(info['features'])}")
        else:
            if 'install_command' in info:
                print(f"  Install: {info['install_command']}")

def recommend_orchestrator_for_use_case(use_case: str,
                                       complexity: str = "medium",
                                       team_size: str = "single") -> None:
    """Print orchestrator recommendations for a use case"""
    recommendations = OrchestratorFactory.recommend_orchestrator(use_case, complexity, team_size)
    available = OrchestratorFactory.get_available_orchestrators()

    print(f"🎯 Recommendations for: {use_case}/{complexity}/{team_size}")
    print("=" * 50)

    for i, orchestrator in enumerate(recommendations, 1):
        is_available = available.get(orchestrator, {}).get('available', False)
        status = "✅" if is_available else "❌"
        print(f"{i}. {status} {orchestrator.upper()}")

        if not is_available:
            install_cmd = available.get(orchestrator, {}).get('install_command')
            if install_cmd:
                print(f"   Install: {install_cmd}")

if __name__ == "__main__":
    # Demo the orchestrator factory
    print("AgentCore Orchestrator Factory Demo")
    print("=" * 40)

    list_available_orchestrators()

    print("\n")
    recommend_orchestrator_for_use_case("enterprise", "high", "large")

    print("\n")
    recommend_orchestrator_for_use_case("development", "low", "single")