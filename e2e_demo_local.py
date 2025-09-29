#!/usr/bin/env python3
"""
End-to-End Demo LOCAL - AgentCore com Ollama 100% Local

Este demo roda completamente local usando:
- Ollama para LLM
- ChromaDB local para vector store
- Sem dependências de cloud/APIs externas
"""

import os
import time
import json
from pathlib import Path

# Carregar configuração local
from dotenv import load_dotenv
load_dotenv('.env.local')

# AgentCore imports
from agentCore.providers import get_llm, get_embeddings, get_provider_info
from agentCore.graphs import create_agent_graph
from agentCore.utils import api2tool
from agentCore.evaluation import (
    PromptEvaluator,
    ModelComparator,
    create_eval_dataset,
    get_chat_scenario
)
from agentCore.reasoning import ChainOfThoughtReasoner
from agentCore.observability import get_tracer
from agentCore.chunking import TextChunker, ChunkProcessor, ChunkingStrategy
from agentCore.storage import get_vector_store
from agentCore.logger import get_logger
from langchain_core.messages import HumanMessage

# Setup logging
logger = get_logger("e2e_demo_local")

def check_ollama_status():
    """Verificar se Ollama está rodando"""
    try:
        import requests
        response = requests.get("http://localhost:11434/api/tags", timeout=5)
        if response.status_code == 200:
            models = response.json().get('models', [])
            model_names = [m['name'] for m in models]
            print(f"✅ Ollama rodando com {len(models)} modelos: {', '.join(model_names[:3])}")
            return True
        else:
            print("❌ Ollama não está respondendo")
            return False
    except Exception as e:
        print(f"❌ Ollama não está acessível: {e}")
        print("💡 Execute: ollama serve")
        return False

def demo_header(title: str):
    """Print demo section header"""
    print("\n" + "="*60)
    print(f"🏠 {title} (LOCAL)")
    print("="*60)

def demo_local_setup():
    """Demo setup local"""
    demo_header("CONFIGURAÇÃO LOCAL")

    if not check_ollama_status():
        print("\n❌ Ollama não está rodando. Execute:")
        print("   ollama serve")
        print("   ollama pull llama3.2:3b")
        return False

    try:
        # Testar provider
        provider_info = get_provider_info("ollama")
        print(f"🔧 Provider: {provider_info}")

        # Testar LLM
        llm = get_llm("ollama")
        print("✅ LLM local configurado")

        return True
    except Exception as e:
        print(f"❌ Erro na configuração: {e}")
        return False

def demo_local_chat():
    """Demo chat local"""
    demo_header("CHAT LOCAL COM OLLAMA")

    tracer = get_tracer()

    # 1. Chat Simples
    print("\n💬 1. Chat Simples Local")
    trace_id = tracer.start_trace("local_simple_chat")

    try:
        with tracer.trace_event(trace_id, "llm_setup"):
            llm = get_llm("ollama")

        with tracer.trace_event(trace_id, "simple_chat"):
            agent = create_agent_graph(llm, tools=None)

            result = agent.invoke({
                "messages": [HumanMessage(content="Olá! Em uma frase, o que é Python?")]
            })

            response = result["messages"][-1].content
            print(f"🤖 Resposta: {response}")

    except Exception as e:
        print(f"❌ Erro no chat simples: {e}")
    finally:
        tracer.end_trace(trace_id)

    # 2. Reasoning Local
    print("\n🧠 2. Reasoning Local")
    trace_id = tracer.start_trace("local_reasoning")

    try:
        with tracer.trace_event(trace_id, "reasoning_setup"):
            reasoner = ChainOfThoughtReasoner(llm)

        with tracer.trace_event(trace_id, "reasoning_task"):
            question = "Se eu tenho 50 reais e compro 2 livros de 15 reais cada, quanto sobra?"

            print(f"❓ Pergunta: {question}")
            reasoning_result = reasoner.reason(question)

            print(f"🧮 Resposta Final: {reasoning_result.final_answer}")
            print(f"📊 Passos: {len(reasoning_result.steps)}")
            print(f"🎯 Confiança: {reasoning_result.overall_confidence:.0%}")

    except Exception as e:
        print(f"❌ Erro no reasoning: {e}")
    finally:
        tracer.end_trace(trace_id)

def demo_local_vector_store():
    """Demo vector store local"""
    demo_header("VECTOR STORE LOCAL (RAG)")

    print("\n📚 RAG Local com ChromaDB")

    try:
        # Setup vector store local
        vector_store = get_vector_store(
            "chroma_local",
            {
                "persist_directory": "./demo_chroma_db",
                "collection_name": "agentcore_demo"
            }
        )

        # Documentos de exemplo
        docs = [
            "AgentCore é uma biblioteca Python para criar agentes de IA",
            "A biblioteca suporta múltiplos provedores LLM como Ollama",
            "Ollama permite rodar modelos de linguagem localmente",
            "ChromaDB é um banco de dados vetorial para busca semântica",
            "Python é uma linguagem de programação versátil e popular"
        ]

        print(f"📝 Adicionando {len(docs)} documentos...")
        vector_store.add_documents(docs)

        # Teste de busca
        query = "O que é AgentCore?"
        print(f"🔍 Buscando: {query}")

        results = vector_store.similarity_search(query, k=2)

        print("📋 Resultados encontrados:")
        for i, result in enumerate(results, 1):
            print(f"   {i}. {result.document.content}")

        # RAG completo
        print("\n🤖 RAG Completo:")
        llm = get_llm("ollama")

        context = "\n".join([r.document.content for r in results])
        rag_prompt = f"""
        Contexto: {context}

        Pergunta: {query}

        Resposta baseada no contexto:"""

        response = llm.invoke(rag_prompt)
        response_text = response.content if hasattr(response, 'content') else str(response)
        print(f"💡 Resposta RAG: {response_text}")

    except Exception as e:
        print(f"❌ Erro no vector store: {e}")

def demo_local_evaluation():
    """Demo evaluation local"""
    demo_header("AVALIAÇÃO LOCAL")

    print("\n📊 Sistema de Avaliação Local")

    try:
        evaluator = PromptEvaluator("ollama")

        # Teste simples
        print("\n🔍 Avaliação Simples:")
        result = evaluator.evaluate_single(
            prompt="Quanto é 2 + 2?",
            expected="4",
            eval_type="semantic_similarity"
        )

        print(f"Score: {result.score:.3f}")
        print(f"Resposta: {result.actual}")

        # Dataset pequeno
        print("\n📈 Avaliação de Dataset:")
        dataset = create_eval_dataset("basic_qa", size=2)  # Apenas 2 amostras

        summary = evaluator.evaluate_dataset(
            dataset=dataset,
            eval_type="semantic_similarity",
            save_results=False
        )

        print(f"Amostras: {summary.total_samples}")
        print(f"Score médio: {summary.avg_score:.3f}")
        print(f"Tempo: {summary.total_time_ms:.0f}ms")

    except Exception as e:
        print(f"❌ Erro na avaliação: {e}")

def demo_local_chunking():
    """Demo chunking local"""
    demo_header("CHUNKING LOCAL")

    print("\n✂️ Estratégias de Chunking")

    sample_text = """
    Ollama é uma ferramenta que permite executar grandes modelos de linguagem localmente.
    Com Ollama, você pode rodar modelos como Llama, Mistral, e outros em sua própria máquina.
    Isso garante privacidade e controle total sobre seus dados.
    AgentCore integra perfeitamente com Ollama para criar agentes inteligentes locais.
    """

    try:
        chunker = TextChunker(chunk_size=100, overlap=20)

        strategies = [ChunkingStrategy.SENTENCE, ChunkingStrategy.ADAPTIVE]

        for strategy in strategies:
            print(f"\n📄 {strategy.value.upper()}:")

            result = chunker.chunk_text(sample_text.strip(), strategy)

            print(f"   Chunks: {result.total_chunks}")
            print(f"   Tokens: {result.total_tokens}")

            if result.chunks:
                print(f"   Exemplo: {result.chunks[0].content[:80]}...")

    except Exception as e:
        print(f"❌ Erro no chunking: {e}")

def demo_local_performance():
    """Demo performance local"""
    demo_header("PERFORMANCE LOCAL")

    print("\n⚡ Teste de Performance")

    try:
        llm = get_llm("ollama")

        # Teste de velocidade
        start_time = time.time()

        simple_queries = [
            "Olá",
            "Quanto é 5+5?",
            "Explique IA em 10 palavras"
        ]

        for i, query in enumerate(simple_queries, 1):
            query_start = time.time()
            response = llm.invoke(query)
            query_time = (time.time() - query_start) * 1000

            response_text = response.content if hasattr(response, 'content') else str(response)
            print(f"   Query {i}: {query_time:.0f}ms - {response_text[:50]}...")

        total_time = (time.time() - start_time) * 1000
        print(f"\n📊 Tempo total: {total_time:.0f}ms")
        print(f"📊 Média por query: {total_time/len(simple_queries):.0f}ms")

    except Exception as e:
        print(f"❌ Erro no teste de performance: {e}")

def demo_local_summary():
    """Demo summary"""
    demo_header("RESUMO LOCAL")

    print("""
🎉 Demo Local Completado!

✅ Funcionalidades Testadas Localmente:
   🏠 Ollama como provedor LLM
   💬 Chat e reasoning local
   📚 Vector store com ChromaDB
   📊 Sistema de avaliação
   ✂️ Chunking de textos
   ⚡ Testes de performance
   👁️ Observabilidade completa

🚀 Vantagens da Configuração Local:
   • 🔒 Total privacidade dos dados
   • 💰 Sem custos de API
   • 🌐 Funciona offline
   • 🎛️ Controle total
   • ⚡ Latência baixa (rede local)

💡 Modelos Recomendados para Produção Local:
   • llama3.2:3b  - Rápido, boa qualidade
   • llama3.2:8b  - Melhor qualidade, mais lento
   • mistral:7b   - Alternativa eficiente
   • codellama:7b - Para código

🔧 Próximos Passos:
   • Testar diferentes modelos
   • Otimizar configurações para seu hardware
   • Implementar cache de respostas
   • Configurar GPU se disponível
    """)

def main():
    """Run complete local demo"""
    print("🏠 AgentCore Enhanced Features - Demo 100% LOCAL com Ollama")
    print("=" * 70)

    try:
        if not demo_local_setup():
            return

        # Run all local demos
        demo_local_chat()
        demo_local_vector_store()
        demo_local_evaluation()
        demo_local_chunking()
        demo_local_performance()
        demo_local_summary()

    except KeyboardInterrupt:
        print("\n⏹️ Demo interrompido pelo usuário")
    except Exception as e:
        print(f"\n❌ Demo falhou: {e}")
        import traceback
        traceback.print_exc()

if __name__ == "__main__":
    main()