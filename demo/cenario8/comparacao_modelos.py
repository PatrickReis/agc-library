"""
Cenário 8: Comparação Abrangente de Modelos de IA
Demonstra metodologia científica para escolher o melhor modelo para cada caso de uso.
"""

from agentCore import get_llm, get_logger
from agentCore.evaluation.model_comparison import ModelComparator
from langchain_core.messages import HumanMessage, SystemMessage
import json
import os
import time
import statistics
import matplotlib.pyplot as plt
import pandas as pd
from datetime import datetime
from typing import List, Dict, Any, Tuple
from dataclasses import dataclass, asdict
from dotenv import load_dotenv

load_dotenv()

@dataclass
class ModelSpec:
    """Especificação detalhada de um modelo."""
    name: str
    provider: str
    model_id: str
    context_window: int
    max_tokens: int
    cost_per_1k_tokens: float
    latency_expected: float
    strengths: List[str]
    limitations: List[str]
    use_cases: List[str]

@dataclass
class BenchmarkResult:
    """Resultado de benchmark para um modelo."""
    model_name: str
    category: str
    test_name: str
    score: float
    execution_time: float
    tokens_used: int
    cost: float
    error_rate: float
    consistency: float

class ModelBenchmark:
    """Sistema abrangente de benchmark de modelos."""

    def __init__(self):
        self.models = {}
        self.benchmarks = []
        self.results = []

    def register_model(self, spec: ModelSpec):
        """Registra um modelo para comparação."""
        self.models[spec.name] = spec

    def add_benchmark(self, name: str, category: str, test_cases: List[Dict], evaluation_criteria: Dict):
        """Adiciona um benchmark específico."""
        benchmark = {
            "name": name,
            "category": category,
            "test_cases": test_cases,
            "criteria": evaluation_criteria
        }
        self.benchmarks.append(benchmark)

    def evaluate_reasoning_capability(self, response: str, expected_steps: List[str]) -> float:
        """Avalia capacidade de raciocínio lógico."""
        response_lower = response.lower()
        score = 0.0

        # Verifica se seguiu etapas lógicas
        for step in expected_steps:
            if step.lower() in response_lower:
                score += 0.3

        # Verifica estrutura de raciocínio
        reasoning_indicators = ["primeiro", "segundo", "então", "portanto", "porque", "logo"]
        reasoning_count = sum(1 for indicator in reasoning_indicators if indicator in response_lower)
        score += min(0.4, reasoning_count * 0.1)

        return min(1.0, score)

    def evaluate_factual_accuracy(self, response: str, facts: List[str]) -> float:
        """Avalia precisão factual."""
        response_lower = response.lower()
        correct_facts = 0

        for fact in facts:
            if fact.lower() in response_lower:
                correct_facts += 1

        return correct_facts / len(facts) if facts else 0.0

    def evaluate_creativity(self, response: str) -> float:
        """Avalia criatividade e originalidade."""
        # Métricas simples de criatividade
        unique_words = len(set(response.lower().split()))
        total_words = len(response.split())

        if total_words == 0:
            return 0.0

        vocabulary_diversity = unique_words / total_words

        # Verifica uso de linguagem elaborada
        sophisticated_words = ["innovative", "comprehensive", "strategic", "optimize", "enhance"]
        sophistication = sum(1 for word in sophisticated_words if word in response.lower())

        creativity_score = (vocabulary_diversity * 0.6) + (min(1.0, sophistication * 0.1) * 0.4)
        return min(1.0, creativity_score)

    def measure_consistency(self, model_name: str, test_case: Dict, runs: int = 3) -> Tuple[List[str], float]:
        """Mede consistência de respostas múltiplas."""
        spec = self.models[model_name]
        responses = []

        try:
            llm = get_llm(provider_name=spec.provider)

            messages = [
                SystemMessage(content="Responda de forma clara e consistente."),
                HumanMessage(content=test_case["input"])
            ]

            for _ in range(runs):
                response = llm.invoke(messages)
                responses.append(response.content)

            # Calcular similaridade entre respostas
            similarities = []
            for i in range(len(responses)):
                for j in range(i + 1, len(responses)):
                    # Similaridade simples baseada em palavras comuns
                    words1 = set(responses[i].lower().split())
                    words2 = set(responses[j].lower().split())
                    if len(words1) > 0 and len(words2) > 0:
                        similarity = len(words1 & words2) / len(words1 | words2)
                        similarities.append(similarity)

            consistency = statistics.mean(similarities) if similarities else 0.0
            return responses, consistency

        except Exception as e:
            print(f"Erro ao medir consistência para {model_name}: {str(e)}")
            return [], 0.0

    def run_comprehensive_benchmark(self, logger) -> List[BenchmarkResult]:
        """Executa benchmark abrangente de todos os modelos."""
        results = []

        print(f"\n🚀 Iniciando benchmark de {len(self.models)} modelos")
        print(f"   Executando {len(self.benchmarks)} categorias de teste")

        for benchmark in self.benchmarks:
            category = benchmark["category"]
            test_cases = benchmark["test_cases"]
            criteria = benchmark["criteria"]

            print(f"\n📊 Categoria: {category}")

            for model_name, spec in self.models.items():
                print(f"  🤖 Testando {model_name}...")

                category_results = []

                try:
                    llm = get_llm(provider_name=spec.provider)

                    for test_case in test_cases:
                        start_time = time.time()

                        # Executar teste
                        messages = [
                            SystemMessage(content=test_case.get("system_prompt", "Responda de forma clara e precisa.")),
                            HumanMessage(content=test_case["input"])
                        ]

                        response = llm.invoke(messages)
                        execution_time = time.time() - start_time

                        # Avaliar resposta baseado nos critérios
                        scores = {}

                        if "reasoning_steps" in criteria:
                            scores["reasoning"] = self.evaluate_reasoning_capability(
                                response.content, criteria["reasoning_steps"]
                            )

                        if "factual_accuracy" in criteria:
                            scores["accuracy"] = self.evaluate_factual_accuracy(
                                response.content, criteria["factual_accuracy"]
                            )

                        if "creativity" in criteria and criteria["creativity"]:
                            scores["creativity"] = self.evaluate_creativity(response.content)

                        # Medir consistência
                        _, consistency = self.measure_consistency(model_name, test_case, runs=2)

                        # Calcular score geral
                        overall_score = statistics.mean(scores.values()) if scores else 0.5

                        # Estimar custo
                        tokens_used = len(response.content) // 4  # Aproximação
                        cost = (tokens_used / 1000) * spec.cost_per_1k_tokens

                        # Criar resultado
                        result = BenchmarkResult(
                            model_name=model_name,
                            category=category,
                            test_name=test_case["name"],
                            score=overall_score,
                            execution_time=execution_time,
                            tokens_used=tokens_used,
                            cost=cost,
                            error_rate=0.0,  # Simplificado para demo
                            consistency=consistency
                        )

                        category_results.append(result)
                        results.append(result)

                    # Resumo da categoria para o modelo
                    avg_score = statistics.mean([r.score for r in category_results])
                    avg_time = statistics.mean([r.execution_time for r in category_results])
                    total_cost = sum([r.cost for r in category_results])

                    print(f"    Score: {avg_score:.3f}, Tempo: {avg_time:.2f}s, Custo: ${total_cost:.4f}")

                except Exception as e:
                    print(f"    ❌ Erro: {str(e)}")
                    logger.error(f"Erro no benchmark {category} para {model_name}: {str(e)}")

        return results

def criar_modelos_comparacao() -> List[ModelSpec]:
    """Cria especificações de modelos para comparação."""
    return [
        ModelSpec(
            name="Llama-3.3-Latest",
            provider="ollama",
            model_id="llama3:latest",
            context_window=8192,
            max_tokens=200,
            cost_per_1k_tokens=0.0001,  # Custo local muito baixo
            latency_expected=2.0,
            strengths=["Eficiência", "Privacidade", "Custo baixo"],
            limitations=["Capacidade limitada", "Conhecimento até cutoff"],
            use_cases=["Tarefas simples", "Alto volume", "Dados sensíveis"]
        ),
        ModelSpec(
            name="GptOss",
            provider="ollama",
            model_id="gpt-oss:latest",
            context_window=16384,
            max_tokens=200,
            cost_per_1k_tokens=0.00015,  # Custo local muito baixo
            latency_expected=1.5,
            strengths=["Velocidade", "Custo-benefício", "API estável"],
            limitations=["Conhecimento até 2022", "Capacidades limitadas"],
            use_cases=["Uso geral", "Chatbots", "Automação simples"]
        ),
         ModelSpec(
            name="mistral",
            provider="ollama",
            model_id="mistral:latest",
            context_window=8192,
            max_tokens=200,
            cost_per_1k_tokens=0.00008, 
            latency_expected=1.5,
            strengths=["Velocidade", "Custo-benefício", "API estável"],
            limitations=["Conhecimento até 2022", "Capacidades limitadas"],
            use_cases=["Uso geral", "Chatbots", "Automação simples"]
        ),
        # ModelSpec(
        #     name="GPT-3.5-Turbo",
        #     provider="openai",
        #     model_id="gpt-3.5-turbo",
        #     context_window=16384,
        #     max_tokens=200,
        #     cost_per_1k_tokens=0.0015,
        #     latency_expected=1.5,
        #     strengths=["Velocidade", "Custo-benefício", "API estável"],
        #     limitations=["Conhecimento até 2022", "Capacidades limitadas"],
        #     use_cases=["Uso geral", "Chatbots", "Automação simples"]
        # ),
        # ModelSpec(
        #     name="GPT-4",
        #     provider="openai",
        #     model_id="gpt-4",
        #     context_window=8192,
        #     max_tokens=200,
        #     cost_per_1k_tokens=0.03,
        #     latency_expected=3.0,
        #     strengths=["Qualidade superior", "Raciocínio complexo", "Criatividade"],
        #     limitations=["Custo alto", "Latência maior"],
        #     use_cases=["Análises complexas", "Criação de conteúdo", "Consultoria"]
        # )
    ]

def criar_benchmarks_abrangentes() -> List[Dict]:
    """Cria benchmarks para diferentes capacidades."""
    return [
        {
            "name": "Raciocínio Lógico",
            "category": "reasoning",
            "test_cases": [
                {
                    "name": "analise_financeira",
                    "input": "Uma empresa teve receita de R$ 1M no Q1, R$ 1.2M no Q2 e R$ 1.5M no Q3. Analise a tendência e projete Q4.",
                    "system_prompt": "Analise os dados numericamente e explique seu raciocínio passo a passo."
                },
                {
                    "name": "problema_logico",
                    "input": "Se todo A é B, e todo B é C, e João é A, o que podemos concluir sobre João?",
                    "system_prompt": "Use lógica formal para resolver este problema."
                }
            ],
            "criteria": {
                "reasoning_steps": ["crescimento", "tendência", "percentual", "projeção"],
                "factual_accuracy": ["25%", "crescimento", "trimestre"]
            }
        },
        {
            "name": "Conhecimento Factual",
            "category": "knowledge",
            "test_cases": [
                {
                    "name": "geografia_brasil",
                    "input": "Quais são as 5 maiores cidades do Brasil por população?",
                    "system_prompt": "Forneça informações factuais precisas."
                },
                {
                    "name": "tecnologia_atual",
                    "input": "Explique o que é inteligência artificial e suas principais aplicações empresariais.",
                    "system_prompt": "Seja preciso e atual nas informações."
                }
            ],
            "criteria": {
                "factual_accuracy": ["São Paulo", "Rio de Janeiro", "Brasília", "Salvador", "Fortaleza"]
            }
        },
        {
            "name": "Criatividade",
            "category": "creativity",
            "test_cases": [
                {
                    "name": "estrategia_marketing",
                    "input": "Crie uma estratégia criativa de marketing para lançar um novo aplicativo de produtividade.",
                    "system_prompt": "Seja criativo e inovador, mas mantenha viabilidade prática."
                },
                {
                    "name": "solucao_problema",
                    "input": "Como uma empresa pode reduzir custos operacionais sem demitir funcionários?",
                    "system_prompt": "Pense fora da caixa, mas seja prático."
                }
            ],
            "criteria": {
                "creativity": True
            }
        },
        {
            "name": "Eficiência Empresarial",
            "category": "business",
            "test_cases": [
                {
                    "name": "analise_swot",
                    "input": "Faça uma análise SWOT para uma startup de tecnologia que acabou de receber investimento.",
                    "system_prompt": "Use framework SWOT estruturado e seja conciso."
                },
                {
                    "name": "kpis_vendas",
                    "input": "Quais KPIs uma equipe de vendas B2B deveria acompanhar mensalmente?",
                    "system_prompt": "Foque em métricas práticas e acionáveis."
                }
            ],
            "criteria": {
                "reasoning_steps": ["forças", "fraquezas", "oportunidades", "ameaças"],
                "factual_accuracy": ["SWOT", "startup", "investimento"]
            }
        }
    ]

def gerar_relatorio_comparativo_completo(results: List[BenchmarkResult], models: Dict[str, ModelSpec]):
    """Gera relatório executivo completo de comparação."""
    print("\n" + "="*80)
    print("📊 RELATÓRIO EXECUTIVO DE COMPARAÇÃO DE MODELOS")
    print("="*80)

    # Análise geral por modelo
    print("\n🏆 RANKING GERAL DOS MODELOS")
    print("-"*50)

    model_summary = {}
    for model_name in models.keys():
        model_results = [r for r in results if r.model_name == model_name]
        if model_results:
            avg_score = statistics.mean([r.score for r in model_results])
            avg_time = statistics.mean([r.execution_time for r in model_results])
            total_cost = sum([r.cost for r in model_results])
            avg_consistency = statistics.mean([r.consistency for r in model_results])

            model_summary[model_name] = {
                "score": avg_score,
                "time": avg_time,
                "cost": total_cost,
                "consistency": avg_consistency
            }

    # Ranking por score geral
    ranked_models = sorted(model_summary.items(), key=lambda x: x[1]["score"], reverse=True)

    for i, (model_name, summary) in enumerate(ranked_models, 1):
        print(f"\n{i}. 🤖 {model_name}")
        print(f"   Score Geral: {summary['score']:.3f}")
        print(f"   Tempo Médio: {summary['time']:.2f}s")
        print(f"   Custo Total: ${summary['cost']:.4f}")
        print(f"   Consistência: {summary['consistency']:.3f}")

        # Mostrar características do modelo
        spec = models[model_name]
        print(f"   Pontos Fortes: {', '.join(spec.strengths)}")
        print(f"   Casos de Uso: {', '.join(spec.use_cases[:2])}")

    # Análise por categoria
    print("\n📊 PERFORMANCE POR CATEGORIA")
    print("-"*50)

    categories = {}
    for result in results:
        if result.category not in categories:
            categories[result.category] = {}
        if result.model_name not in categories[result.category]:
            categories[result.category][result.model_name] = []
        categories[result.category][result.model_name].append(result.score)

    for category, cat_models in categories.items():
        print(f"\n📁 {category.upper()}:")
        cat_ranking = []
        for model_name, scores in cat_models.items():
            avg_score = statistics.mean(scores)
            cat_ranking.append((model_name, avg_score))

        cat_ranking.sort(key=lambda x: x[1], reverse=True)

        for i, (model_name, score) in enumerate(cat_ranking, 1):
            medal = "🥇" if i == 1 else "🥈" if i == 2 else "🥉" if i == 3 else "  "
            print(f"   {medal} {model_name}: {score:.3f}")

    # Análise de custo-benefício
    print("\n💰 ANÁLISE DE CUSTO-BENEFÍCIO")
    print("-"*50)

    for model_name, summary in model_summary.items():
        efficiency = summary["score"] / (summary["cost"] + 0.001)  # Evitar divisão por zero
        print(f"{model_name}: Score/Custo = {efficiency:.1f}")

    # Recomendações estratégicas
    print("\n🎯 RECOMENDAÇÕES ESTRATÉGICAS")
    print("-"*50)

    best_overall = ranked_models[0][0]
    best_value = max(model_summary.items(), key=lambda x: x[1]["score"] / (x[1]["cost"] + 0.001))[0]
    fastest = min(model_summary.items(), key=lambda x: x[1]["time"])[0]
    most_consistent = max(model_summary.items(), key=lambda x: x[1]["consistency"])[0]

    print(f"\n🏆 MELHOR GERAL: {best_overall}")
    print(f"   Use para: Casos críticos, análises complexas")

    print(f"\n💎 MELHOR CUSTO-BENEFÍCIO: {best_value}")
    print(f"   Use para: Volume alto, uso geral")

    print(f"\n⚡ MAIS RÁPIDO: {fastest}")
    print(f"   Use para: Aplicações time-sensitive")

    print(f"\n🎯 MAIS CONSISTENTE: {most_consistent}")
    print(f"   Use para: Processos críticos, compliance")

    # Matrix de decisão
    print(f"\n📋 MATRIX DE DECISÃO POR CASO DE USO")
    print("-"*50)

    use_cases = {
        "Customer Support (Alto Volume)": best_value,
        "Análises Estratégicas": best_overall,
        "Automação Simples": fastest,
        "Processos Críticos": most_consistent
    }

    for use_case, recommended_model in use_cases.items():
        print(f"✅ {use_case}: {recommended_model}")

def demo_comparacao_modelos():
    """
    Demonstra comparação abrangente de modelos de IA.
    """
    logger = get_logger("comparacao_modelos")

    try:
        print("🔬 SISTEMA DE COMPARAÇÃO DE MODELOS DE IA")
        print("="*45)

        # Configurar benchmark
        benchmark = ModelBenchmark()

        # Registrar modelos
        print("\n🤖 Registrando modelos para comparação...")
        model_specs = criar_modelos_comparacao()

        for spec in model_specs:
            benchmark.register_model(spec)
            print(f"  ✅ {spec.name} ({spec.provider})")

        # Configurar benchmarks
        print("\n📊 Configurando benchmarks...")
        benchmarks_config = criar_benchmarks_abrangentes()

        for bench_config in benchmarks_config:
            benchmark.add_benchmark(
                bench_config["name"],
                bench_config["category"],
                bench_config["test_cases"],
                bench_config["criteria"]
            )
            print(f"  ✅ {bench_config['name']} ({len(bench_config['test_cases'])} testes)")

        # Executar benchmark completo
        print(f"\n🚀 Executando benchmark completo...")
        print("   (Isso pode levar alguns minutos...)")

        start_time = time.time()
        results = benchmark.run_comprehensive_benchmark(logger)
        total_time = time.time() - start_time

        print(f"\n⏱️ Benchmark concluído em {total_time:.1f}s")
        print(f"📊 {len(results)} avaliações executadas")

        # Gerar relatório
        gerar_relatorio_comparativo_completo(results, benchmark.models)

        print(f"\n✅ Comparação de modelos concluída!")
        print(f"\n💡 Use estas métricas para escolher o modelo ideal")
        print("   para cada caso de uso específico da sua empresa.")

        logger.info(f"Comparação de modelos concluída - {len(results)} avaliações")
        return True

    except Exception as e:
        error_msg = f"Erro durante comparação de modelos: {str(e)}"
        logger.error(error_msg)
        print(f"❌ {error_msg}")
        return False

def explicar_metodologia():
    """
    Explica a metodologia de comparação.
    """
    print("""
🔬 METODOLOGIA DE COMPARAÇÃO
============================

DIMENSÕES AVALIADAS:
1. 🧠 Capacidade de Raciocínio
   - Lógica sequencial
   - Análise quantitativa
   - Conclusões fundamentadas

2. 📚 Conhecimento Factual
   - Precisão de informações
   - Cobertura de domínios
   - Atualidade dos dados

3. 🎨 Criatividade
   - Originalidade de ideias
   - Diversidade vocabular
   - Soluções inovadoras

4. ⚡ Performance Operacional
   - Velocidade de resposta
   - Consistência
   - Eficiência de tokens

5. 💰 Custo-Benefício
   - Custo por interação
   - Valor gerado
   - ROI efetivo

MÉTRICAS CALCULADAS:
- Score Absoluto (0-1)
- Ranking Relativo
- Consistência (variação)
- Eficiência (score/custo)
- Especialização por categoria
""")

def mostrar_criterios_selecao():
    """
    Mostra critérios para seleção de modelos.
    """
    print("""
🎯 CRITÉRIOS DE SELEÇÃO POR CONTEXTO
====================================

ALTO VOLUME / BAIXO CUSTO:
✅ Priorizar: Custo por token
✅ Aceitar: Qualidade moderada
✅ Exemplo: Customer support L1

ALTA QUALIDADE / CUSTO SECUNDÁRIO:
✅ Priorizar: Score de qualidade
✅ Aceitar: Custo mais alto
✅ Exemplo: Análises estratégicas

BAIXA LATÊNCIA / TEMPO REAL:
✅ Priorizar: Velocidade de resposta
✅ Aceitar: Menor qualidade
✅ Exemplo: Chatbots interativos

MÁXIMA CONSISTÊNCIA:
✅ Priorizar: Baixa variação
✅ Aceitar: Performance moderada
✅ Exemplo: Processos regulatórios

MODELO HÍBRIDO:
✅ Usar diferentes modelos por contexto
✅ Routing inteligente baseado em input
✅ Otimização contínua automática
""")

def configurar_ambiente():
    """
    Configuração para comparação de modelos.
    """
    print("""
📋 CONFIGURAÇÃO - COMPARAÇÃO DE MODELOS
=======================================

Dependências:
pip install matplotlib  # Para gráficos
pip install pandas      # Para análise
pip install numpy       # Para cálculos

Provedores necessários:
- Pelo menos 2 modelos diferentes
- Credenciais configuradas
- Limites de API adequados

IMPORTANTE:
- Testes consomem tokens/créditos
- Execute em horários de baixo uso
- Salve resultados para análise posterior
- Consider usar modelos locais para economia
""")

if __name__ == "__main__":
    configurar_ambiente()
    explicar_metodologia()
    mostrar_criterios_selecao()

    resposta = input("\nDeseja executar a comparação de modelos? (s/n): ")
    if resposta.lower() in ['s', 'sim', 'y', 'yes']:
        demo_comparacao_modelos()
    else:
        print("Demo cancelado.")