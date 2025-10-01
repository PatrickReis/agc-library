"""
Cenário 6: Evals Básico - Validação e Qualidade de Prompts
Demonstra como validar e melhorar a qualidade de sistemas de IA.
"""

from agentCore import get_llm, get_logger
from agentCore.evaluation.prompt_evaluator import PromptEvaluator
from agentCore.evaluation.metrics_collector import MetricsCollector
from langchain_core.messages import HumanMessage, SystemMessage
import json
import os
import time
from datetime import datetime
from typing import List, Dict, Any
from dotenv import load_dotenv

load_dotenv()

class EvalDataset:
    """Classe para gerenciar datasets de avaliação."""

    def __init__(self):
        self.test_cases = []

    def add_test_case(self, input_text: str, expected_output: str, category: str, criteria: dict = None):
        """Adiciona um caso de teste ao dataset."""
        test_case = {
            "id": len(self.test_cases) + 1,
            "input": input_text,
            "expected": expected_output,
            "category": category,
            "criteria": criteria or {},
            "timestamp": datetime.now().isoformat()
        }
        self.test_cases.append(test_case)

    def get_by_category(self, category: str) -> List[Dict]:
        """Retorna casos de teste por categoria."""
        return [tc for tc in self.test_cases if tc["category"] == category]

def criar_dataset_atendimento():
    """
    Cria dataset para avaliar sistema de atendimento ao cliente.
    """
    dataset = EvalDataset()

    # Casos de teste para diferentes categorias
    dataset.add_test_case(
        input_text="Oi, gostaria de saber sobre os benefícios da empresa",
        expected_output="benefícios oferecidos: vale refeição, vale alimentação, plano de saúde, plano odontológico",
        category="beneficios_rh",
        criteria={"deve_mencionar": ["vale refeição", "plano de saúde"], "tom": "profissional"}
    )

    dataset.add_test_case(
        input_text="Como funciona a política de home office?",
        expected_output="máximo 3 dias por semana, presença obrigatória segundas e sextas",
        category="politicas_rh",
        criteria={"deve_mencionar": ["3 dias", "segundas e sextas"], "precisao": "alta"}
    )

    dataset.add_test_case(
        input_text="Qual é o processo de vendas da empresa?",
        expected_output="6 etapas: qualificação, descoberta, proposta, apresentação, negociação, kick-off",
        category="comercial",
        criteria={"deve_mencionar": ["6 etapas", "qualificação", "proposta"], "estrutura": "sequencial"}
    )

    dataset.add_test_case(
        input_text="Quais são os níveis de SLA do suporte?",
        expected_output="4 níveis: P1 (1h resposta), P2 (4h), P3 (1 dia), P4 (2 dias)",
        category="suporte_tecnico",
        criteria={"deve_mencionar": ["P1", "1 hora", "4 níveis"], "precisao": "alta"}
    )

    dataset.add_test_case(
        input_text="Como está o clima hoje?",
        expected_output="não tenho informações sobre clima, sou especializado em dúvidas da empresa",
        category="fora_escopo",
        criteria={"deve_reconhecer": "fora do escopo", "tom": "educado"}
    )

    return dataset

def criar_metricas_avaliacao():
    """
    Define métricas para avaliação de qualidade.
    """
    return {
        "relevancia": {
            "description": "Quão relevante é a resposta para a pergunta",
            "weight": 0.3,
            "scale": "1-5"
        },
        "precisao": {
            "description": "Precisão factual das informações",
            "weight": 0.3,
            "scale": "1-5"
        },
        "completude": {
            "description": "Completude da resposta",
            "weight": 0.2,
            "scale": "1-5"
        },
        "tom_profissional": {
            "description": "Adequação do tom profissional",
            "weight": 0.1,
            "scale": "1-5"
        },
        "clareza": {
            "description": "Clareza e objetividade",
            "weight": 0.1,
            "scale": "1-5"
        }
    }

def avaliar_resposta_automatica(resposta: str, caso_teste: Dict, metricas: Dict) -> Dict:
    """
    Avalia uma resposta automaticamente baseado em critérios.
    """
    scores = {}

    # Relevância - verifica se resposta está relacionada à pergunta
    input_lower = caso_teste["input"].lower()
    resposta_lower = resposta.lower()

    if caso_teste["category"] == "fora_escopo":
        # Para perguntas fora do escopo, deve reconhecer limitação
        if any(term in resposta_lower for term in ["não tenho", "não posso", "especializado em", "fora do"]):
            scores["relevancia"] = 5
        else:
            scores["relevancia"] = 1
    else:
        # Para perguntas no escopo, deve ter palavras-chave relacionadas
        palavras_chave = {
            "beneficios_rh": ["benefício", "vale", "plano", "auxílio"],
            "politicas_rh": ["política", "home office", "dias", "presença"],
            "comercial": ["processo", "vendas", "etapa", "cliente"],
            "suporte_tecnico": ["sla", "suporte", "resposta", "resolução"]
        }

        palavras_categoria = palavras_chave.get(caso_teste["category"], [])
        matches = sum(1 for palavra in palavras_categoria if palavra in resposta_lower)
        scores["relevancia"] = min(5, max(1, matches + 1))

    # Precisão - verifica critérios específicos
    criterios = caso_teste.get("criteria", {})
    deve_mencionar = criterios.get("deve_mencionar", [])

    if deve_mencionar:
        mentions = sum(1 for item in deve_mencionar if item.lower() in resposta_lower)
        scores["precisao"] = min(5, max(1, (mentions / len(deve_mencionar)) * 5))
    else:
        scores["precisao"] = 3  # Neutro se não há critérios específicos

    # Completude - baseado no tamanho e estrutura da resposta
    if len(resposta) < 50:
        scores["completude"] = 2
    elif len(resposta) < 150:
        scores["completude"] = 4
    else:
        scores["completude"] = 5

    # Tom profissional - verifica se evita linguagem inadequada
    linguagem_inadequada = ["cara", "mano", "tipo assim", "né"]
    if any(term in resposta_lower for term in linguagem_inadequada):
        scores["tom_profissional"] = 2
    else:
        scores["tom_profissional"] = 4

    # Clareza - verifica estrutura e organização
    if any(char in resposta for char in [":", "-", "•"]) or "." in resposta:
        scores["clareza"] = 4
    else:
        scores["clareza"] = 3

    return scores

def calcular_score_geral(scores: Dict, metricas: Dict) -> float:
    """
    Calcula score geral ponderado.
    """
    score_total = 0
    peso_total = 0

    for metrica, peso_info in metricas.items():
        if metrica in scores:
            peso = peso_info["weight"]
            score_total += scores[metrica] * peso
            peso_total += peso

    return (score_total / peso_total) if peso_total > 0 else 0

def demo_evals_basico():
    """
    Demonstra sistema básico de avaliação de prompts.
    """
    logger = get_logger("evals_basico")

    try:
        print("🧪 SISTEMA DE AVALIAÇÃO BÁSICO (EVALS)")
        print("="*50)

        # Configurar LLM
        provider = os.getenv("LLM_PROVIDER", "ollama")
        model_name = os.getenv("MODEL_NAME", "llama3:latest")
        llm = get_llm(provider_name=provider)

        # Criar dataset de teste
        print("\n📊 Criando dataset de avaliação...")
        dataset = criar_dataset_atendimento()
        metricas = criar_metricas_avaliacao()

        print(f"✅ Dataset criado com {len(dataset.test_cases)} casos de teste")
        print(f"✅ {len(metricas)} métricas definidas")

        # Sistema de prompt a ser testado
        system_prompt = """Você é um assistente especializado em responder dúvidas sobre nossa empresa.
        Responda de forma clara, objetiva e profissional.
        Use apenas informações que você tem certeza.
        Se não souber algo, diga claramente que não possui essa informação."""

        # Executar avaliações
        print("\n" + "="*60)
        print("🔄 EXECUTANDO AVALIAÇÕES")
        print("="*60)

        resultados = []
        tempo_inicio = time.time()

        for i, caso in enumerate(dataset.test_cases, 1):
            print(f"\n📝 Teste {i}/{len(dataset.test_cases)}: {caso['category']}")
            print(f"Pergunta: {caso['input']}")

            # Gerar resposta
            messages = [
                SystemMessage(content=system_prompt),
                HumanMessage(content=caso['input'])
            ]

            resposta = llm.invoke(messages)
            resposta_texto = resposta.content

            print(f"Resposta: {resposta_texto}")

            # Avaliar resposta
            scores = avaliar_resposta_automatica(resposta_texto, caso, metricas)
            score_geral = calcular_score_geral(scores, metricas)

            # Armazenar resultado
            resultado = {
                "test_id": caso["id"],
                "input": caso["input"],
                "expected": caso["expected"],
                "actual": resposta_texto,
                "category": caso["category"],
                "scores": scores,
                "score_geral": score_geral,
                "status": "PASS" if score_geral >= 3.0 else "FAIL"
            }
            resultados.append(resultado)

            # Mostrar scores
            print(f"Scores: {scores}")
            print(f"Score Geral: {score_geral:.2f}/5.0 - {resultado['status']}")

        tempo_total = time.time() - tempo_inicio

        # Gerar relatório final
        print("\n" + "="*60)
        print("📊 RELATÓRIO DE AVALIAÇÃO")
        print("="*60)

        # Estatísticas gerais
        scores_gerais = [r["score_geral"] for r in resultados]
        score_medio = sum(scores_gerais) / len(scores_gerais)
        tests_passed = len([r for r in resultados if r["status"] == "PASS"])
        pass_rate = (tests_passed / len(resultados)) * 100

        print(f"\n📈 ESTATÍSTICAS GERAIS:")
        print(f"Score Médio: {score_medio:.2f}/5.0")
        print(f"Taxa de Sucesso: {pass_rate:.1f}% ({tests_passed}/{len(resultados)})")
        print(f"Tempo Total: {tempo_total:.2f}s")
        print(f"Tempo por Teste: {tempo_total/len(resultados):.2f}s")

        # Análise por categoria
        print(f"\n📊 DESEMPENHO POR CATEGORIA:")
        categorias = {}
        for resultado in resultados:
            cat = resultado["category"]
            if cat not in categorias:
                categorias[cat] = []
            categorias[cat].append(resultado["score_geral"])

        for categoria, scores in categorias.items():
            score_cat = sum(scores) / len(scores)
            print(f"{categoria}: {score_cat:.2f}/5.0 ({len(scores)} testes)")

        # Análise por métrica
        print(f"\n🎯 DESEMPENHO POR MÉTRICA:")
        for metrica in metricas.keys():
            scores_metrica = []
            for resultado in resultados:
                if metrica in resultado["scores"]:
                    scores_metrica.append(resultado["scores"][metrica])

            if scores_metrica:
                media_metrica = sum(scores_metrica) / len(scores_metrica)
                print(f"{metrica}: {media_metrica:.2f}/5.0")

        # Casos problemáticos
        print(f"\n❌ CASOS QUE FALHARAM:")
        falhas = [r for r in resultados if r["status"] == "FAIL"]
        if falhas:
            for falha in falhas:
                print(f"- {falha['category']}: Score {falha['score_geral']:.2f}")
                print(f"  Pergunta: {falha['input']}")
                print(f"  Problema: Score abaixo de 3.0")
        else:
            print("🎉 Nenhum caso falhou!")

        # Recomendações
        print(f"\n💡 RECOMENDAÇÕES:")
        if score_medio < 3.0:
            print("❌ Sistema precisa de melhorias significativas")
            print("  - Revisar prompt system")
            print("  - Adicionar mais contexto/exemplos")
            print("  - Considerar fine-tuning do modelo")
        elif score_medio < 4.0:
            print("⚠️ Sistema funcional mas pode melhorar")
            print("  - Otimizar prompts para categorias com menor score")
            print("  - Adicionar validações específicas")
        else:
            print("✅ Sistema com boa qualidade")
            print("  - Continuar monitoramento")
            print("  - Considerar testes A/B para otimizações")

        print("\n✅ Avaliação básica concluída!")
        print(f"\n💡 PRÓXIMO PASSO: Ver Cenário 7 para Evals avançados com")
        print("   comparação de modelos e métricas mais sofisticadas.")

        logger.info(f"Evals básico concluído - Score médio: {score_medio:.2f}")
        return True

    except Exception as e:
        error_msg = f"Erro durante execução dos Evals: {str(e)}"
        logger.error(error_msg)
        print(f"❌ {error_msg}")
        return False

def explicar_conceitos_evals():
    """
    Explica conceitos fundamentais de Evals.
    """
    print("""
📚 O QUE SÃO EVALS?
===================

EVALUATIONS (Evals) são sistemas para:
✅ Medir qualidade de sistemas de IA
✅ Comparar diferentes prompts/modelos
✅ Detectar regressões de performance
✅ Validar melhorias antes do deploy

COMPONENTES PRINCIPAIS:
1. 📊 Dataset de teste (casos conhecidos)
2. 🎯 Métricas de avaliação (como medir qualidade)
3. 🤖 Sistema automatizado de scoring
4. 📈 Relatórios e análises

BENEFÍCIOS:
- Qualidade consistente em produção
- Detecção precoce de problemas
- Otimização baseada em dados
- Confiança para fazer mudanças
""")

def mostrar_tipos_metricas():
    """
    Mostra diferentes tipos de métricas de avaliação.
    """
    print("""
🎯 TIPOS DE MÉTRICAS DE AVALIAÇÃO
=================================

1. MÉTRICAS DE QUALIDADE:
   - Relevância: resposta relacionada à pergunta
   - Precisão: fatos corretos
   - Completude: informação suficiente
   - Clareza: fácil de entender

2. MÉTRICAS DE COMPORTAMENTO:
   - Tom adequado (profissional, amigável)
   - Seguimento de instruções
   - Reconhecimento de limites
   - Consistência de respostas

3. MÉTRICAS TÉCNICAS:
   - Tempo de resposta
   - Uso de tokens/recursos
   - Taxa de erro
   - Disponibilidade

4. MÉTRICAS DE NEGÓCIO:
   - Satisfação do usuário
   - Redução de tickets de suporte
   - Conversão/engagement
   - ROI do sistema
""")

def configurar_ambiente():
    """
    Configuração para Evals.
    """
    print("""
📋 CONFIGURAÇÃO - EVALS BÁSICO
===============================

Dependências:
pip install pytest  # Para estrutura de testes
pip install pandas  # Para análise de dados

Configuração:
export LLM_PROVIDER=ollama
export MODEL_NAME=llama3:latest

IMPORTANTE:
- Use temperatura baixa (0.1) para consistência
- Crie datasets representativos do uso real
- Defina critérios claros de sucesso/falha
- Execute Evals regularmente (CI/CD)
""")

if __name__ == "__main__":
    configurar_ambiente()
    explicar_conceitos_evals()
    mostrar_tipos_metricas()

    resposta = input("\nDeseja executar o demo de Evals Básico? (s/n): ")
    if resposta.lower() in ['s', 'sim', 'y', 'yes']:
        demo_evals_basico()
    else:
        print("Demo cancelado.")