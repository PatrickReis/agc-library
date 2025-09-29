#!/usr/bin/env python3
"""
AgentCore v2.0 - Exemplo Avançado

Este exemplo demonstra as novas funcionalidades da biblioteca AgentCore v2.0:

1. 🤖 Multi-Framework Orchestration (CrewAI, LangGraph)
2. 🗄️ Multi-Provider Vector Storage (AWS, Qdrant, ChromaDB, etc.)
3. ✂️ Advanced Chunking Strategies
4. ☁️ Production-Ready AWS Integrations
5. 🔧 Auto-Configuration Based on Use Case
"""

import os
from typing import List, Dict, Any

# Import new AgentCore v2.0 components
from agentCore import (
    # Core
    api2tool,

    # LLM
    get_llm, get_provider_info,

    # Multi-framework orchestration
    get_orchestrator, create_crew_agent,

    # Multi-provider storage
    get_vector_store, auto_configure_vector_store,

    # Advanced chunking
    get_chunking_strategy, ChunkingMethod,

    # Logging
    get_logger
)

logger = get_logger("example_v2")

def demo_multi_framework_orchestration():
    """Demonstrate multi-framework orchestration capabilities"""

    print("\n🤖 MULTI-FRAMEWORK ORCHESTRATION")
    print("=" * 50)

    # Configure LLM (AWS Bedrock is default)
    llm = get_llm()

    # Create some example tools
    example_openapi = {
        "openapi": "3.0.0",
        "info": {"title": "Demo API", "version": "1.0.0"},
        "servers": [{"url": "https://api.example.com"}],
        "paths": {
            "/weather/{city}": {
                "get": {
                    "operationId": "get_weather",
                    "summary": "Get weather for a city",
                    "parameters": [
                        {
                            "name": "city",
                            "in": "path",
                            "required": True,
                            "schema": {"type": "string"}
                        }
                    ]
                }
            },
            "/news": {
                "get": {
                    "operationId": "get_news",
                    "summary": "Get latest news",
                    "parameters": [
                        {
                            "name": "category",
                            "in": "query",
                            "schema": {"type": "string"}
                        }
                    ]
                }
            }
        }
    }

    tools = api2tool(example_openapi)
    tool_functions = [tool['function'] for tool in tools]

    # Option 1: CrewAI (Best for complex multi-agent scenarios)
    print("\n1. 🎭 CrewAI Orchestration")
    try:
        crew_agent = create_crew_agent(
            llm=llm,
            tools=tool_functions,
            agents_config=[
                {
                    "role": "Weather Specialist",
                    "goal": "Provide accurate weather information",
                    "backstory": "Expert meteorologist with access to weather APIs"
                },
                {
                    "role": "News Analyst",
                    "goal": "Gather and analyze news information",
                    "backstory": "Experienced journalist with access to news feeds"
                }
            ]
        )

        print("   ✅ CrewAI agent created successfully")
        print("   👥 Agents: Weather Specialist, News Analyst")

    except ImportError:
        print("   ⚠️ CrewAI not available (install: pip install crewai)")
    except Exception as e:
        print(f"   ❌ Error: {e}")

    # Option 2: Auto-select orchestrator
    print("\n2. 🎯 Auto-Selected Orchestrator")
    try:
        orchestrator = get_orchestrator(
            orchestrator_type="auto",  # Auto-select best option
            llm=llm,
            tools=tool_functions
        )
        print(f"   ✅ Auto-selected: {type(orchestrator).__name__}")
    except Exception as e:
        print(f"   ❌ Error: {e}")

def demo_multi_provider_storage():
    """Demonstrate multi-provider vector storage"""

    print("\n🗄️ MULTI-PROVIDER VECTOR STORAGE")
    print("=" * 50)

    # Option 1: Auto-configure based on use case
    print("\n1. 🤖 Auto-Configuration")

    use_cases = [
        ("development", "development", "low"),
        ("enterprise", "production", "high"),
        ("research", "development", "medium")
    ]

    for use_case, environment, budget in use_cases:
        try:
            store = auto_configure_vector_store(use_case, environment, budget)
            health = store.health_check()
            print(f"   ✅ {use_case}/{environment}/{budget}: {health['provider']}")
        except Exception as e:
            print(f"   ❌ {use_case}/{environment}/{budget}: {e}")

    # Option 2: Manual provider selection
    print("\n2. 🔧 Manual Provider Configuration")

    providers_to_test = [
        ("chroma_local", {"persist_directory": "./test_chroma"}),
        ("faiss_local", {"index_path": "./test_faiss"}),
    ]

    # Add AWS providers if credentials available
    if os.getenv('AWS_ACCESS_KEY_ID') or os.getenv('AWS_PROFILE'):
        providers_to_test.extend([
            ("aws_s3_faiss", {
                "s3_bucket": "my-test-bucket",
                "region": "us-east-1"
            }),
        ])

    for provider_type, config in providers_to_test:
        try:
            store = get_vector_store(provider_type, config)
            info = store.get_collection_info()
            print(f"   ✅ {provider_type}: {info.get('storage_type', 'initialized')}")
        except Exception as e:
            print(f"   ⚠️ {provider_type}: {str(e)[:50]}...")

def demo_advanced_chunking():
    """Demonstrate advanced chunking strategies"""

    print("\n✂️ ADVANCED CHUNKING STRATEGIES")
    print("=" * 50)

    # Sample texts for different content types
    sample_texts = {
        "markdown": """# Machine Learning Guide

## Introduction
Machine learning is a subset of artificial intelligence that focuses on algorithms.

### Supervised Learning
Supervised learning uses labeled training data to learn a mapping function.

#### Classification
Classification predicts discrete categories or classes.

#### Regression
Regression predicts continuous numerical values.

## Unsupervised Learning
Unsupervised learning finds patterns in data without labeled examples.
""",

        "python_code": '''
def calculate_accuracy(predictions, targets):
    """Calculate classification accuracy."""
    correct = sum(p == t for p, t in zip(predictions, targets))
    return correct / len(predictions)

class NeuralNetwork:
    """Simple neural network implementation."""

    def __init__(self, layers):
        self.layers = layers
        self.weights = []

    def forward(self, x):
        """Forward pass through the network."""
        for layer in self.layers:
            x = layer.forward(x)
        return x

    def backward(self, gradient):
        """Backward pass for training."""
        for layer in reversed(self.layers):
            gradient = layer.backward(gradient)
        return gradient

def train_model(model, data, epochs=100):
    """Train the neural network model."""
    for epoch in range(epochs):
        for batch in data:
            output = model.forward(batch.input)
            loss = calculate_loss(output, batch.target)
            model.backward(loss.gradient())
''',

        "regular_text": """
Artificial intelligence has revolutionized numerous industries in recent years.
From healthcare diagnostics to autonomous vehicles, AI applications continue to expand.
Machine learning algorithms can process vast amounts of data to identify patterns
that would be impossible for humans to detect manually. Deep learning, a subset
of machine learning, has been particularly successful in image recognition and
natural language processing tasks. However, the rapid advancement of AI also
raises important ethical considerations regarding privacy, bias, and job displacement.
"""
    }

    # Test different chunking strategies
    strategies = [
        (ChunkingMethod.RECURSIVE, {"chunk_size": 200, "chunk_overlap": 50}),
        (ChunkingMethod.SLIDING_WINDOW, {"chunk_size": 200, "stride": 100}),
        (ChunkingMethod.MARKDOWN_AWARE, {"chunk_size": 300}),
        (ChunkingMethod.CODE_AWARE, {"chunk_size": 400, "language": "python"}),
    ]

    for content_type, text in sample_texts.items():
        print(f"\n📄 Content Type: {content_type}")

        for method, config in strategies:
            try:
                # Skip inappropriate combinations
                if method == ChunkingMethod.MARKDOWN_AWARE and content_type != "markdown":
                    continue
                if method == ChunkingMethod.CODE_AWARE and content_type != "python_code":
                    continue
                if method == ChunkingMethod.SEMANTIC and content_type == "python_code":
                    continue  # Skip semantic for code (needs sentence-transformers)

                chunker = get_chunking_strategy(method, **config)
                chunks = chunker.chunk(text, {"content_type": content_type})

                avg_size = sum(len(c.content) for c in chunks) / len(chunks) if chunks else 0

                print(f"   {method.value:15} | {len(chunks):2} chunks | avg: {avg_size:.0f} chars")

            except ImportError as e:
                print(f"   {method.value:15} | ⚠️ Missing dependency")
            except Exception as e:
                print(f"   {method.value:15} | ❌ Error: {str(e)[:30]}...")

def demo_production_features():
    """Demonstrate production-ready features"""

    print("\n🏭 PRODUCTION-READY FEATURES")
    print("=" * 50)

    # 1. Provider recommendations
    print("\n1. 📊 Provider Recommendations")
    from agentCore.storage.vector_store_factory import VectorStoreFactory

    scenarios = [
        ("enterprise", "production", "high"),
        ("development", "development", "low"),
        ("research", "production", "medium"),
        ("cost_sensitive", "production", "low")
    ]

    for use_case, env, budget in scenarios:
        recommendations = VectorStoreFactory.recommend_provider(use_case, env, budget)
        print(f"   {use_case:12} | {env:11} | {budget:6} → {', '.join(recommendations[:2])}")

    # 2. Health checks and monitoring
    print("\n2. 🏥 Health Checks")
    try:
        # Test with local storage
        store = get_vector_store("chroma_local", {"persist_directory": "./health_test"})
        health = store.health_check()

        print(f"   Status: {health['status']}")
        print(f"   Provider: {health['provider']}")

        if health['status'] == 'healthy':
            print("   ✅ Vector store is operational")
        else:
            print(f"   ❌ Issue detected: {health.get('error', 'Unknown')}")

    except Exception as e:
        print(f"   ❌ Health check failed: {e}")

    # 3. AWS Integration status
    print("\n3. ☁️ AWS Integration Status")
    try:
        provider_info = get_provider_info()

        if provider_info['provider'] == 'bedrock':
            print(f"   ✅ Provider: AWS Bedrock")
            print(f"   📍 Region: {provider_info.get('region', 'N/A')}")
            print(f"   🤖 Model: {provider_info.get('model', 'N/A')}")
            print(f"   🔑 Credentials: {'✅' if provider_info.get('credentials_configured') else '❌'}")
        else:
            print(f"   📝 Current provider: {provider_info['provider']}")
            print("   💡 For production, consider AWS Bedrock")

    except Exception as e:
        print(f"   ❌ Provider check failed: {e}")

def demo_integration_example():
    """Demonstrate complete integration example"""

    print("\n🔗 COMPLETE INTEGRATION EXAMPLE")
    print("=" * 50)

    try:
        # 1. Setup LLM
        llm = get_llm()
        print("✅ LLM configured")

        # 2. Setup vector store
        vector_store = auto_configure_vector_store("development", "development", "low")
        print("✅ Vector store configured")

        # 3. Setup chunking
        chunker = get_chunking_strategy(ChunkingMethod.RECURSIVE, chunk_size=500, chunk_overlap=100)
        print("✅ Chunking strategy configured")

        # 4. Setup tools
        simple_api = {
            "openapi": "3.0.0",
            "info": {"title": "Simple API", "version": "1.0.0"},
            "servers": [{"url": "https://api.example.com"}],
            "paths": {
                "/search": {
                    "get": {
                        "operationId": "search_data",
                        "summary": "Search for information",
                        "parameters": [{"name": "query", "in": "query", "schema": {"type": "string"}}]
                    }
                }
            }
        }

        tools = api2tool(simple_api)
        print(f"✅ {len(tools)} tools generated from API")

        # 5. Create orchestrator (try CrewAI first, fallback to LangGraph)
        try:
            agent = create_crew_agent(llm=llm, tools=[t['function'] for t in tools])
            orchestrator_type = "CrewAI"
        except ImportError:
            from agentCore.graphs.graph import create_agent_graph
            agent = create_agent_graph(llm, tools=[t['function'] for t in tools])
            orchestrator_type = "LangGraph"

        print(f"✅ Agent created using {orchestrator_type}")

        print("\n🎉 Complete system ready!")
        print("   Components: LLM + Vector Store + Chunking + Tools + Agent")
        print("   Ready for: Document processing, API integration, Q&A")

    except Exception as e:
        print(f"❌ Integration failed: {e}")

def main():
    """Run all demonstrations"""

    print("🚀 AGENTCORE v2.0 - ADVANCED FEATURES DEMO")
    print("=" * 60)

    # Check prerequisites
    provider_info = get_provider_info()
    print(f"🤖 LLM Provider: {provider_info['provider']}")

    if provider_info['provider'] == 'bedrock':
        creds_status = "✅" if provider_info.get('credentials_configured') else "⚠️"
        print(f"☁️ AWS Credentials: {creds_status}")

    # Run demonstrations
    demo_multi_framework_orchestration()
    demo_multi_provider_storage()
    demo_advanced_chunking()
    demo_production_features()
    demo_integration_example()

    print(f"\n{'='*60}")
    print("🎯 SUMMARY OF IMPROVEMENTS")
    print("=" * 60)
    print("✅ Multi-framework orchestration (CrewAI + LangGraph + AutoGen)")
    print("✅ Multi-provider vector storage (AWS + Qdrant + ChromaDB + Pinecone + FAISS)")
    print("✅ Advanced chunking strategies (7+ methods)")
    print("✅ Production-ready AWS integrations")
    print("✅ Auto-configuration based on use case")
    print("✅ Health monitoring and diagnostics")
    print("✅ Comprehensive error handling")

    print(f"\n💡 NEXT STEPS:")
    print("1. Install additional providers: pip install crewai qdrant-client")
    print("2. Configure AWS credentials for production features")
    print("3. Test with your own APIs and documents")
    print("4. Explore enterprise features in production environment")

if __name__ == "__main__":
    main()