"""
CrewAI-based orchestrator for complex multi-agent scenarios
"""

from typing import List, Dict, Any, Optional, Callable
from abc import ABC, abstractmethod

try:
    from crewai import Agent, Task, Crew, Process
    from crewai.tools import BaseTool
    CREWAI_AVAILABLE = True
except ImportError:
    CREWAI_AVAILABLE = False
    # Mock classes for when CrewAI is not available
    class Agent: pass
    class Task: pass
    class Crew: pass
    class Process: pass
    class BaseTool: pass

from ..logger.logger import get_logger

logger = get_logger("crew_orchestrator")

class AgentCoreCrewTool(BaseTool if CREWAI_AVAILABLE else object):
    """Adapter to convert AgentCore tools to CrewAI tools"""

    def __init__(self, name: str, description: str, func: Callable, **kwargs):
        if CREWAI_AVAILABLE:
            super().__init__()
        self.name = name
        self.description = description
        self.func = func
        self.kwargs = kwargs

    def _run(self, *args, **kwargs) -> str:
        """Execute the tool function"""
        try:
            result = self.func(*args, **kwargs)
            logger.tool_success(self.name, "Tool executed successfully")
            return str(result)
        except Exception as e:
            logger.tool_error(self.name, str(e))
            return f"Error executing {self.name}: {str(e)}"

class CrewOrchestrator:
    """
    CrewAI-based orchestrator for complex multi-agent workflows

    Ideal for scenarios with:
    - Multiple specialized agents
    - Complex role-based interactions
    - Enterprise workflows
    - Collaborative task solving
    """

    def __init__(self, llm, tools: Optional[List] = None):
        if not CREWAI_AVAILABLE:
            raise ImportError("CrewAI not available. Install with: pip install crewai")

        self.llm = llm
        self.tools = self._convert_tools(tools or [])
        self.agents = {}
        self.tasks = []
        self.crew = None

        logger.info(f"CrewOrchestrator initialized with {len(self.tools)} tools")

    def _convert_tools(self, tools: List) -> List[AgentCoreCrewTool]:
        """Convert AgentCore tools to CrewAI compatible tools"""
        converted_tools = []

        for tool in tools:
            if callable(tool):
                # Tool function directly
                tool_name = getattr(tool, '__name__', 'unknown_tool')
                tool_desc = getattr(tool, '__doc__', f'Tool: {tool_name}')
                converted_tools.append(
                    AgentCoreCrewTool(
                        name=tool_name,
                        description=tool_desc,
                        func=tool
                    )
                )
            elif isinstance(tool, dict) and 'function' in tool:
                # AgentCore tool format
                schema = tool.get('schema', {})
                converted_tools.append(
                    AgentCoreCrewTool(
                        name=schema.get('name', 'unknown'),
                        description=schema.get('description', 'No description'),
                        func=tool['function']
                    )
                )

        return converted_tools

    def add_agent(self,
                  role: str,
                  goal: str,
                  backstory: str,
                  tools: Optional[List] = None,
                  verbose: bool = True,
                  **kwargs) -> Agent:
        """
        Add a specialized agent to the crew

        Args:
            role: Agent's role (e.g., "API Specialist", "Data Analyst")
            goal: What the agent aims to achieve
            backstory: Agent's background and expertise
            tools: Specific tools for this agent (optional)
            verbose: Enable verbose logging
        """
        agent_tools = tools or self.tools

        agent = Agent(
            role=role,
            goal=goal,
            backstory=backstory,
            verbose=verbose,
            llm=self.llm,
            tools=agent_tools,
            **kwargs
        )

        self.agents[role] = agent
        logger.info(f"Added agent: {role}")
        return agent

    def add_task(self,
                 description: str,
                 agent: Agent,
                 expected_output: str,
                 tools: Optional[List] = None,
                 **kwargs) -> Task:
        """
        Add a task to be executed by an agent

        Args:
            description: Detailed task description
            agent: Agent responsible for the task
            expected_output: What output is expected
            tools: Specific tools for this task
        """
        task_tools = tools or agent.tools

        task = Task(
            description=description,
            agent=agent,
            expected_output=expected_output,
            tools=task_tools,
            **kwargs
        )

        self.tasks.append(task)
        logger.info(f"Added task for {agent.role}")
        return task

    def create_crew(self,
                    process: str = "sequential",
                    verbose: bool = True,
                    **kwargs) -> Crew:
        """
        Create and configure the crew

        Args:
            process: "sequential" or "hierarchical"
            verbose: Enable verbose output
        """
        if not self.agents:
            raise ValueError("No agents added to the crew")
        if not self.tasks:
            raise ValueError("No tasks added to the crew")

        process_map = {
            "sequential": Process.sequential,
            "hierarchical": Process.hierarchical
        }

        self.crew = Crew(
            agents=list(self.agents.values()),
            tasks=self.tasks,
            process=process_map.get(process, Process.sequential),
            verbose=verbose,
            **kwargs
        )

        logger.success(f"Crew created with {len(self.agents)} agents and {len(self.tasks)} tasks")
        return self.crew

    def execute(self, inputs: Optional[Dict] = None) -> Dict[str, Any]:
        """
        Execute the crew workflow

        Args:
            inputs: Optional inputs for the workflow

        Returns:
            Results from crew execution
        """
        if not self.crew:
            raise ValueError("Crew not created. Call create_crew() first")

        logger.info("Starting crew execution")

        try:
            if inputs:
                result = self.crew.kickoff(inputs=inputs)
            else:
                result = self.crew.kickoff()

            logger.success("Crew execution completed successfully")
            return {
                "status": "success",
                "result": result,
                "crew_usage": getattr(self.crew, 'usage_metrics', {})
            }

        except Exception as e:
            logger.error(f"Crew execution failed: {str(e)}")
            return {
                "status": "error",
                "error": str(e),
                "result": None
            }

def create_crew_agent(llm,
                     tools: Optional[List] = None,
                     agents_config: Optional[List[Dict]] = None,
                     tasks_config: Optional[List[Dict]] = None) -> CrewOrchestrator:
    """
    Factory function to create a pre-configured CrewAI orchestrator

    Args:
        llm: Language model instance
        tools: List of tools available to agents
        agents_config: Configuration for agents
        tasks_config: Configuration for tasks

    Returns:
        Configured CrewOrchestrator

    Example:
        agents_config = [
            {
                "role": "API Specialist",
                "goal": "Execute API calls and process responses",
                "backstory": "Expert in API integration and data processing"
            },
            {
                "role": "Response Analyst",
                "goal": "Analyze and summarize API responses",
                "backstory": "Data analyst specialized in interpreting API results"
            }
        ]

        tasks_config = [
            {
                "description": "Execute API call based on user request",
                "agent_role": "API Specialist",
                "expected_output": "JSON response from API"
            },
            {
                "description": "Analyze API response and provide summary",
                "agent_role": "Response Analyst",
                "expected_output": "Human-readable summary of results"
            }
        ]
    """

    orchestrator = CrewOrchestrator(llm, tools)

    # Default agents if none provided
    if not agents_config:
        agents_config = [
            {
                "role": "Tool Executor",
                "goal": "Execute tools and APIs based on user requests",
                "backstory": "I am a specialized agent focused on tool execution and API interaction. I excel at understanding user needs and selecting the right tools to accomplish tasks."
            },
            {
                "role": "Response Processor",
                "goal": "Process and format tool outputs for users",
                "backstory": "I specialize in analyzing tool outputs and presenting them in a clear, user-friendly format. I ensure responses are accurate and helpful."
            }
        ]

    # Add agents
    agents = {}
    for agent_config in agents_config:
        agent = orchestrator.add_agent(**agent_config)
        agents[agent_config["role"]] = agent

    # Default tasks if none provided
    if not tasks_config:
        tasks_config = [
            {
                "description": "Based on the user input: '{user_input}', determine which tools to use and execute them to gather the required information.",
                "agent_role": "Tool Executor",
                "expected_output": "Raw tool outputs and execution results"
            },
            {
                "description": "Process the tool execution results and provide a comprehensive, user-friendly response that addresses the original user request.",
                "agent_role": "Response Processor",
                "expected_output": "Clear, formatted response answering the user's question"
            }
        ]

    # Add tasks
    for task_config in tasks_config:
        agent_role = task_config.pop("agent_role")
        agent = agents.get(agent_role)
        if agent:
            orchestrator.add_task(agent=agent, **task_config)

    # Create crew
    orchestrator.create_crew()

    return orchestrator