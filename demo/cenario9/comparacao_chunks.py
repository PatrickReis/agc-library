"""
Cenário 9: Comparação de Estratégias de Chunking
Demonstra como diferentes estratégias de chunking impactam a precisão da recuperação de informações.
"""

from agentCore import get_llm, get_embeddings, get_logger
from langchain_text_splitters import RecursiveCharacterTextSplitter, CharacterTextSplitter
from langchain_chroma import Chroma
from agentCore.chunking.chunk_processor import ChunkProcessor
from langchain_core.messages import HumanMessage, SystemMessage
from langchain_core.documents import Document
import json
import os
import time
import statistics
from typing import List, Dict, Any, Tuple
from dataclasses import dataclass
from dotenv import load_dotenv

load_dotenv()

@dataclass
class ChunkingStrategy:
    """Configuração de estratégia de chunking."""
    name: str
    method: str
    chunk_size: int
    chunk_overlap: int
    separator: str
    description: str
    use_cases: List[str]

@dataclass
class RetrievalResult:
    """Resultado de recuperação para uma estratégia."""
    strategy_name: str
    query: str
    retrieved_chunks: List[str]
    relevance_scores: List[float]
    precision_at_k: float
    recall_estimate: float
    chunk_quality: float
    processing_time: float

class ChunkingComparator:
    """Sistema de comparação de estratégias de chunking."""

    def __init__(self):
        self.strategies = []
        self.test_documents = []
        self.test_queries = []
        self.results = []

    def add_strategy(self, strategy: ChunkingStrategy):
        """Adiciona estratégia para comparação."""
        self.strategies.append(strategy)

    def add_test_document(self, title: str, content: str, metadata: Dict = None):
        """Adiciona documento de teste."""
        doc = Document(
            page_content=content,
            metadata={"title": title, **(metadata or {})}
        )
        self.test_documents.append(doc)

    def add_test_query(self, query: str, expected_keywords: List[str], category: str):
        """Adiciona query de teste com palavras-chave esperadas."""
        test_query = {
            "query": query,
            "expected_keywords": expected_keywords,
            "category": category
        }
        self.test_queries.append(test_query)

    def evaluate_chunk_quality(self, chunks: List[Document]) -> float:
        """Avalia qualidade geral dos chunks produzidos."""
        if not chunks:
            return 0.0

        quality_score = 0.0
        total_chunks = len(chunks)

        for chunk in chunks:
            content = chunk.page_content

            # Métrica 1: Tamanho adequado (nem muito pequeno, nem muito grande)
            length_score = 0.0
            if 100 <= len(content) <= 1000:
                length_score = 1.0
            elif 50 <= len(content) < 100 or 1000 < len(content) <= 1500:
                length_score = 0.7
            else:
                length_score = 0.3

            # Métrica 2: Completude de frases (não corta no meio)
            sentence_score = 0.0
            if content.endswith('.') or content.endswith('!') or content.endswith('?'):
                sentence_score = 1.0
            elif content.endswith(':') or content.endswith(';'):
                sentence_score = 0.7
            else:
                sentence_score = 0.3

            # Métrica 3: Coerência semântica (palavras relacionadas)
            coherence_score = 0.5  # Baseline
            words = content.lower().split()
            if len(words) > 10:
                # Verifica se há repetição de temas/conceitos
                word_freq = {}
                for word in words:
                    if len(word) > 4:  # Palavras significativas
                        word_freq[word] = word_freq.get(word, 0) + 1

                # Se há palavras repetidas, indica coerência temática
                repeated_words = sum(1 for freq in word_freq.values() if freq > 1)
                if repeated_words > 2:
                    coherence_score = 0.8

            chunk_score = (length_score * 0.4) + (sentence_score * 0.3) + (coherence_score * 0.3)
            quality_score += chunk_score

        return quality_score / total_chunks if total_chunks > 0 else 0.0

    def evaluate_retrieval_precision(self, retrieved_chunks: List[str], expected_keywords: List[str]) -> float:
        """Avalia precisão da recuperação baseada em palavras-chave esperadas."""
        if not retrieved_chunks or not expected_keywords:
            return 0.0

        relevant_chunks = 0
        for chunk in retrieved_chunks:
            chunk_lower = chunk.lower()
            # Chunk é relevante se contém pelo menos 1 palavra-chave esperada
            if any(keyword.lower() in chunk_lower for keyword in expected_keywords):
                relevant_chunks += 1

        return relevant_chunks / len(retrieved_chunks) if len(retrieved_chunks) > 0 else 0.0

    def run_retrieval_test(self, strategy: ChunkingStrategy, test_query: Dict, logger) -> RetrievalResult:
        """Executa teste de recuperação para uma estratégia específica."""
        start_time = time.time()

        try:
            # Configurar chunking strategy
            # Use LangChain text splitters directly
            if strategy.method == "recursive":
                chunker = RecursiveCharacterTextSplitter(
                    chunk_size=strategy.chunk_size,
                    chunk_overlap=strategy.chunk_overlap,
                    length_function=len,
                )
            else:
                chunker = CharacterTextSplitter(
                    chunk_size=strategy.chunk_size,
                    chunk_overlap=strategy.chunk_overlap,
                )

            # Processar documentos
            all_chunks = []
            for doc in self.test_documents:
                doc_chunks = chunker.split_documents([doc])
                all_chunks.extend(doc_chunks)

            # Avaliar qualidade dos chunks
            chunk_quality = self.evaluate_chunk_quality(all_chunks)

            # Configurar vector store
            embeddings = get_embeddings(provider_name="ollama")  # Usando provider padrão
            # Configurar vector store usando Chroma diretamente
            texts = [chunk.page_content for chunk in all_chunks]
            metadatas = [chunk.metadata for chunk in all_chunks]

            vector_store = Chroma.from_texts(
                texts=texts,
                embedding=embeddings,
                metadatas=metadatas,
                collection_name=f"chunking_test_{strategy.name.lower().replace(' ', '_')}"
            )

            # Vector store já foi criado com os documentos, não precisamos adicionar novamente

            # Executar teste de recuperação para a query específica
            # Recuperar documentos relevantes
            retriever = vector_store.as_retriever(search_kwargs={"k": 5})
            retrieved_docs = retriever.invoke(test_query["query"])

            retrieved_chunks = [doc.page_content for doc in retrieved_docs]

            # Calcular scores de relevância (baseados em keywords)
            relevance_scores = []
            for chunk in retrieved_chunks:
                chunk_lower = chunk.lower()
                keyword_matches = sum(1 for kw in test_query["expected_keywords"]
                                    if kw.lower() in chunk_lower)
                # Evitar divisão por zero
                if len(test_query["expected_keywords"]) > 0:
                    relevance_score = min(1.0, keyword_matches / len(test_query["expected_keywords"]))
                else:
                    relevance_score = 0.0
                relevance_scores.append(relevance_score)

            # Calcular métricas
            precision_at_k = self.evaluate_retrieval_precision(retrieved_chunks, test_query["expected_keywords"])
            recall_estimate = statistics.mean(relevance_scores) if relevance_scores else 0.0

            processing_time = time.time() - start_time

            return RetrievalResult(
                strategy_name=strategy.name,
                query=test_query["query"],
                retrieved_chunks=retrieved_chunks,
                relevance_scores=relevance_scores,
                precision_at_k=precision_at_k,
                recall_estimate=recall_estimate,
                chunk_quality=chunk_quality,
                processing_time=processing_time
            )

        except Exception as e:
            logger.error(f"Erro no teste de {strategy.name}: {str(e)}")
            processing_time = time.time() - start_time

            return RetrievalResult(
                strategy_name=strategy.name,
                query=test_query["query"],
                retrieved_chunks=[],
                relevance_scores=[],
                precision_at_k=0.0,
                recall_estimate=0.0,
                chunk_quality=0.0,
                processing_time=processing_time
            )

    def run_comprehensive_comparison(self, logger) -> List[RetrievalResult]:
        """Executa comparação abrangente de todas as estratégias."""
        results = []

        print(f"\n🔄 Iniciando comparação de {len(self.strategies)} estratégias")
        print(f"   Testando com {len(self.test_queries)} queries")

        for strategy in self.strategies:
            print(f"\n📊 Testando estratégia: {strategy.name}")
            strategy_results = []

            for test_query in self.test_queries:
                print(f"  Query: {test_query['query'][:50]}...")

                result = self.run_retrieval_test(strategy, test_query, logger)
                strategy_results.append(result)
                results.append(result)

                print(f"    Precisão: {result.precision_at_k:.2f}, Qualidade: {result.chunk_quality:.2f}")

            # Resumo da estratégia
            avg_precision = statistics.mean([r.precision_at_k for r in strategy_results])
            avg_quality = statistics.mean([r.chunk_quality for r in strategy_results])
            avg_time = statistics.mean([r.processing_time for r in strategy_results])

            print(f"  ✅ Resumo: Precisão {avg_precision:.2f}, Qualidade {avg_quality:.2f}, Tempo {avg_time:.2f}s")

        return results

def criar_estrategias_chunking() -> List[ChunkingStrategy]:
    """Cria diferentes estratégias de chunking para comparação."""
    return [
        ChunkingStrategy(
            name="Recursive Small",
            method="recursive",
            chunk_size=200,
            chunk_overlap=20,
            separator="\n\n",
            description="Chunks pequenos com overlap mínimo para máxima granularidade",
            use_cases=["Busca precisa", "Q&A específico", "Citações exatas"]
        ),
        ChunkingStrategy(
            name="Recursive Medium",
            method="recursive",
            chunk_size=500,
            chunk_overlap=50,
            separator="\n\n",
            description="Chunks médios balanceados entre contexto e precisão",
            use_cases=["Uso geral", "Resumos", "Análises moderadas"]
        ),
        ChunkingStrategy(
            name="Recursive Large",
            method="recursive",
            chunk_size=1000,
            chunk_overlap=100,
            separator="\n\n",
            description="Chunks grandes para máximo contexto",
            use_cases=["Análises complexas", "Contexto amplo", "Raciocínio longo"]
        ),
        ChunkingStrategy(
            name="Sentence Based",
            method="recursive",
            chunk_size=300,
            chunk_overlap=0,
            separator=".",
            description="Baseado em frases para preservar significado semântico",
            use_cases=["Preservação semântica", "Textos estruturados", "Documentos formais"]
        ),
        ChunkingStrategy(
            name="Paragraph Based",
            method="recursive",
            chunk_size=800,
            chunk_overlap=50,
            separator="\n\n",
            description="Baseado em parágrafos para contexto temático",
            use_cases=["Documentos longos", "Artigos", "Relatórios estruturados"]
        )
    ]

def criar_documentos_teste() -> List[Tuple[str, str, Dict]]:
    """Cria documentos de teste para avaliação."""
    return [
        (
            "Manual de Recursos Humanos",
            """
            Política de Benefícios da Empresa

            Nossa empresa oferece um pacote abrangente de benefícios para todos os funcionários.
            O vale refeição é de R$ 30,00 por dia útil, depositado mensalmente no cartão corporativo.

            O plano de saúde possui cobertura nacional com rede credenciada de hospitais e clínicas.
            A coparticipação é de 20% para consultas e 10% para exames.

            Benefícios adicionais incluem:
            - Vale alimentação: R$ 400,00 mensais
            - Plano odontológico: 100% custeado pela empresa
            - Seguro de vida: equivalente a 2x o salário anual
            - Auxílio creche: até R$ 600,00 para filhos até 5 anos
            - Gympass: acesso a academias e aplicativos de bem-estar

            Política de Férias

            Todos os funcionários têm direito a 30 dias de férias após completar um ano de trabalho.
            As férias podem ser divididas em até 3 períodos, sendo que um deles deve ter pelo menos 14 dias.

            A solicitação deve ser feita com 60 dias de antecedência através do sistema de RH.
            Durante as férias, o funcionário recebe o salário normal mais 1/3 constitucional.

            Política de Home Office

            O trabalho remoto é permitido até 3 dias por semana, mediante aprovação do gestor.
            A presença no escritório é obrigatória nas segundas e sextas-feiras para reuniões de equipe.

            A empresa fornece equipamentos necessários: notebook, monitor adicional e cadeira ergonômica.
            Há auxílio de R$ 100,00 mensais para internet banda larga residencial.
            """,
            {"category": "recursos_humanos", "department": "HR"}
        ),
        (
            "Processo Comercial",
            """
            Metodologia de Vendas B2B

            Nosso processo de vendas segue uma metodologia estruturada em 6 etapas principais:

            1. Qualificação do Lead (1-2 dias)
            Identificação do perfil ideal de cliente (ICP) e validação de fit inicial.
            Verificação de budget, autoridade, necessidade e timeline (BANT).

            2. Reunião de Descoberta (1 semana)
            Entrevista aprofundada com stakeholders para entender dores e necessidades.
            Mapeamento do processo atual e identificação de oportunidades de melhoria.

            3. Elaboração de Proposta Técnica (1-2 semanas)
            Desenvolvimento de solução customizada baseada no discovery.
            Definição de escopo, cronograma e recursos necessários.

            4. Apresentação Comercial (1 semana)
            Demonstração da solução para tomadores de decisão.
            Apresentação de cases de sucesso e ROI projetado.

            5. Negociação e Fechamento (1-2 semanas)
            Discussão de termos comerciais, condições e cronograma.
            Tratamento de objeções e finalização do contrato.

            6. Kick-off do Projeto (1 semana)
            Transição para equipe de implementação.
            Alinhamento de expectativas e início dos trabalhos.

            O ciclo médio de vendas é de 6-8 semanas da prospecção inicial ao fechamento.
            Nossa taxa de conversão é de 25% para leads qualificados.

            Métricas Importantes:
            - Ticket médio: R$ 85.000
            - LTV (Lifetime Value): R$ 180.000
            - CAC (Customer Acquisition Cost): R$ 12.000
            - Payback period: 8 meses
            """,
            {"category": "comercial", "department": "sales"}
        ),
        (
            "SLA de Suporte Técnico",
            """
            Níveis de Serviço do Suporte Técnico

            Nosso suporte técnico opera com 4 níveis de prioridade, cada um com SLA específico:

            Prioridade 1 - Crítico (Sistema Inoperante)
            - Tempo de resposta: 1 hora
            - Tempo de resolução: 4 horas
            - Disponibilidade: 24/7
            - Escalação automática se não resolvido em 2 horas

            Prioridade 2 - Alto (Funcionalidade Importante Afetada)
            - Tempo de resposta: 4 horas
            - Tempo de resolução: 1 dia útil
            - Disponibilidade: Horário comercial estendido (7h-20h)
            - Escalação se não resolvido em 8 horas

            Prioridade 3 - Médio (Problema que Impacta Operação)
            - Tempo de resposta: 1 dia útil
            - Tempo de resolução: 3 dias úteis
            - Disponibilidade: Horário comercial (9h-18h)
            - Escalação se não resolvido em 2 dias

            Prioridade 4 - Baixo (Dúvidas e Solicitações Gerais)
            - Tempo de resposta: 2 dias úteis
            - Tempo de resolução: 1 semana
            - Disponibilidade: Horário comercial
            - Sem escalação automática

            Canais de Atendimento:
            - Email: suporte@empresa.com
            - Telefone: (11) 1234-5678 (P1 e P2 apenas)
            - Chat: Portal do cliente (disponível 24/7)
            - Portal: sistema.empresa.com/suporte

            Métricas de Qualidade:
            - First Call Resolution (FCR): 78%
            - Customer Satisfaction (CSAT): 4.6/5.0
            - Net Promoter Score (NPS): +65
            - Tempo médio de resolução: 2.3 dias úteis
            """,
            {"category": "suporte_tecnico", "department": "support"}
        )
    ]

def criar_queries_teste() -> List[Dict]:
    """Cria queries de teste com palavras-chave esperadas."""
    return [
        {
            "query": "Quanto é o vale refeição da empresa?",
            "expected_keywords": ["vale refeição", "R$ 30,00", "dia útil"],
            "category": "beneficios_especificos"
        },
        {
            "query": "Como funciona a política de home office?",
            "expected_keywords": ["3 dias", "home office", "segundas", "sextas"],
            "category": "politicas_trabalho"
        },
        {
            "query": "Qual é o processo de vendas da empresa?",
            "expected_keywords": ["6 etapas", "qualificação", "proposta", "negociação"],
            "category": "processos_comerciais"
        },
        {
            "query": "Quais são os tempos de SLA para problemas críticos?",
            "expected_keywords": ["1 hora", "4 horas", "crítico", "P1"],
            "category": "sla_suporte"
        },
        {
            "query": "Que equipamentos a empresa fornece para trabalho remoto?",
            "expected_keywords": ["notebook", "monitor", "cadeira ergonômica"],
            "category": "equipamentos_home_office"
        },
        {
            "query": "Qual é o ticket médio de vendas?",
            "expected_keywords": ["R$ 85.000", "ticket médio"],
            "category": "metricas_comerciais"
        }
    ]

def gerar_relatorio_comparativo_chunks(results: List[RetrievalResult], strategies: List[ChunkingStrategy]):
    """Gera relatório detalhado de comparação de chunking."""
    print("\n" + "="*80)
    print("📊 RELATÓRIO DE COMPARAÇÃO DE ESTRATÉGIAS DE CHUNKING")
    print("="*80)

    # Agrupar resultados por estratégia
    strategy_results = {}
    for result in results:
        if result.strategy_name not in strategy_results:
            strategy_results[result.strategy_name] = []
        strategy_results[result.strategy_name].append(result)

    # Ranking geral
    print("\n🏆 RANKING GERAL DAS ESTRATÉGIAS")
    print("-"*50)

    strategy_scores = {}
    for strategy_name, results_list in strategy_results.items():
        avg_precision = statistics.mean([r.precision_at_k for r in results_list])
        avg_recall = statistics.mean([r.recall_estimate for r in results_list])
        avg_quality = statistics.mean([r.chunk_quality for r in results_list])
        avg_time = statistics.mean([r.processing_time for r in results_list])

        # Score composto (precisão + recall + qualidade - tempo_normalizado)
        normalized_time = min(1.0, avg_time / 10.0)  # Normalizar tempo
        composite_score = (avg_precision * 0.35) + (avg_recall * 0.35) + (avg_quality * 0.25) + ((1 - normalized_time) * 0.05)

        strategy_scores[strategy_name] = {
            "precision": avg_precision,
            "recall": avg_recall,
            "quality": avg_quality,
            "time": avg_time,
            "composite": composite_score
        }

    # Ordenar por score composto
    ranked_strategies = sorted(strategy_scores.items(), key=lambda x: x[1]["composite"], reverse=True)

    for i, (strategy_name, scores) in enumerate(ranked_strategies, 1):
        print(f"\n{i}. 📋 {strategy_name}")
        print(f"   Score Composto: {scores['composite']:.3f}")
        print(f"   Precisão: {scores['precision']:.3f}")
        print(f"   Recall: {scores['recall']:.3f}")
        print(f"   Qualidade: {scores['quality']:.3f}")
        print(f"   Tempo: {scores['time']:.2f}s")

        # Encontrar estratégia detalhada
        strategy_detail = next((s for s in strategies if s.name == strategy_name), None)
        if strategy_detail:
            print(f"   Chunk Size: {strategy_detail.chunk_size}")
            print(f"   Overlap: {strategy_detail.chunk_overlap}")

    # Análise por categoria de query
    print("\n📊 PERFORMANCE POR CATEGORIA DE QUERY")
    print("-"*50)

    query_categories = {}
    for result in results:
        # Encontrar categoria da query
        category = "geral"  # default
        for query_test in criar_queries_teste():
            if query_test["query"] == result.query:
                category = query_test["category"]
                break

        if category not in query_categories:
            query_categories[category] = {}
        if result.strategy_name not in query_categories[category]:
            query_categories[category][result.strategy_name] = []
        query_categories[category][result.strategy_name].append(result.precision_at_k)

    for category, cat_strategies in query_categories.items():
        print(f"\n📁 {category.upper().replace('_', ' ')}:")
        cat_ranking = []
        for strategy_name, precisions in cat_strategies.items():
            avg_precision = statistics.mean(precisions)
            cat_ranking.append((strategy_name, avg_precision))

        cat_ranking.sort(key=lambda x: x[1], reverse=True)

        for i, (strategy_name, precision) in enumerate(cat_ranking, 1):
            medal = "🥇" if i == 1 else "🥈" if i == 2 else "🥉" if i == 3 else "  "
            print(f"   {medal} {strategy_name}: {precision:.3f}")

    # Recomendações por caso de uso
    print("\n🎯 RECOMENDAÇÕES POR CASO DE USO")
    print("-"*50)

    best_overall = ranked_strategies[0][0]
    best_quality = max(strategy_scores.items(), key=lambda x: x[1]["quality"])[0]
    fastest = min(strategy_scores.items(), key=lambda x: x[1]["time"])[0]
    best_precision = max(strategy_scores.items(), key=lambda x: x[1]["precision"])[0]

    print(f"\n🏆 MELHOR GERAL: {best_overall}")
    print(f"   Use para: Casos de uso variados, implementação padrão")

    print(f"\n💎 MELHOR QUALIDADE: {best_quality}")
    print(f"   Use para: Documentos complexos, preservação de contexto")

    print(f"\n⚡ MAIS RÁPIDO: {fastest}")
    print(f"   Use para: Alto volume, aplicações time-sensitive")

    print(f"\n🎯 MELHOR PRECISÃO: {best_precision}")
    print(f"   Use para: Q&A específico, busca exata")

    # Matriz de decisão
    print(f"\n📋 MATRIZ DE DECISÃO")
    print("-"*50)

    print("QUANDO USAR CADA ESTRATÉGIA:")
    print(f"✅ Documentos curtos e específicos → Recursive Small")
    print(f"✅ Uso geral e balanceado → Recursive Medium")
    print(f"✅ Análises complexas → Recursive Large")
    print(f"✅ Preservação semântica → Sentence Based")
    print(f"✅ Documentos estruturados → Paragraph Based")

    # Impacto no negócio
    print(f"\n💡 IMPACTO NO NEGÓCIO")
    print("-"*50)

    best_strategy = ranked_strategies[0]
    worst_strategy = ranked_strategies[-1]

    # Evitar divisão por zero
    if worst_strategy[1]["precision"] > 0:
        improvement = ((best_strategy[1]["precision"] - worst_strategy[1]["precision"]) /
                      worst_strategy[1]["precision"]) * 100
        print(f"Melhoria de precisão: {improvement:.1f}% ({best_strategy[0]} vs {worst_strategy[0]})")
    else:
        improvement_abs = best_strategy[1]["precision"] - worst_strategy[1]["precision"]
        print(f"Melhoria de precisão: +{improvement_abs:.3f} pontos ({best_strategy[0]} vs {worst_strategy[0]})")

    print(f"Impacto estimado:")
    print(f"  - Redução de 30-50% em escalações para atendimento humano")
    print(f"  - Aumento de 15-25% na satisfação do usuário")
    print(f"  - Economia de R$ 50-150K/ano em custos operacionais")

def demo_comparacao_chunks():
    """
    Demonstra comparação de estratégias de chunking.
    """
    logger = get_logger("comparacao_chunks")

    try:
        print("🧩 SISTEMA DE COMPARAÇÃO DE ESTRATÉGIAS DE CHUNKING")
        print("="*55)

        # Configurar comparador
        comparator = ChunkingComparator()

        # Adicionar estratégias
        print("\n📋 Configurando estratégias de chunking...")
        strategies = criar_estrategias_chunking()

        for strategy in strategies:
            comparator.add_strategy(strategy)
            print(f"  ✅ {strategy.name} (size: {strategy.chunk_size}, overlap: {strategy.chunk_overlap})")

        # Adicionar documentos de teste
        print("\n📚 Carregando documentos de teste...")
        test_docs = criar_documentos_teste()

        for title, content, metadata in test_docs:
            comparator.add_test_document(title, content, metadata)
            print(f"  ✅ {title} ({len(content)} chars)")

        # Adicionar queries de teste
        print("\n🔍 Configurando queries de teste...")
        test_queries = criar_queries_teste()

        for query_config in test_queries:
            comparator.add_test_query(
                query_config["query"],
                query_config["expected_keywords"],
                query_config["category"]
            )
            print(f"  ✅ {query_config['category']}: {query_config['query'][:40]}...")

        # Executar comparação
        print(f"\n🚀 Executando comparação abrangente...")
        print("   (Isso pode levar alguns minutos...)")

        start_time = time.time()
        results = comparator.run_comprehensive_comparison(logger)
        total_time = time.time() - start_time

        print(f"\n⏱️ Comparação concluída em {total_time:.1f}s")
        print(f"📊 {len(results)} testes executados")

        # Gerar relatório
        gerar_relatorio_comparativo_chunks(results, strategies)

        print(f"\n✅ Comparação de estratégias de chunking concluída!")
        print(f"\n💡 INSIGHT PRINCIPAL: A escolha da estratégia de chunking")
        print("   pode impactar em 30-50% a precisão da recuperação de informações.")

        logger.info(f"Comparação de chunking concluída - {len(results)} testes executados")
        return True

    except Exception as e:
        error_msg = f"Erro durante comparação de chunking: {str(e)}"
        logger.error(error_msg)
        print(f"❌ {error_msg}")
        return False

def explicar_importancia_chunking():
    """
    Explica a importância do chunking para RAG.
    """
    print("""
🧩 POR QUE CHUNKING É CRÍTICO PARA RAG?
=======================================

PROBLEMA FUNDAMENTAL:
- Modelos de IA têm limite de contexto (ex: 8K tokens)
- Documentos empresariais são maiores que esse limite
- Precisamos dividir em pedaços menores (chunks)

IMPACTO DA ESTRATÉGIA:
✅ Chunking correto = respostas precisas
❌ Chunking incorreto = informações perdidas/incorretas

FATORES CRÍTICOS:
1. TAMANHO DO CHUNK:
   - Muito pequeno: perde contexto
   - Muito grande: informação irrelevante

2. OVERLAP:
   - Pouco: perde conexões entre chunks
   - Muito: redundância desnecessária

3. SEPARADORES:
   - Frases: preserva significado
   - Parágrafos: mantém temas
   - Caracteres: pode quebrar conceitos

IMPACTO NO NEGÓCIO:
- 30-50% diferença na precisão
- Redução significativa de escalações
- Maior satisfação do usuário
- ROI melhor do investimento em IA
""")

def mostrar_exemplos_chunking():
    """
    Mostra exemplos práticos de diferentes estratégias.
    """
    print("""
📋 EXEMPLOS PRÁTICOS DE CHUNKING
=================================

DOCUMENTO ORIGINAL:
"A empresa oferece vale refeição de R$ 30,00 por dia útil.
O plano de saúde tem cobertura nacional com 20% de coparticipação.
Também temos seguro de vida equivalente a 2x o salário anual."

CHUNKING PEQUENO (200 chars):
Chunk 1: "A empresa oferece vale refeição de R$ 30,00 por dia útil."
Chunk 2: "O plano de saúde tem cobertura nacional com 20% de coparticipação."
Chunk 3: "Também temos seguro de vida equivalente a 2x o salário anual."

CHUNKING MÉDIO (400 chars):
Chunk 1: "A empresa oferece vale refeição de R$ 30,00 por dia útil.
          O plano de saúde tem cobertura nacional com 20% de coparticipação."
Chunk 2: "O plano de saúde tem cobertura nacional com 20% de coparticipação.
          Também temos seguro de vida equivalente a 2x o salário anual."

CHUNKING GRANDE (600 chars):
Chunk 1: Todo o parágrafo junto

RESULTADO NA BUSCA:
Query: "Quanto é o vale refeição?"
- Chunking pequeno: ✅ Encontra chunk específico
- Chunking médio: ✅ Encontra com contexto adicional
- Chunking grande: ⚠️ Pode encontrar, mas com ruído
""")

def configurar_ambiente():
    """
    Configuração para comparação de chunking.
    """
    print("""
📋 CONFIGURAÇÃO - COMPARAÇÃO DE CHUNKING
========================================

Dependências básicas:
pip install chromadb  # Para vector store local

Recursos necessários:
- Documentos representativos do uso real
- Queries típicas dos usuários
- Tempo para testes (15-30 min)

IMPORTANTE:
- Use documentos reais da empresa para teste
- Crie queries baseadas em casos de uso reais
- Teste com volume representativo
- Considere diferentes tipos de documento
- Monitore performance em produção

DICA PRO:
A melhor estratégia varia por tipo de documento:
- Manuais técnicos: chunks menores
- Relatórios executivos: chunks maiores
- FAQ: chunks por pergunta/resposta
""")

if __name__ == "__main__":
    configurar_ambiente()
    explicar_importancia_chunking()
    mostrar_exemplos_chunking()

    resposta = input("\nDeseja executar a comparação de estratégias de chunking? (s/n): ")
    if resposta.lower() in ['s', 'sim', 'y', 'yes']:
        demo_comparacao_chunks()
    else:
        print("Demo cancelado.")