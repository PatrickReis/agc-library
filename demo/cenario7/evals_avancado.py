"""
Cenário 7: Evals Avançado - Comparação de Modelos e A/B Testing
Demonstra sistema sofisticado de avaliação e otimização de IA.
"""

from agentCore import get_llm, get_logger
from agentCore.evaluation.model_comparison import ModelComparator
from agentCore.evaluation.metrics_collector import MetricsCollector
from langchain_core.messages import HumanMessage, SystemMessage
import json
import os
import time
import statistics
import random
from datetime import datetime, timedelta
from typing import List, Dict, Any, Tuple
from dataclasses import dataclass
from dotenv import load_dotenv

load_dotenv()

@dataclass
class ModelConfig:
    """Configuração de modelo para comparação."""
    name: str
    provider: str
    model: str
    temperature: float
    max_tokens: int
    description: str

@dataclass
class EvalResult:
    """Resultado de uma avaliação."""
    model_name: str
    test_case_id: str
    input_text: str
    output_text: str
    scores: Dict[str, float]
    overall_score: float
    execution_time: float
    token_usage: int
    cost_estimate: float

class AdvancedEvaluator:
    """Sistema avançado de avaliação com múltiplas métricas."""

    def __init__(self):
        self.models = []
        self.test_cases = []
        self.results = []

    def add_model(self, config: ModelConfig):
        """Adiciona modelo para comparação."""
        self.models.append(config)

    def add_test_case(self, id: str, input_text: str, category: str, expected_criteria: Dict):
        """Adiciona caso de teste."""
        test_case = {
            "id": id,
            "input": input_text,
            "category": category,
            "criteria": expected_criteria
        }
        self.test_cases.append(test_case)

    def evaluate_semantic_similarity(self, response: str, expected_keywords: List[str]) -> float:
        """Avalia similaridade semântica usando keywords."""
        response_lower = response.lower()
        matches = 0
        for keyword in expected_keywords:
            if keyword.lower() in response_lower:
                matches += 1
        return (matches / len(expected_keywords)) if expected_keywords else 0.0

    def evaluate_response_structure(self, response: str) -> float:
        """Avalia estrutura e organização da resposta."""
        score = 0.0

        # Verifica se tem estrutura organizada
        if any(char in response for char in [":", "-", "•", "1.", "2."]):
            score += 0.3

        # Verifica se tem conclusão clara
        conclusion_words = ["portanto", "assim", "em resumo", "conclusão"]
        if any(word in response.lower() for word in conclusion_words):
            score += 0.2

        # Verifica tamanho adequado
        if 50 <= len(response) <= 500:
            score += 0.3
        elif len(response) > 500:
            score += 0.1

        # Verifica se evita repetição
        words = response.lower().split()
        unique_words = set(words)
        if len(unique_words) / len(words) > 0.7:  # 70% palavras únicas
            score += 0.2

        return min(1.0, score)

    def evaluate_hallucination_detection(self, response: str, category: str) -> float:
        """Detecta possíveis alucinações baseado na categoria."""
        # Palavras que indicam incerteza (bom para evitar alucinações)
        uncertainty_indicators = ["possivelmente", "talvez", "pode ser", "não tenho certeza", "acredito que"]

        # Palavras que indicam alta confiança (risco de alucinação se incorreto)
        high_confidence = ["certamente", "definitivamente", "sem dúvida", "100%", "sempre"]

        response_lower = response.lower()

        # Se categoria é "fora_escopo", deve mostrar incerteza
        if category == "fora_escopo":
            if any(ind in response_lower for ind in uncertainty_indicators):
                return 1.0
            elif any(conf in response_lower for conf in high_confidence):
                return 0.1
            else:
                return 0.5

        # Para outras categorias, balance é importante
        uncertainty_count = sum(1 for ind in uncertainty_indicators if ind in response_lower)
        confidence_count = sum(1 for conf in high_confidence if conf in response_lower)

        if uncertainty_count > 0 and confidence_count == 0:
            return 0.8  # Bom: mostra humildade
        elif uncertainty_count == 0 and confidence_count > 2:
            return 0.3  # Ruim: muito confiante, risco alucinação
        else:
            return 0.6  # Neutro

    def calculate_comprehensive_score(self, response: str, test_case: Dict) -> Dict[str, float]:
        """Calcula score abrangente com múltiplas métricas."""
        scores = {}

        # Métrica 1: Relevância (similarity com keywords esperadas)
        expected_keywords = test_case["criteria"].get("keywords", [])
        scores["relevancia"] = self.evaluate_semantic_similarity(response, expected_keywords)

        # Métrica 2: Estrutura e organização
        scores["estrutura"] = self.evaluate_response_structure(response)

        # Métrica 3: Detecção de alucinação
        scores["anti_alucinacao"] = self.evaluate_hallucination_detection(response, test_case["category"])

        # Métrica 4: Completude baseada em critérios obrigatórios
        required_elements = test_case["criteria"].get("required_elements", [])
        if required_elements:
            response_lower = response.lower()
            found_elements = sum(1 for elem in required_elements if elem.lower() in response_lower)
            scores["completude"] = found_elements / len(required_elements)
        else:
            scores["completude"] = 0.7  # Neutro se não há elementos obrigatórios

        # Métrica 5: Tom e profissionalismo
        professional_tone = self.evaluate_professional_tone(response)
        scores["profissionalismo"] = professional_tone

        return scores

    def evaluate_professional_tone(self, response: str) -> float:
        """Avalia tom profissional da resposta."""
        response_lower = response.lower()

        # Palavras que prejudicam profissionalismo
        unprofessional = ["cara", "mano", "tipo assim", "né", "tá ligado", "beleza"]
        unprofessional_count = sum(1 for word in unprofessional if word in response_lower)

        # Palavras que indicam profissionalismo
        professional = ["prezado", "senhor", "senhora", "cordialmente", "atenciosamente"]
        professional_count = sum(1 for word in professional if word in response_lower)

        if unprofessional_count > 0:
            return max(0.1, 0.8 - (unprofessional_count * 0.2))
        elif professional_count > 0:
            return min(1.0, 0.8 + (professional_count * 0.1))
        else:
            return 0.7  # Neutro

    def run_comprehensive_evaluation(self, logger) -> List[EvalResult]:
        """Executa avaliação abrangente de todos os modelos."""
        all_results = []

        print(f"\n🔄 Iniciando avaliação de {len(self.models)} modelos com {len(self.test_cases)} casos")

        for model_config in self.models:
            print(f"\n📊 Avaliando modelo: {model_config.name}")

            try:
                # Configurar modelo
                llm = get_llm(
                    provider=model_config.provider,
                    model=model_config.model,
                    temperature=model_config.temperature,
                    max_tokens=model_config.max_tokens
                )

                model_results = []

                for test_case in self.test_cases:
                    start_time = time.time()

                    # Gerar resposta
                    messages = [
                        SystemMessage(content="""Você é um assistente empresarial especializado.
                        Responda de forma clara, precisa e profissional.
                        Se não souber algo, admita claramente."""),
                        HumanMessage(content=test_case["input"])
                    ]

                    response = llm.invoke(messages)
                    execution_time = time.time() - start_time

                    # Calcular scores
                    scores = self.calculate_comprehensive_score(response.content, test_case)

                    # Score geral ponderado
                    weights = {
                        "relevancia": 0.25,
                        "estrutura": 0.20,
                        "anti_alucinacao": 0.20,
                        "completude": 0.25,
                        "profissionalismo": 0.10
                    }

                    overall_score = sum(scores[metric] * weights[metric] for metric in weights)

                    # Estimar custo (simulado)
                    estimated_tokens = len(response.content) // 4  # Aproximação
                    cost_estimate = estimated_tokens * 0.0001  # $0.0001 por token (exemplo)

                    # Criar resultado
                    result = EvalResult(
                        model_name=model_config.name,
                        test_case_id=test_case["id"],
                        input_text=test_case["input"],
                        output_text=response.content,
                        scores=scores,
                        overall_score=overall_score,
                        execution_time=execution_time,
                        token_usage=estimated_tokens,
                        cost_estimate=cost_estimate
                    )

                    model_results.append(result)
                    all_results.append(result)

                # Resumo do modelo
                avg_score = statistics.mean([r.overall_score for r in model_results])
                avg_time = statistics.mean([r.execution_time for r in model_results])
                total_cost = sum([r.cost_estimate for r in model_results])

                print(f"  ✅ Score médio: {avg_score:.3f}")
                print(f"  ⏱️ Tempo médio: {avg_time:.2f}s")
                print(f"  💰 Custo estimado: ${total_cost:.4f}")

            except Exception as e:
                print(f"  ❌ Erro ao avaliar {model_config.name}: {str(e)}")
                logger.error(f"Erro na avaliação do modelo {model_config.name}: {str(e)}")

        return all_results

def criar_configuracoes_modelos() -> List[ModelConfig]:
    """Cria diferentes configurações de modelos para comparação."""
    return [
        ModelConfig(
            name="Ollama_Conservative",
            provider="ollama",
            model="llama3:latest",
            temperature=0.1,
            max_tokens=150,
            description="Configuração conservadora para máxima consistência"
        ),
        ModelConfig(
            name="Ollama_Balanced",
            provider="ollama",
            model="llama3:latest",
            temperature=0.3,
            max_tokens=200,
            description="Configuração balanceada para uso geral"
        ),
        ModelConfig(
            name="Ollama_Creative",
            provider="ollama",
            model="llama3:latest",
            temperature=0.7,
            max_tokens=250,
            description="Configuração mais criativa para respostas elaboradas"
        )
    ]

def criar_dataset_avancado():
    """Cria dataset avançado para avaliação abrangente."""
    test_cases = [
        {
            "id": "rh_001",
            "input": "Quais são os benefícios oferecidos pela empresa?",
            "category": "recursos_humanos",
            "criteria": {
                "keywords": ["vale refeição", "plano de saúde", "vale alimentação"],
                "required_elements": ["vale", "plano", "benefícios"],
                "max_length": 300
            }
        },
        {
            "id": "rh_002",
            "input": "Como funciona a política de férias?",
            "category": "recursos_humanos",
            "criteria": {
                "keywords": ["30 dias", "férias", "período aquisitivo"],
                "required_elements": ["dias", "férias"],
                "should_avoid": ["não sei", "não tenho informação"]
            }
        },
        {
            "id": "com_001",
            "input": "Qual é o processo de vendas da empresa?",
            "category": "comercial",
            "criteria": {
                "keywords": ["qualificação", "proposta", "apresentação", "etapas"],
                "required_elements": ["processo", "etapas"],
                "should_include_structure": True
            }
        },
        {
            "id": "tec_001",
            "input": "Quais são os níveis de SLA do suporte técnico?",
            "category": "suporte_tecnico",
            "criteria": {
                "keywords": ["P1", "P2", "P3", "P4", "tempo", "resposta"],
                "required_elements": ["P1", "resposta", "resolução"],
                "precision_required": True
            }
        },
        {
            "id": "edge_001",
            "input": "Qual é a temperatura em Marte hoje?",
            "category": "fora_escopo",
            "criteria": {
                "keywords": ["não sei", "não tenho", "fora do escopo", "especializado"],
                "required_elements": ["não"],
                "should_show_limitation": True
            }
        },
        {
            "id": "edge_002",
            "input": "Me conte uma piada sobre programação",
            "category": "fora_escopo",
            "criteria": {
                "keywords": ["não posso", "especializado em", "empresa"],
                "should_redirect": True
            }
        }
    ]

    return test_cases

def gerar_relatorio_comparativo(results: List[EvalResult], logger):
    """Gera relatório comparativo abrangente."""
    print("\n" + "="*80)
    print("📊 RELATÓRIO COMPARATIVO AVANÇADO")
    print("="*80)

    # Agrupar por modelo
    models = {}
    for result in results:
        if result.model_name not in models:
            models[result.model_name] = []
        models[result.model_name].append(result)

    # Análise geral por modelo
    print("\n📈 PERFORMANCE GERAL POR MODELO:")
    print("-"*50)

    for model_name, model_results in models.items():
        if not model_results:
            continue

        scores = [r.overall_score for r in model_results]
        times = [r.execution_time for r in model_results]
        costs = [r.cost_estimate for r in model_results]

        avg_score = statistics.mean(scores)
        std_score = statistics.stdev(scores) if len(scores) > 1 else 0
        avg_time = statistics.mean(times)
        total_cost = sum(costs)

        print(f"\n🤖 {model_name}:")
        print(f"  Score Médio: {avg_score:.3f} ± {std_score:.3f}")
        print(f"  Tempo Médio: {avg_time:.2f}s")
        print(f"  Custo Total: ${total_cost:.4f}")
        print(f"  Consistência: {'Alta' if std_score < 0.1 else 'Média' if std_score < 0.2 else 'Baixa'}")

    # Análise por categoria
    print("\n📊 PERFORMANCE POR CATEGORIA:")
    print("-"*50)

    categories = {}
    for result in results:
        # Encontrar categoria do test case
        test_case = next((tc for tc in criar_dataset_avancado() if tc["id"] == result.test_case_id), None)
        if test_case:
            cat = test_case["category"]
            if cat not in categories:
                categories[cat] = {}
            if result.model_name not in categories[cat]:
                categories[cat][result.model_name] = []
            categories[cat][result.model_name].append(result.overall_score)

    for category, cat_models in categories.items():
        print(f"\n📁 {category.upper()}:")
        for model_name, scores in cat_models.items():
            avg_score = statistics.mean(scores)
            print(f"  {model_name}: {avg_score:.3f}")

    # Análise por métrica
    print("\n🎯 ANÁLISE DETALHADA POR MÉTRICA:")
    print("-"*50)

    metrics = ["relevancia", "estrutura", "anti_alucinacao", "completude", "profissionalismo"]

    for metric in metrics:
        print(f"\n📊 {metric.upper()}:")
        metric_scores = {}

        for result in results:
            if result.model_name not in metric_scores:
                metric_scores[result.model_name] = []
            if metric in result.scores:
                metric_scores[result.model_name].append(result.scores[metric])

        for model_name, scores in metric_scores.items():
            if scores:
                avg_score = statistics.mean(scores)
                print(f"  {model_name}: {avg_score:.3f}")

    # Recomendação final
    print("\n🎯 RECOMENDAÇÃO ESTRATÉGICA:")
    print("-"*50)

    # Encontrar melhor modelo geral
    model_performance = {}
    for model_name, model_results in models.items():
        if model_results:
            scores = [r.overall_score for r in model_results]
            times = [r.execution_time for r in model_results]
            costs = [r.cost_estimate for r in model_results]

            avg_score = statistics.mean(scores)
            avg_time = statistics.mean(times)
            total_cost = sum(costs)

            # Score composto (considera qualidade, velocidade e custo)
            composite_score = (avg_score * 0.6) + ((1/avg_time) * 0.2) + ((1/(total_cost+0.001)) * 0.2)
            model_performance[model_name] = {
                "quality": avg_score,
                "speed": avg_time,
                "cost": total_cost,
                "composite": composite_score
            }

    best_overall = max(model_performance.items(), key=lambda x: x[1]["composite"])
    best_quality = max(model_performance.items(), key=lambda x: x[1]["quality"])
    fastest = min(model_performance.items(), key=lambda x: x[1]["speed"])
    cheapest = min(model_performance.items(), key=lambda x: x[1]["cost"])

    print(f"🏆 MELHOR GERAL: {best_overall[0]}")
    print(f"   (Score composto: {best_overall[1]['composite']:.3f})")

    print(f"\n🎖️ MELHOR QUALIDADE: {best_quality[0]}")
    print(f"   (Score: {best_quality[1]['quality']:.3f})")

    print(f"\n⚡ MAIS RÁPIDO: {fastest[0]}")
    print(f"   (Tempo: {fastest[1]['speed']:.2f}s)")

    print(f"\n💰 MAIS ECONÔMICO: {cheapest[0]}")
    print(f"   (Custo: ${cheapest[1]['cost']:.4f})")

    print(f"\n💡 RECOMENDAÇÃO DE USO:")
    if best_overall[1]["quality"] > 0.8:
        print("✅ Sistema pronto para produção")
        print(f"   Usar {best_overall[0]} para uso geral")
        print(f"   Usar {best_quality[0]} para casos críticos")
    elif best_overall[1]["quality"] > 0.6:
        print("⚠️ Sistema precisa de ajustes antes da produção")
        print("   Focar em melhorar prompts e datasets")
    else:
        print("❌ Sistema não está pronto para produção")
        print("   Revisão completa de prompts e modelos necessária")

def demo_evals_avancado():
    """
    Demonstra sistema avançado de avaliação e comparação.
    """
    logger = get_logger("evals_avancado")

    try:
        print("🧪 SISTEMA DE AVALIAÇÃO AVANÇADO")
        print("="*40)

        # Criar avaliador
        evaluator = AdvancedEvaluator()

        # Configurar modelos para comparação
        print("\n🤖 Configurando modelos para comparação...")
        model_configs = criar_configuracoes_modelos()

        for config in model_configs:
            evaluator.add_model(config)
            print(f"  ✅ {config.name} ({config.description})")

        # Carregar dataset avançado
        print("\n📊 Carregando dataset avançado...")
        test_cases = criar_dataset_avancado()

        for test_case in test_cases:
            evaluator.add_test_case(
                test_case["id"],
                test_case["input"],
                test_case["category"],
                test_case["criteria"]
            )

        print(f"  ✅ {len(test_cases)} casos de teste carregados")

        # Executar avaliação abrangente
        print(f"\n🚀 Executando avaliação comparativa...")
        start_time = time.time()

        results = evaluator.run_comprehensive_evaluation(logger)

        total_time = time.time() - start_time

        print(f"\n⏱️ Avaliação concluída em {total_time:.2f}s")
        print(f"📊 {len(results)} avaliações executadas")

        # Gerar relatório comparativo
        gerar_relatorio_comparativo(results, logger)

        print(f"\n✅ Evals Avançado concluído!")
        print(f"\n💡 PRÓXIMO PASSO: Use essas métricas para escolher")
        print("   a configuração ideal para seu caso de uso específico.")

        logger.info(f"Evals avançado concluído - {len(results)} avaliações executadas")
        return True

    except Exception as e:
        error_msg = f"Erro durante execução dos Evals Avançados: {str(e)}"
        logger.error(error_msg)
        print(f"❌ {error_msg}")
        return False

def explicar_diferencas_evals():
    """
    Explica diferenças entre Evals básico e avançado.
    """
    print("""
🔍 COMPARAÇÃO: EVALS BÁSICO vs AVANÇADO
=======================================

EVALS BÁSICO (Cenário 6):
✅ Validação simples de qualidade
✅ Métricas básicas (relevância, precisão)
✅ Dataset pequeno e focado
✅ Relatórios simples

EVALS AVANÇADO (Cenário 7):
🚀 Comparação múltiplos modelos/configurações
🚀 Métricas sofisticadas (anti-alucinação, estrutura)
🚀 A/B testing automatizado
🚀 Análise estatística robusta
🚀 Recomendações estratégicas
🚀 Consideração de custo-benefício

QUANDO USAR CADA UM:
- Básico: Validação inicial, sistemas simples
- Avançado: Otimização, sistemas críticos, produção
""")

def mostrar_metricas_avancadas():
    """
    Explica métricas avançadas utilizadas.
    """
    print("""
🎯 MÉTRICAS AVANÇADAS EXPLICADAS
================================

1. ANTI-ALUCINAÇÃO:
   - Detecta confiança excessiva
   - Valida admissão de limitações
   - Previne informações incorretas

2. ESTRUTURA E ORGANIZAÇÃO:
   - Lista estruturada vs texto corrido
   - Conclusões claras
   - Tamanho adequado da resposta

3. ANÁLISE ESTATÍSTICA:
   - Média ± desvio padrão
   - Consistência entre execuções
   - Intervalos de confiança

4. COST-BENEFIT ANALYSIS:
   - Tokens utilizados
   - Tempo de execução
   - Custo estimado por interação

5. COMPOSITE SCORING:
   - Combina qualidade + velocidade + custo
   - Ponderação customizável
   - Ranking multi-critério
""")

def configurar_ambiente():
    """
    Configuração para Evals Avançado.
    """
    print("""
📋 CONFIGURAÇÃO - EVALS AVANÇADO
================================

Dependências adicionais:
pip install scipy  # Para análise estatística
pip install matplotlib  # Para gráficos (opcional)

Recursos necessários:
- Múltiplos modelos/provedores configurados
- Dataset abrangente e representativo
- Tempo para execução completa (~10-30min)

IMPORTANTE:
- Execute em ambiente isolado para evitar interferências
- Use seeds fixos para reproducibilidade
- Monitore recursos durante execução
- Salve resultados para análise posterior
""")

if __name__ == "__main__":
    configurar_ambiente()
    explicar_diferencas_evals()
    mostrar_metricas_avancadas()

    resposta = input("\nDeseja executar o demo de Evals Avançado? (s/n): ")
    if resposta.lower() in ['s', 'sim', 'y', 'yes']:
        demo_evals_avancado()
    else:
        print("Demo cancelado.")