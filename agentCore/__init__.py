"""
AgentCore - A comprehensive library for building AI agents with tool integration and multi-provider LLM support

This library provides:
- Multi-provider LLM support (AWS Bedrock, OpenAI, Ollama, Google Gemini)
- Automatic tool generation from OpenAPI specifications
- Multi-provider vector storage (AWS, Qdrant, ChromaDB, Pinecone, FAISS)
- Advanced chunking strategies (recursive, semantic, sliding window, markdown-aware)
- Multi-framework orchestration (CrewAI, LangGraph, AutoGen)
- Comprehensive logging and monitoring
- Production-ready AWS integrations
"""

__version__ = "2.0.0"
__author__ = "Patrick Reis"
__email__ = "patrick.reis1@gmail.com"
__license__ = "MIT"

# Core utilities
from .utils.api2tool import api2tool

# LLM providers
from .providers.llm_providers import get_llm, get_embeddings, get_provider_info

# Orchestration (multi-framework support)
from .orchestration.orchestrator_factory import get_orchestrator
from .orchestration.crew_orchestrator import create_crew_agent
from .graphs.graph import create_agent_graph

# Vector storage (multi-provider)
from .storage.vector_store_factory import get_vector_store, auto_configure_vector_store
from .storage.chunking.chunking_strategies import get_chunking_strategy, ChunkingMethod

# Logging
from .logger.logger import get_logger

__all__ = [
    # Core
    "api2tool",

    # LLM
    "get_llm",
    "get_embeddings",
    "get_provider_info",

    # Orchestration
    "get_orchestrator",
    "create_crew_agent",
    "create_agent_graph",

    # Storage
    "get_vector_store",
    "auto_configure_vector_store",
    "get_chunking_strategy",
    "ChunkingMethod",

    # Utilities
    "get_logger",
]