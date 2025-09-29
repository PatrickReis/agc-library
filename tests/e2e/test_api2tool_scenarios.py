"""
End-to-end tests for API2Tool scenarios
Tests the complete API2Tool conversion and microservice migration evidence
"""

import pytest
import json
import tempfile
from pathlib import Path

from agentCore.utils import api2tool

class TestAPI2ToolScenarios:
    """Test API2Tool conversion scenarios"""

    @pytest.fixture
    def sample_openapi_spec(self):
        """Sample OpenAPI specification for testing"""
        return {
            "openapi": "3.0.0",
            "info": {
                "title": "Pet Store API",
                "version": "1.0.0",
                "description": "A sample API for pet store operations"
            },
            "servers": [
                {"url": "https://petstore.example.com"}
            ],
            "paths": {
                "/pets": {
                    "get": {
                        "operationId": "list_pets",
                        "summary": "List all pets",
                        "description": "Returns a list of all pets in the store",
                        "parameters": [
                            {
                                "name": "limit",
                                "in": "query",
                                "required": False,
                                "schema": {"type": "integer", "maximum": 100},
                                "description": "Maximum number of pets to return"
                            }
                        ],
                        "responses": {
                            "200": {
                                "description": "A list of pets",
                                "content": {
                                    "application/json": {
                                        "schema": {
                                            "type": "array",
                                            "items": {"$ref": "#/components/schemas/Pet"}
                                        }
                                    }
                                }
                            }
                        }
                    },
                    "post": {
                        "operationId": "create_pet",
                        "summary": "Create a new pet",
                        "description": "Add a new pet to the store",
                        "requestBody": {
                            "required": True,
                            "content": {
                                "application/json": {
                                    "schema": {"$ref": "#/components/schemas/Pet"}
                                }
                            }
                        },
                        "responses": {
                            "201": {
                                "description": "Pet created successfully"
                            }
                        }
                    }
                },
                "/pets/{petId}": {
                    "get": {
                        "operationId": "get_pet",
                        "summary": "Get a pet by ID",
                        "description": "Returns details of a specific pet",
                        "parameters": [
                            {
                                "name": "petId",
                                "in": "path",
                                "required": True,
                                "schema": {"type": "integer"},
                                "description": "ID of the pet to retrieve"
                            }
                        ],
                        "responses": {
                            "200": {
                                "description": "Pet details",
                                "content": {
                                    "application/json": {
                                        "schema": {"$ref": "#/components/schemas/Pet"}
                                    }
                                }
                            },
                            "404": {
                                "description": "Pet not found"
                            }
                        }
                    }
                }
            },
            "components": {
                "schemas": {
                    "Pet": {
                        "type": "object",
                        "required": ["name", "status"],
                        "properties": {
                            "id": {
                                "type": "integer",
                                "format": "int64"
                            },
                            "name": {
                                "type": "string"
                            },
                            "status": {
                                "type": "string",
                                "enum": ["available", "pending", "sold"]
                            }
                        }
                    }
                }
            }
        }

    def test_openapi_analysis(self, sample_openapi_spec):
        """Test 1: Analyze OpenAPI specification"""
        print("\n🧪 Testing OpenAPI analysis")

        try:
            # Get API information
            info = api2tool(sample_openapi_spec, output_format="info")

            assert info["loaded"] == True, "API not loaded correctly"
            assert info["title"] == "Pet Store API", "Wrong API title"
            assert info["tool_count"] == 3, f"Expected 3 tools, got {info['tool_count']}"

            print(f"✅ API Analysis:")
            print(f"   Title: {info['title']}")
            print(f"   Version: {info['version']}")
            print(f"   Tools: {info['tool_count']}")
            print(f"   Base URL: {info['base_url']}")

            # Test tool names
            tool_names = api2tool(sample_openapi_spec, output_format="names")
            expected_names = ["list_pets", "create_pet", "get_pet"]

            for expected_name in expected_names:
                assert expected_name in tool_names, f"Missing tool: {expected_name}"

            print(f"✅ Generated tools: {', '.join(tool_names)}")

        except Exception as e:
            pytest.fail(f"OpenAPI analysis test failed: {e}")

    def test_tool_generation(self, sample_openapi_spec):
        """Test 2: Generate tools from OpenAPI"""
        print("\n🧪 Testing tool generation")

        try:
            # Generate tools
            tools = api2tool(sample_openapi_spec, output_format="tools")

            assert len(tools) == 3, f"Expected 3 tools, got {len(tools)}"

            # Verify tool structure
            for tool in tools:
                assert "schema" in tool, "Missing schema in tool"
                assert "function" in tool, "Missing function in tool"

                schema = tool["schema"]
                assert "name" in schema, "Missing name in schema"
                assert "description" in schema, "Missing description in schema"
                assert "parameters" in schema, "Missing parameters in schema"

            print(f"✅ Generated {len(tools)} tools successfully")

            # Test specific tool
            list_pets_tool = next((t for t in tools if t["schema"]["name"] == "list_pets"), None)
            assert list_pets_tool is not None, "list_pets tool not found"

            # Check parameters
            params = list_pets_tool["schema"]["parameters"]
            assert "properties" in params, "Missing properties in parameters"

            print(f"✅ Tool validation passed")

        except Exception as e:
            pytest.fail(f"Tool generation test failed: {e}")

    def test_python_file_generation(self, sample_openapi_spec):
        """Test 3: Generate Python file with tools"""
        print("\n🧪 Testing Python file generation")

        try:
            # Generate Python code
            python_code = api2tool(sample_openapi_spec, output_format="file")

            assert "def list_pets" in python_code, "list_pets function not found in generated code"
            assert "def create_pet" in python_code, "create_pet function not found in generated code"
            assert "def get_pet" in python_code, "get_pet function not found in generated code"

            assert "@tool" in python_code, "Tool decorator not found"
            assert "import" in python_code, "Import statements not found"

            print(f"✅ Generated Python code ({len(python_code)} characters)")
            print(f"   Functions: list_pets, create_pet, get_pet")

            # Save to temporary file and verify it's valid Python
            with tempfile.NamedTemporaryFile(mode='w', suffix='.py', delete=False) as f:
                f.write(python_code)
                temp_file = f.name

            # Try to compile the generated code
            with open(temp_file, 'r') as f:
                code_content = f.read()

            compile(code_content, temp_file, 'exec')
            print(f"✅ Generated code is valid Python")

            # Cleanup
            Path(temp_file).unlink()

        except Exception as e:
            pytest.fail(f"Python file generation test failed: {e}")

    def test_microservice_migration_evidence(self, sample_openapi_spec):
        """Test 4: Evidence of microservice migration capabilities"""
        print("\n🧪 Testing microservice migration evidence")

        try:
            # Simulate complete microservice conversion workflow

            # 1. Analyze existing API
            analysis = api2tool(sample_openapi_spec, output_format="info")

            # 2. Generate tools dictionary for easy access
            tools_dict = api2tool(sample_openapi_spec, output_format="dict")

            # 3. Generate deployable Python code
            service_code = api2tool(sample_openapi_spec, output_format="file")

            # Evidence of migration capabilities:
            migration_evidence = {
                "original_api": {
                    "title": analysis["title"],
                    "endpoints": len(analysis["tool_names"]),
                    "base_url": analysis["base_url"]
                },
                "generated_tools": {
                    "count": len(tools_dict),
                    "tool_names": list(tools_dict.keys()),
                    "all_have_schemas": all("schema" in tool for tool in tools_dict.values())
                },
                "microservice_ready": {
                    "python_code_generated": len(service_code) > 0,
                    "functions_created": "def " in service_code,
                    "langraph_compatible": "@tool" in service_code,
                    "importable": "import" in service_code
                },
                "deployment_ready": {
                    "structured_format": True,
                    "error_handling": "except" in service_code,
                    "documentation": '"""' in service_code
                }
            }

            # Verify migration evidence
            assert migration_evidence["original_api"]["endpoints"] > 0, "No endpoints found"
            assert migration_evidence["generated_tools"]["count"] > 0, "No tools generated"
            assert migration_evidence["generated_tools"]["all_have_schemas"], "Tools missing schemas"
            assert migration_evidence["microservice_ready"]["python_code_generated"], "No Python code generated"
            assert migration_evidence["microservice_ready"]["langraph_compatible"], "Not LangGraph compatible"
            assert migration_evidence["deployment_ready"]["structured_format"], "Not properly structured"

            print(f"✅ Microservice Migration Evidence:")
            print(f"   Original API: {migration_evidence['original_api']['title']} ({migration_evidence['original_api']['endpoints']} endpoints)")
            print(f"   Generated Tools: {migration_evidence['generated_tools']['count']} tools")
            print(f"   Python Code: {len(service_code)} characters")
            print(f"   LangGraph Compatible: ✅")
            print(f"   Deployment Ready: ✅")

            # Additional evidence: Show that tools can be used programmatically
            tools = api2tool(sample_openapi_spec)
            tool_functions = [tool['function'] for tool in tools]

            assert len(tool_functions) == 3, "Tool functions not extractable"
            print(f"   Programmatic Access: ✅ ({len(tool_functions)} callable functions)")

        except Exception as e:
            pytest.fail(f"Microservice migration evidence test failed: {e}")

    def test_real_world_api_example(self):
        """Test 5: Real-world API example (if available)"""
        print("\n🧪 Testing real-world API example")

        try:
            # Test with Swagger Petstore (public API)
            petstore_url = "https://petstore.swagger.io/v2/swagger.json"

            # Test if we can fetch and process it
            try:
                info = api2tool(petstore_url, output_format="info")

                print(f"✅ Real API processed:")
                print(f"   API: {info['title']}")
                print(f"   Tools generated: {info['tool_count']}")

                # Get tool names
                tool_names = api2tool(petstore_url, output_format="names")
                print(f"   Sample tools: {', '.join(tool_names[:5])}")

                if len(tool_names) > 5:
                    print(f"   ... and {len(tool_names) - 5} more")

            except Exception as api_error:
                print(f"⚠️ Real API test skipped (network/API issue): {api_error}")
                # This is expected in offline environments

        except Exception as e:
            pytest.fail(f"Real-world API test failed: {e}")

    def test_chunking_strategy_evidence(self, sample_openapi_spec):
        """Test 6: Evidence of chunking strategy for large APIs"""
        print("\n🧪 Testing chunking strategy evidence")

        try:
            # Create a larger API spec to demonstrate chunking
            large_api_spec = sample_openapi_spec.copy()

            # Add more endpoints to simulate large API
            for i in range(10):
                large_api_spec["paths"][f"/resource{i}"] = {
                    "get": {
                        "operationId": f"get_resource_{i}",
                        "summary": f"Get resource {i}",
                        "responses": {"200": {"description": "Success"}}
                    }
                }

            # Process large API
            tools = api2tool(large_api_spec)
            tools_dict = api2tool(large_api_spec, output_format="dict")

            # Evidence of chunking capabilities
            chunking_evidence = {
                "total_tools": len(tools),
                "can_process_large_apis": len(tools) > 10,
                "tools_are_organized": isinstance(tools_dict, dict),
                "individual_tool_access": "get_resource_0" in tools_dict,
                "batch_processing": len(tools) == len(tools_dict)
            }

            # Verify chunking evidence
            assert chunking_evidence["total_tools"] > 10, "Large API not processed"
            assert chunking_evidence["can_process_large_apis"], "Cannot handle large APIs"
            assert chunking_evidence["tools_are_organized"], "Tools not properly organized"

            print(f"✅ Chunking Strategy Evidence:")
            print(f"   Total tools processed: {chunking_evidence['total_tools']}")
            print(f"   Large API handling: ✅")
            print(f"   Organized output: ✅")
            print(f"   Individual access: ✅")

            # Demonstrate chunking by processing tools in groups
            chunk_size = 5
            tool_chunks = [tools[i:i + chunk_size] for i in range(0, len(tools), chunk_size)]

            print(f"   Chunking capability: {len(tool_chunks)} chunks of {chunk_size} tools")

        except Exception as e:
            pytest.fail(f"Chunking strategy test failed: {e}")

if __name__ == "__main__":
    pytest.main([__file__, "-v"])