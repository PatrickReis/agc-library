"""
End-to-end tests for chat scenarios
Tests the complete chat scenarios as specified in the requirements
"""

import pytest
import os
import time
from typing import Dict, Any

from agentCore.providers import get_llm, get_embeddings
from agentCore.graphs import create_agent_graph
from agentCore.utils import api2tool
from agentCore.storage import get_vector_store
from agentCore.evaluation import PromptEvaluator, create_eval_dataset
from agentCore.reasoning import ChainOfThoughtReasoner
from agentCore.observability import get_tracer
from langchain_core.messages import HumanMessage

class TestChatScenarios:
    """Test chat scenarios end-to-end"""

    @pytest.fixture(autouse=True)
    def setup(self):
        """Setup for each test"""
        self.tracer = get_tracer()

    def test_simple_chat_bedrock(self):
        """Test 1: Simple chat with Bedrock"""
        print("\n🧪 Testing simple chat with Bedrock")

        # Start tracing
        trace_id = self.tracer.start_trace("simple_chat_test")

        try:
            with self.tracer.trace_event(trace_id, "llm_setup"):
                # Setup LLM
                llm = get_llm("bedrock")
                assert llm is not None, "Failed to initialize Bedrock LLM"

            with self.tracer.trace_event(trace_id, "agent_creation"):
                # Create simple agent (no tools)
                agent = create_agent_graph(llm, tools=None)
                assert agent is not None, "Failed to create agent"

            with self.tracer.trace_event(trace_id, "simple_interaction"):
                # Test simple interaction
                test_message = "Olá! Como você está?"
                result = agent.invoke({
                    "messages": [HumanMessage(content=test_message)]
                })

                response = result["messages"][-1].content
                assert response is not None, "No response received"
                assert len(response) > 0, "Empty response"

                print(f"✅ Simple chat response: {response[:100]}...")

        except Exception as e:
            pytest.fail(f"Simple chat test failed: {e}")
        finally:
            self.tracer.end_trace(trace_id)

    def test_reasoning_chat_bedrock(self):
        """Test 2: Chat with reasoning using Bedrock"""
        print("\n🧪 Testing reasoning chat with Bedrock")

        trace_id = self.tracer.start_trace("reasoning_chat_test")

        try:
            with self.tracer.trace_event(trace_id, "llm_setup"):
                llm = get_llm("bedrock")

            with self.tracer.trace_event(trace_id, "reasoning_setup"):
                # Setup reasoning
                reasoner = ChainOfThoughtReasoner(llm)

            with self.tracer.trace_event(trace_id, "reasoning_test"):
                # Test reasoning
                reasoning_question = "Se eu tenho 15 maçãs e como 3, depois compro mais 8, quantas maçãs tenho no total?"

                reasoning_result = reasoner.reason(reasoning_question)

                assert reasoning_result.final_answer is not None, "No reasoning result"
                assert len(reasoning_result.steps) > 0, "No reasoning steps"

                print(f"✅ Reasoning result: {reasoning_result.final_answer}")
                print(f"📊 Reasoning steps: {len(reasoning_result.steps)}")

        except Exception as e:
            pytest.fail(f"Reasoning chat test failed: {e}")
        finally:
            self.tracer.end_trace(trace_id)

    @pytest.mark.skipif(
        not os.getenv("ENABLE_VECTOR_TESTS"),
        reason="Vector store tests disabled"
    )
    def test_chat_with_vector_store(self):
        """Test 3: Chat with reasoning and vector store"""
        print("\n🧪 Testing chat with vector store + reasoning")

        trace_id = self.tracer.start_trace("vector_chat_test")

        try:
            with self.tracer.trace_event(trace_id, "setup"):
                # Setup components
                llm = get_llm("bedrock")
                embeddings = get_embeddings("bedrock")

                # Setup vector store (local for testing)
                vector_store = get_vector_store(
                    "chroma_local",
                    {"persist_directory": "./test_chroma_db"}
                )

            with self.tracer.trace_event(trace_id, "vector_population"):
                # Add test documents
                test_docs = [
                    "AgentCore é uma biblioteca Python para construir agentes de IA.",
                    "A biblioteca suporta múltiplos provedores LLM como AWS Bedrock.",
                    "Você pode converter APIs OpenAPI em ferramentas automaticamente."
                ]

                vector_store.add_documents(test_docs)

            with self.tracer.trace_event(trace_id, "rag_query"):
                # Test RAG query
                query = "O que é AgentCore?"

                # Retrieve relevant documents
                relevant_docs = vector_store.similarity_search(query, k=2)

                # Create context from retrieved docs
                context = "\n".join([doc.page_content for doc in relevant_docs])

                # Query with context
                rag_prompt = f"""
                Com base no contexto abaixo, responda à pergunta:

                Contexto: {context}

                Pergunta: {query}

                Resposta:"""

                response = llm.invoke(rag_prompt)
                response_text = response.content if hasattr(response, 'content') else str(response)

                assert "AgentCore" in response_text, "Response doesn't mention AgentCore"

                print(f"✅ RAG response: {response_text[:100]}...")

        except Exception as e:
            pytest.fail(f"Vector store chat test failed: {e}")
        finally:
            self.tracer.end_trace(trace_id)

    def test_tool_assisted_chat(self):
        """Test chat with API tools"""
        print("\n🧪 Testing tool-assisted chat")

        trace_id = self.tracer.start_trace("tool_chat_test")

        try:
            with self.tracer.trace_event(trace_id, "tool_setup"):
                # Create mock OpenAPI spec for testing
                mock_openapi = {
                    "openapi": "3.0.0",
                    "info": {"title": "Test API", "version": "1.0.0"},
                    "servers": [{"url": "https://api.test.com"}],
                    "paths": {
                        "/weather": {
                            "get": {
                                "operationId": "get_weather",
                                "summary": "Get weather information",
                                "parameters": [
                                    {
                                        "name": "city",
                                        "in": "query",
                                        "required": True,
                                        "schema": {"type": "string"}
                                    }
                                ]
                            }
                        }
                    }
                }

                # Convert to tools
                tools = api2tool(mock_openapi)
                tool_functions = [tool['function'] for tool in tools]

                assert len(tool_functions) > 0, "No tools generated"

            with self.tracer.trace_event(trace_id, "agent_with_tools"):
                # Create agent with tools
                llm = get_llm("bedrock")
                agent = create_agent_graph(llm, tools=tool_functions)

                # Test tool-requiring query
                query = "Qual é o clima em São Paulo?"

                # Note: This will likely fail with actual API call, but tests the flow
                try:
                    result = agent.invoke({
                        "messages": [HumanMessage(content=query)]
                    })

                    response = result["messages"][-1].content
                    print(f"✅ Tool-assisted response: {response[:100]}...")

                except Exception as tool_error:
                    # Expected to fail with mock API, but flow should work
                    print(f"⚠️ Tool call failed as expected with mock API: {tool_error}")
                    assert "tool" in str(tool_error).lower() or "api" in str(tool_error).lower()

        except Exception as e:
            pytest.fail(f"Tool-assisted chat test failed: {e}")
        finally:
            self.tracer.end_trace(trace_id)

class TestPromptEvaluation:
    """Test prompt evaluation scenarios"""

    def test_prompt_evaluation_basic(self):
        """Test basic prompt evaluation"""
        print("\n🧪 Testing prompt evaluation")

        try:
            # Setup evaluator
            evaluator = PromptEvaluator("bedrock")

            # Test basic evaluation
            prompt = "Qual é a capital da França?"
            expected = "Paris"

            result = evaluator.evaluate_single(
                prompt=prompt,
                expected=expected,
                eval_type="semantic_similarity"
            )

            assert result.score >= 0.0, "Invalid score"
            assert result.score <= 1.0, "Score out of range"

            print(f"✅ Evaluation score: {result.score:.3f}")

        except Exception as e:
            pytest.fail(f"Prompt evaluation test failed: {e}")

    def test_dataset_evaluation(self):
        """Test evaluation on dataset"""
        print("\n🧪 Testing dataset evaluation")

        try:
            evaluator = PromptEvaluator("bedrock")

            # Create test dataset
            dataset = create_eval_dataset("basic_qa", size=3)

            # Run evaluation
            summary = evaluator.evaluate_dataset(
                dataset=dataset,
                eval_type="semantic_similarity",
                save_results=False
            )

            assert summary.total_samples == 3, "Wrong number of samples"
            assert 0.0 <= summary.avg_score <= 1.0, "Invalid average score"

            print(f"✅ Dataset evaluation - Avg score: {summary.avg_score:.3f}")

        except Exception as e:
            pytest.fail(f"Dataset evaluation test failed: {e}")

class TestModelComparison:
    """Test model comparison scenarios"""

    @pytest.mark.skipif(
        not os.getenv("ENABLE_MODEL_COMPARISON"),
        reason="Model comparison tests disabled"
    )
    def test_model_comparison(self):
        """Test model comparison"""
        print("\n🧪 Testing model comparison")

        try:
            from agentCore.evaluation import ModelComparator

            # Setup comparator with available providers
            available_providers = ["bedrock"]  # Add others if configured

            if os.getenv("OPENAI_API_KEY"):
                available_providers.append("openai")

            comparator = ModelComparator(available_providers)

            # Quick test dataset
            test_prompts = [
                "Qual é 2 + 2?",
                "Explique o que é machine learning em uma frase."
            ]
            expected_outputs = [
                "4",
                "Machine learning é uma área da inteligência artificial onde sistemas aprendem padrões dos dados para fazer previsões."
            ]

            # Run comparison
            result = comparator.quick_comparison(test_prompts, expected_outputs)

            assert len(result.models) > 0, "No models tested"
            assert result.best_model in available_providers, "Invalid best model"

            print(f"✅ Model comparison - Best: {result.best_model}")

        except Exception as e:
            pytest.fail(f"Model comparison test failed: {e}")

# Pytest configuration
def pytest_configure(config):
    """Configure pytest"""
    config.addinivalue_line(
        "markers", "slow: marks tests as slow (deselect with '-m \"not slow\"')"
    )
    config.addinivalue_line(
        "markers", "integration: marks tests as integration tests"
    )

if __name__ == "__main__":
    # Run tests directly
    pytest.main([__file__, "-v"])