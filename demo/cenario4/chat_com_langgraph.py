"""
Cenário 4: Chat com LangGraph - Workflows Complexos
Demonstra a diferença entre LangChain (linear) e LangGraph (fluxos condicionais).
"""

from agentCore import get_llm, get_embeddings, get_logger
from langchain_core.messages import HumanMessage, SystemMessage, AIMessage
from langchain_core.documents import Document
from langgraph.graph import StateGraph, END
from langgraph.checkpoint.memory import MemorySaver
from typing import TypedDict, Annotated, List
from langchain.tools import Tool
import operator
import sqlite3
import os
from datetime import datetime
from dotenv import load_dotenv

load_dotenv()

class AgentState(TypedDict):
    """Estado compartilhado entre nós do grafo."""
    messages: Annotated[List, operator.add]
    next_step: str
    user_request: str
    analysis_type: str
    collected_data: dict
    final_recommendation: str
    confidence_score: float

def criar_ferramentas_negocio():
    """
    Cria ferramentas especializadas para análise de negócios.
    """
    def analisar_vendas(periodo: str) -> dict:
        """Simula análise de dados de vendas."""
        vendas_mock = {
            "q3_2024": {
                "receita": 2500000,
                "tickets": 150,
                "ticket_medio": 16667,
                "crescimento": "15%",
                "conversao": "3.2%"
            },
            "mensal": {
                "setembro": 900000,
                "agosto": 850000,
                "julho": 750000,
                "tendencia": "crescente"
            }
        }
        return vendas_mock.get(periodo, {"erro": "Período não encontrado"})

    def analisar_market_share(setor: str) -> dict:
        """Simula análise de market share."""
        market_data = {
            "tecnologia": {
                "nossa_posicao": "4º lugar",
                "participacao": "8.5%",
                "lider": "TechCorp (22%)",
                "crescimento_mercado": "12% ao ano"
            },
            "financeiro": {
                "nossa_posicao": "7º lugar",
                "participacao": "3.2%",
                "lider": "FinanceCorp (35%)",
                "crescimento_mercado": "6% ao ano"
            }
        }
        return market_data.get(setor, {"erro": "Setor não encontrado"})

    def analisar_concorrencia(concorrente: str) -> dict:
        """Análise competitiva."""
        competitors = {
            "techcorp": {
                "pontos_fortes": ["marca forte", "R&D avançado", "escala"],
                "pontos_fracos": ["preço alto", "atendimento", "inovação lenta"],
                "estrategia": "liderança tecnológica",
                "vulnerabilidades": ["startups disruptivas", "mudança de preferências"]
            },
            "startupx": {
                "pontos_fortes": ["agilidade", "inovação", "preço"],
                "pontos_fracos": ["recursos limitados", "marca fraca", "escala"],
                "estrategia": "disrupção de mercado",
                "vulnerabilidades": ["funding", "competição estabelecida"]
            }
        }
        return competitors.get(concorrente.lower(), {"erro": "Concorrente não encontrado"})

    return [
        Tool(name="analisar_vendas", description="Analisa dados de vendas por período", func=analisar_vendas),
        Tool(name="analisar_market_share", description="Analisa participação de mercado por setor", func=analisar_market_share),
        Tool(name="analisar_concorrencia", description="Analisa dados de concorrentes", func=analisar_concorrencia)
    ]

def criar_base_estrategica():
    """
    Base de conhecimento estratégico da empresa.
    """
    documentos = [
        Document(
            page_content="""
            Planejamento Estratégico 2024-2026

            Objetivos estratégicos:
            1. Aumentar market share de 8.5% para 15% em 3 anos
            2. Diversificar portfólio para reduzir dependência do produto principal
            3. Expandir para 3 novos mercados regionais
            4. Melhorar NPS de 7.2 para 8.5+
            5. Alcançar EBITDA de 35% (atual: 30%)

            Investimentos aprovados:
            - R$ 5M em P&D (foco IA e automação)
            - R$ 3M em expansão comercial
            - R$ 2M em marketing digital
            """,
            metadata={"source": "planejamento_estrategico.pdf", "category": "estrategia"}
        ),
        Document(
            page_content="""
            Análise SWOT - Atualização Q3 2024

            FORÇAS:
            - Equipe técnica qualificada (95% seniores)
            - Portfólio de produtos robustos
            - Relacionamento sólido com clientes (NPS 7.2)
            - Margem operacional saudável (30%)

            FRAQUEZAS:
            - Dependência de produto principal (70% receita)
            - Marketing limitado vs concorrentes
            - Processo de vendas longo (8 semanas)

            OPORTUNIDADES:
            - Crescimento do mercado de IA (50% ao ano)
            - Digitalização acelerada pós-pandemia
            - Necessidade de automação empresarial

            AMEAÇAS:
            - Entrada de big techs no mercado
            - Startups com soluções disruptivas
            - Recessão econômica global
            """,
            metadata={"source": "analise_swot.pdf", "category": "estrategia"}
        )
    ]
    return documentos

# Nós do grafo LangGraph
def analisar_solicitacao(state: AgentState) -> AgentState:
    """Primeiro nó: analisa o tipo de solicitação do usuário."""
    user_request = state["user_request"]

    # Lógica para classificar tipo de análise
    if any(word in user_request.lower() for word in ["vendas", "receita", "faturamento"]):
        analysis_type = "vendas"
    elif any(word in user_request.lower() for word in ["mercado", "concorrencia", "market share"]):
        analysis_type = "mercado"
    elif any(word in user_request.lower() for word in ["estrategia", "swot", "planejamento"]):
        analysis_type = "estrategico"
    else:
        analysis_type = "geral"

    print(f"🔍 Análise classificada como: {analysis_type}")

    return {
        **state,
        "analysis_type": analysis_type,
        "next_step": "coletar_dados"
    }

def coletar_dados(state: AgentState) -> AgentState:
    """Segundo nó: coleta dados baseado no tipo de análise."""
    analysis_type = state["analysis_type"]
    tools = criar_ferramentas_negocio()
    collected_data = {}

    print(f"📊 Coletando dados para análise: {analysis_type}")

    if analysis_type == "vendas":
        # Coleta dados de vendas
        tool_vendas = next(t for t in tools if t.name == "analisar_vendas")
        collected_data["q3"] = tool_vendas.func("q3_2024")
        collected_data["mensal"] = tool_vendas.func("mensal")

    elif analysis_type == "mercado":
        # Coleta dados de mercado e concorrência
        tool_market = next(t for t in tools if t.name == "analisar_market_share")
        tool_comp = next(t for t in tools if t.name == "analisar_concorrencia")
        collected_data["market"] = tool_market.func("tecnologia")
        collected_data["competitor1"] = tool_comp.func("techcorp")
        collected_data["competitor2"] = tool_comp.func("startupx")

    elif analysis_type == "estrategico":
        # Coleta dados estratégicos da base de conhecimento
        collected_data["strategy"] = "Dados estratégicos coletados da base"
        collected_data["swot"] = "Análise SWOT atualizada Q3 2024"
        collected_data["planning"] = "Planejamento estratégico 2024-2026"

    else:  # análise geral
        # Para análise geral, coleta dados de todas as fontes
        tool_vendas = next(t for t in tools if t.name == "analisar_vendas")
        tool_market = next(t for t in tools if t.name == "analisar_market_share")
        tool_comp = next(t for t in tools if t.name == "analisar_concorrencia")

        collected_data["vendas_q3"] = tool_vendas.func("q3_2024")
        collected_data["market_tech"] = tool_market.func("tecnologia")
        collected_data["competitor_main"] = tool_comp.func("techcorp")
        collected_data["base_estrategica"] = "Dados estratégicos da empresa"

    print(f"✅ Dados coletados: {len(collected_data)} fontes")

    return {
        **state,
        "collected_data": collected_data,
        "next_step": "analisar_dados"
    }

def analisar_dados(state: AgentState) -> AgentState:
    """Terceiro nó: analisa os dados coletados."""
    collected_data = state["collected_data"]
    analysis_type = state["analysis_type"]

    print(f"🧠 Analisando dados para {analysis_type}")

    # Simulação de análise com IA
    if analysis_type == "vendas":
        confidence = 0.85
        recommendation = """
        Análise de Vendas Q3 2024:
        - Crescimento sustentado de 15% vs Q2
        - Ticket médio saudável (R$ 16,667)
        - Tendência mensal positiva

        Recomendações:
        1. Manter estratégia atual de vendas
        2. Focar em aumentar taxa de conversão (atual 3.2%)
        3. Explorar oportunidades de upsell
        """
    elif analysis_type == "mercado":
        confidence = 0.78
        recommendation = """
        Análise de Market Share:
        - Posição: 4º lugar com 8.5% (meta: 15%)
        - Gap para líder: 13.5 pontos percentuais
        - Mercado crescendo 12% ao ano

        Ameaças Identificadas:
        - TechCorp: força em R&D mas vulnerável a startups
        - StartupX: agressiva em preço, mas recursos limitados

        Estratégia Recomendada:
        1. Atacar pontos fracos do líder (atendimento/inovação)
        2. Defender-se de startups com agilidade maior
        3. Investir em diferenciação tecnológica
        """
    elif analysis_type == "estrategico":
        confidence = 0.82
        recommendation = """
        Análise Estratégica - Próximos Passos:

        Situação Atual:
        - EBITDA: 30% (meta: 35%)
        - Market share: 8.5% (meta: 15%)
        - NPS: 7.2 (meta: 8.5+)

        Recomendações Estratégicas:
        1. CRESCIMENTO ORGÂNICO:
           • Investir R$ 5M em P&D focado em IA
           • Melhorar processo de vendas (reduzir de 8 para 5 semanas)
           • Aumentar conversão com marketing digital (R$ 2M)

        2. EXPANSÃO DE MERCADO:
           • Diversificar portfólio (reduzir dependência de 70% para 50%)
           • Expandir para 3 novos mercados regionais
           • Atacar pontos fracos do líder (atendimento/inovação)

        3. EFICIÊNCIA OPERACIONAL:
           • Automação para melhorar margem
           • Foco em clientes de maior valor (upsell)
           • Otimização de custos para atingir EBITDA 35%

        Próximos 90 dias:
        - Definir roadmap detalhado de P&D
        - Implementar campanha de marketing digital
        - Iniciar projeto de automação de vendas
        """
    else:  # análise geral
        confidence = 0.75
        # Usar dados coletados para análise abrangente
        vendas_data = collected_data.get("vendas_q3", {})
        market_data = collected_data.get("market_tech", {})

        recommendation = f"""
        Análise Estratégica Completa - Próximos Passos:

        SITUAÇÃO ATUAL:
        • Receita Q3: R$ {vendas_data.get('receita', 'N/A'):,} (crescimento: {vendas_data.get('crescimento', 'N/A')})
        • Market Share: {market_data.get('participacao', 'N/A')} - {market_data.get('nossa_posicao', 'N/A')}
        • Líder do mercado: {market_data.get('lider', 'N/A')}
        • Crescimento do mercado: {market_data.get('crescimento_mercado', 'N/A')}

        DIAGNÓSTICO:
        ✅ Pontos Fortes: Crescimento sustentado, margem saudável
        ⚠️ Desafios: Gap para liderança, dependência de produto principal
        🎯 Oportunidades: Mercado em crescimento, automação empresarial

        ESTRATÉGIA RECOMENDADA:

        1. CURTO PRAZO (3-6 meses):
           • Acelerar vendas: otimizar processo para reduzir ciclo
           • Aumentar conversão: melhorar qualificação de leads
           • Retenção: programa de success para aumentar NPS

        2. MÉDIO PRAZO (6-18 meses):
           • Diversificação: desenvolver 2 novos produtos/serviços
           • Expansão: entrar em mercados adjacentes
           • Eficiência: automação de processos internos

        3. LONGO PRAZO (18+ meses):
           • Liderança tecnológica: investimento em IA/ML
           • Acquisições estratégicas: consolidar posição
           • Internacionalização: explorar mercados externos

        MÉTRICAS-CHAVE A MONITORAR:
        - Market share (meta: 15% em 3 anos)
        - EBITDA (meta: 35%)
        - NPS (meta: 8.5+)
        - Diversificação de receita (meta: 50% produto principal)

        PRÓXIMOS PASSOS IMEDIATOS:
        1. Aprovação do board para investimentos priorizados
        2. Formação de task force para execução
        3. Definição de OKRs trimestrais alinhados à estratégia
        4. Setup de dashboard executivo para acompanhamento
        """

    return {
        **state,
        "final_recommendation": recommendation,
        "confidence_score": confidence,
        "next_step": "gerar_relatorio"
    }

def gerar_relatorio(state: AgentState) -> AgentState:
    """Nó final: gera relatório executivo."""
    print("📋 Gerando relatório executivo final")

    # Extrair informações do estado
    analysis_type = state.get("analysis_type", "N/A")
    confidence = state.get("confidence_score", 0)
    recommendation = state.get("final_recommendation", "Nenhuma recomendação disponível")
    collected_data = state.get("collected_data", {})

    # Exibir relatório completo
    print(f"\n{'='*80}")
    print(f"📊 RELATÓRIO EXECUTIVO - ANÁLISE {analysis_type.upper()}")
    print(f"{'='*80}")
    print(f"🎯 CONFIANÇA DA ANÁLISE: {confidence:.0%}")
    print(f"📈 FONTES DE DADOS: {len(collected_data)} fontes consultadas")
    print(f"\n📋 RECOMENDAÇÕES ESTRATÉGICAS:")
    print(recommendation)
    print(f"\n{'='*80}")

    # Adicionar sumário executivo
    summary = f"""
🔍 SUMÁRIO EXECUTIVO:
• Tipo de análise: {analysis_type}
• Confiança: {confidence:.0%}
• Fontes consultadas: {len(collected_data)}
• Status: Análise concluída com sucesso
"""
    print(summary)

    return {
        **state,
        "next_step": "finalizado"
    }

def decidir_proximo_passo(state: AgentState) -> str:
    """Função de decisão condicional do grafo."""
    next_step = state.get("next_step", "analisar_solicitacao")

    if next_step == "finalizado":
        return "__end__"
    return next_step

def demo_langgraph_vs_langchain():
    """
    Demonstra diferenças entre LangChain e LangGraph.
    """
    logger = get_logger("langgraph_demo")

    print("""
🔄 DEMONSTRAÇÃO: LANGCHAIN vs LANGGRAPH
=========================================

LANGCHAIN (Cenários 1-3):
- Fluxo LINEAR: Pergunta → Processamento → Resposta
- Sem decisões condicionais complexas
- Limitado para workflows simples

LANGGRAPH (Cenário 4):
- Fluxo CONDICIONAL: Múltiplos caminhos baseados em contexto
- Decisões inteligentes em cada etapa
- Ideal para análises complexas e workflows empresariais
""")

    try:
        # Configurar LLM
        provider = os.getenv("LLM_PROVIDER", "ollama")
        model_name = os.getenv("MODEL_NAME", "llama3:latest")
        llm = get_llm(provider_name=provider)

        # Criar grafo LangGraph
        workflow = StateGraph(AgentState)

        # Adicionar nós
        workflow.add_node("analisar_solicitacao", analisar_solicitacao)
        workflow.add_node("coletar_dados", coletar_dados)
        workflow.add_node("analisar_dados", analisar_dados)
        workflow.add_node("gerar_relatorio", gerar_relatorio)

        # Definir edges condicionais
        workflow.set_entry_point("analisar_solicitacao")
        workflow.add_conditional_edges(
            "analisar_solicitacao",
            decidir_proximo_passo,
            {
                "coletar_dados": "coletar_dados",
                "__end__": END
            }
        )
        workflow.add_conditional_edges(
            "coletar_dados",
            decidir_proximo_passo,
            {
                "analisar_dados": "analisar_dados",
                "__end__": END
            }
        )
        workflow.add_conditional_edges(
            "analisar_dados",
            decidir_proximo_passo,
            {
                "gerar_relatorio": "gerar_relatorio",
                "__end__": END
            }
        )
        workflow.add_conditional_edges(
            "gerar_relatorio",
            decidir_proximo_passo,
            {
                "__end__": END
            }
        )

        # Configurar persistência (opcional)
        memory = MemorySaver()
        app = workflow.compile(checkpointer=memory)

        # Cenários de teste
        cenarios = [
            "Preciso de uma análise completa das nossas vendas do Q3 para apresentar ao board",
            "Como estamos posicionados no mercado vs concorrência? Quais são as ameaças?",
            "Gostaria de uma análise estratégica para definir próximos passos da empresa"
        ]

        print("\n" + "="*80)
        print("🤖 ASSISTENTE ESTRATÉGICO COM LANGGRAPH")
        print("="*80)

        for i, pergunta in enumerate(cenarios, 1):
            print(f"\n{'='*70}")
            print(f"CENÁRIO {i}: {pergunta}")
            print('='*70)

            # Estado inicial
            initial_state = {
                "messages": [],
                "user_request": pergunta,
                "next_step": "analisar_solicitacao",
                "analysis_type": "",
                "collected_data": {},
                "final_recommendation": "",
                "confidence_score": 0.0
            }

            # Executar workflow
            print(f"\n🚀 Executando workflow LangGraph...")

            config = {"configurable": {"thread_id": f"scenario_{i}"}}
            result = app.invoke(initial_state, config=config)

            # Apresentar resultados
            print(f"\n📊 ANÁLISE CONCLUÍDA")
            print(f"Tipo: {result['analysis_type']}")
            print(f"Confiança: {result['confidence_score']:.0%}")
            print(f"\n📋 RECOMENDAÇÕES:")
            print(result['final_recommendation'])
            print("\n" + "="*70)

            logger.info(f"Cenário {i} processado via LangGraph")

        print("\n✅ Demo LangGraph concluída!")
        print("\n💡 OBSERVAÇÃO: O LangGraph permitiu workflows condicionais complexos")
        print("   que se adaptam automaticamente ao tipo de solicitação empresarial.")

    except Exception as e:
        error_msg = f"Erro durante execução LangGraph: {str(e)}"
        logger.error(error_msg)
        print(f"❌ {error_msg}")
        return False

    return True

def comparar_arquiteturas():
    """
    Comparação técnica detalhada.
    """
    print("""
🔍 COMPARAÇÃO TÉCNICA DETALHADA
================================

LANGCHAIN (Linear):
┌─────────────┐    ┌─────────────┐    ┌─────────────┐
│   Entrada   │───▶│ Processamento│───▶│   Saída     │
└─────────────┘    └─────────────┘    └─────────────┘

- Adequado para: Chat simples, RAG básico
- Limitações: Sem decisões condicionais, fluxo fixo

LANGGRAPH (Condicional):
                    ┌─────────────┐
                    │ Classificar │
                    │ Solicitação │
                    └──────┬──────┘
                           │
                    ┌──────▼──────┐
                    │  Decisão    │
                    │ Condicional │
                    └──┬──────┬───┘
                       │      │
        ┌─────────────▼┐    ┌▼─────────────┐
        │ Coletar     │    │ Análise      │
        │ Dados Vendas│    │ Estratégica  │
        └─────────────┘    └──────────────┘
                       │      │
                    ┌──▼──────▼───┐
                    │  Análise    │
                    │  Integrada  │
                    └─────────────┘

- Adequado para: Workflows complexos, análises estratégicas
- Vantagens: Adaptação automática, múltiplos caminhos
""")

def configurar_ambiente():
    """
    Configuração do ambiente.
    """
    print("""
📋 CONFIGURAÇÃO - LANGGRAPH
============================

Dependências adicionais:
pip install langgraph
pip install sqlite3  # Para persistência

Configuração padrão:
export LLM_PROVIDER=ollama
export MODEL_NAME=llama3:latest

Observação: LangGraph permite workflows mais sofisticados
que requerem planejamento cuidadoso da lógica de negócio.
""")

if __name__ == "__main__":
    configurar_ambiente()
    comparar_arquiteturas()

    print("\n🚀 Executando demo LangGraph automaticamente...")
    demo_langgraph_vs_langchain()