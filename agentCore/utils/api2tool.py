"""
API to Tool converter - Main interface for AgentCore library

This module provides the main api2tool function that users will import:
from agentCore.utils import api2tool
"""

import os
import tempfile
from typing import Union, List, Dict, Any, Optional
from pathlib import Path
from .openapi_to_tools import OpenAPIToLangGraphTools, convert_openapi_to_tools, generate_langraph_tools_file


class API2Tool:
    """
    Main API2Tool class that provides comprehensive functionality for converting
    OpenAPI specifications to LangGraph tools.
    """

    def __init__(self, base_url: Optional[str] = None):
        """
        Initialize API2Tool converter.

        Args:
            base_url: Base URL for API calls. If not provided, will be inferred from OpenAPI spec.
        """
        self.base_url = base_url
        self.converter = OpenAPIToLangGraphTools(base_url=base_url)
        self.loaded_spec = None

    def load_openapi(self, source: Union[str, Path, Dict]) -> 'API2Tool':
        """
        Load OpenAPI specification from various sources.

        Args:
            source: Can be:
                - URL string (http://example.com/openapi.json)
                - File path (./openapi.json)
                - Dictionary with OpenAPI spec

        Returns:
            Self for method chaining
        """
        self.loaded_spec = self.converter.load_openapi(source)

        # Auto-detect base URL if not provided
        if not self.base_url and self.loaded_spec:
            servers = self.loaded_spec.get('servers', [])
            if servers:
                self.base_url = servers[0].get('url', 'http://localhost:8000')
                self.converter.base_url = self.base_url

        return self

    def to_tools(self) -> List[Dict[str, Any]]:
        """
        Convert loaded OpenAPI spec to LangGraph tools.

        Returns:
            List of tool dictionaries with 'schema' and 'function' keys
        """
        if not self.loaded_spec:
            raise ValueError("No OpenAPI spec loaded. Call load_openapi() first.")

        return self.converter.generate_tools()

    def to_dict(self) -> Dict[str, Dict[str, Any]]:
        """
        Convert to tools dictionary with operation_id as keys.

        Returns:
            Dictionary mapping operation_id to tool data
        """
        if not self.loaded_spec:
            raise ValueError("No OpenAPI spec loaded. Call load_openapi() first.")

        return self.converter.generate_tools_dict()

    def to_file(self, output_path: str = "generated_tools.py") -> str:
        """
        Generate a Python file with @tool decorated functions.

        Args:
            output_path: Path where to save the generated file

        Returns:
            The generated Python code as string
        """
        if not self.loaded_spec:
            raise ValueError("No OpenAPI spec loaded. Call load_openapi() first.")

        return self.converter.generate_python_file(output_path, self.base_url)

    def get_tool_names(self) -> List[str]:
        """
        Get list of tool names that would be generated.

        Returns:
            List of operation IDs/tool names
        """
        if not self.loaded_spec:
            raise ValueError("No OpenAPI spec loaded. Call load_openapi() first.")

        tools = self.to_tools()
        return [tool['schema']['name'] for tool in tools]

    def get_info(self) -> Dict[str, Any]:
        """
        Get information about the loaded OpenAPI spec and generated tools.

        Returns:
            Dictionary with spec info, tool count, etc.
        """
        if not self.loaded_spec:
            return {"loaded": False, "error": "No OpenAPI spec loaded"}

        tools = self.to_tools()

        return {
            "loaded": True,
            "title": self.loaded_spec.get('info', {}).get('title', 'Unknown API'),
            "version": self.loaded_spec.get('info', {}).get('version', 'Unknown'),
            "description": self.loaded_spec.get('info', {}).get('description', ''),
            "base_url": self.base_url,
            "tool_count": len(tools),
            "tool_names": [tool['schema']['name'] for tool in tools]
        }


def api2tool(source: Union[str, Path, Dict],
             base_url: Optional[str] = None,
             output_format: str = "tools") -> Union[List[Dict[str, Any]], Dict[str, Dict[str, Any]], str]:
    """
    Main api2tool function - converts OpenAPI specification to LangGraph tools.

    This is the primary interface users will use:
    from agentCore.utils import api2tool

    Args:
        source: OpenAPI source - can be:
            - URL string: "http://example.com/openapi.json"
            - File path: "./openapi.json" or Path("./openapi.json")
            - Dictionary: OpenAPI spec as dict
        base_url: Base URL for API calls (optional)
        output_format: Output format, one of:
            - "tools": List of tool dictionaries (default)
            - "dict": Dictionary with operation_id keys
            - "file": Generate Python file and return code
            - "names": List of tool names only
            - "info": Info about the spec and tools

    Returns:
        Depending on output_format:
        - "tools": List[Dict[str, Any]] - Ready to use with LangGraph
        - "dict": Dict[str, Dict[str, Any]] - Tools indexed by operation_id
        - "file": str - Python code for the generated file
        - "names": List[str] - List of tool names
        - "info": Dict[str, Any] - Information about the spec

    Examples:
        # Basic usage - get tools list
        tools = api2tool("./openapi.json")

        # Get tools as dictionary
        tools_dict = api2tool("./openapi.json", output_format="dict")

        # Generate Python file
        code = api2tool("./openapi.json", output_format="file")

        # Get just the tool names
        names = api2tool("./openapi.json", output_format="names")

        # Get info about the API
        info = api2tool("./openapi.json", output_format="info")

        # Load from URL
        tools = api2tool("http://petstore.swagger.io/v2/swagger.json")

        # Specify base URL
        tools = api2tool("./openapi.json", base_url="https://api.example.com")
    """

    converter = API2Tool(base_url=base_url)
    converter.load_openapi(source)

    if output_format == "tools":
        return converter.to_tools()
    elif output_format == "dict":
        return converter.to_dict()
    elif output_format == "file":
        return converter.to_file()
    elif output_format == "names":
        return converter.get_tool_names()
    elif output_format == "info":
        return converter.get_info()
    else:
        raise ValueError(f"Invalid output_format: {output_format}. Must be one of: tools, dict, file, names, info")


def api2tool_file(source: Union[str, Path, Dict],
                  output_path: str = "generated_tools.py",
                  base_url: Optional[str] = None) -> str:
    """
    Convenience function to generate a Python file with tools.

    Args:
        source: OpenAPI specification source
        output_path: Path where to save the generated file
        base_url: Base URL for API calls

    Returns:
        The generated Python code
    """
    converter = API2Tool(base_url=base_url)
    converter.load_openapi(source)
    return converter.to_file(output_path)


def api2tool_quick(source: Union[str, Path, Dict], base_url: Optional[str] = None) -> List:
    """
    Quick function to get tools ready for immediate use with LangGraph.

    Args:
        source: OpenAPI specification source
        base_url: Base URL for API calls

    Returns:
        List of functions ready to use with LangGraph ToolExecutor
    """
    tools = api2tool(source, base_url=base_url, output_format="tools")
    return [tool['function'] for tool in tools]


# Backward compatibility - expose the original function
generate_tools_from_openapi = generate_langraph_tools_file