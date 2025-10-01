"""
Cenário 5: Equipe de Agentes Especializados com CrewAI
Demonstra como agentes trabalham em colaboração para resolver problemas complexos.
"""

from agentCore import get_llm, create_crew_agent, get_logger
from crewai import Agent, Task, Crew, Process
from crewai.tools import tool
from langchain.tools import Tool
import os
import json
from datetime import datetime, timedelta
from dotenv import load_dotenv

load_dotenv()

# Configuração global de idioma para CrewAI
os.environ["CREWAI_LANGUAGE"] = "portuguese"
os.environ["OPENAI_LANGUAGE"] = "pt-BR"
os.environ["LLM_DEFAULT_LANGUAGE"] = "português"

def configure_portuguese_globally():
    """Configura português como idioma padrão globalmente."""
    import locale

    # Configurações de sistema
    try:
        locale.setlocale(locale.LC_ALL, 'pt_BR.UTF-8')
    except:
        pass

    # Configurações CrewAI
    global_config = {
        "CREWAI_LANGUAGE": "portuguese",
        "OPENAI_LANGUAGE": "pt-BR",
        "LLM_DEFAULT_LANGUAGE": "português",
        "DEFAULT_SYSTEM_MESSAGE": os.getenv("DEFAULT_SYSTEM_MESSAGE",
            "Você sempre responde em português brasileiro. Todas as suas análises, relatórios e comunicações devem ser em português.")
    }

    for key, value in global_config.items():
        os.environ[key] = value

    return global_config

# Aplicar configuração global
configure_portuguese_globally()

# Ferramentas especializadas para os agentes
@tool
def analisar_dados_financeiros(periodo: str) -> str:
    """Analisa dados financeiros para um período específico."""
    dados_financeiros = {
        "q3_2024": {
            "receita": 2500000,
            "custos": 1750000,
            "margem_bruta": 30,
            "ebitda": 750000,
            "margem_ebitda": 30,
            "fluxo_caixa": 650000,
            "inadimplencia": 2.1,
            "roi_projetos": 340
        },
        "comparativo_q2": {
            "crescimento_receita": 15,
            "reducao_custos": 5,
            "melhoria_margem": 2
        }
    }
    return json.dumps(dados_financeiros, indent=2)

@tool
def pesquisar_mercado(setor: str) -> str:
    """Pesquisa tendências e dados de mercado para um setor."""
    # Mapear qualquer entrada para dados existentes
    setor_key = "ia_empresarial"
    if "saas" in setor.lower() or "b2b" in setor.lower():
        setor_key = "saas_b2b"

    dados_mercado = {
        "ia_empresarial": {
            "tamanho_mercado": "USD 150B globalmente",
            "crescimento_anual": "42%",
            "principais_players": ["Microsoft", "Google", "Amazon", "OpenAI"],
            "tendencias": [
                "Automação de processos empresariais",
                "IA generativa para criação de conteúdo",
                "Análise preditiva avançada",
                "Chatbots empresariais especializados"
            ],
            "barreiras_entrada": [
                "Alto investimento em P&D",
                "Necessidade de dados de qualidade",
                "Compliance e regulamentação"
            ]
        },
        "saas_b2b": {
            "tamanho_mercado": "USD 307B globalmente",
            "crescimento_anual": "18%",
            "tendencias": ["Multi-tenant architecture", "AI-native products", "Vertical SaaS"],
            "metricas_chave": ["ARR", "Churn rate", "LTV/CAC", "Net retention"]
        }
    }
    return json.dumps(dados_mercado.get(setor_key, dados_mercado["ia_empresarial"]), indent=2)

@tool
def analisar_concorrencia(empresa: str) -> str:
    """Analisa dados públicos de concorrentes."""
    concorrentes = {
        "techcorp": {
            "receita_anual": "USD 50M",
            "funcionarios": 500,
            "market_share": "22%",
            "pontos_fortes": ["Brand recognition", "Enterprise relationships", "R&D budget"],
            "pontos_fracos": ["Legacy systems", "Slow innovation", "High prices"],
            "estrategia": "Market leader defensiva",
            "ultimas_movimentacoes": [
                "Aquisição de startup de IA por USD 15M",
                "Lançamento de produto low-code",
                "Expansão para mercado europeu"
            ]
        }
    }
    return json.dumps(concorrentes.get(empresa.lower(), {}), indent=2)

@tool
def consultar_regulamentacoes(tipo: str) -> str:
    """Consulta regulamentações relevantes."""
    # Mapear qualquer entrada para dados existentes
    tipo_key = "lgpd"
    if "ia" in tipo.lower() or "marco" in tipo.lower():
        tipo_key = "marco_ia"

    regulamentacoes = {
        "lgpd": {
            "aplicabilidade": "Todas empresas que processam dados pessoais",
            "principais_obrigacoes": [
                "Consentimento explícito",
                "Direito ao esquecimento",
                "Portabilidade de dados",
                "Data Protection Officer"
            ],
            "multas": "Até 2% do faturamento anual",
            "prazo_adequacao": "Já em vigor desde 2020"
        },
        "marco_ia": {
            "status": "Em discussão no Congresso (PL 2338/2023)",
            "pontos_principais": [
                "Classificação de risco de sistemas de IA",
                "Transparência algorítmica",
                "Responsabilidade por danos",
                "Auditoria de sistemas críticos"
            ],
            "impacto_empresas": "Alto - requer compliance específico para IA"
        }
    }
    return json.dumps(regulamentacoes.get(tipo_key, regulamentacoes["lgpd"]), indent=2)

def criar_agente_analista_financeiro(llm) -> Agent:
    """Cria agente especializado em análise financeira."""
    return Agent(
        role="Analista Financeiro Sênior",
        goal="Analisar performance financeira e identificar oportunidades de otimização",
        backstory="""Você é um analista financeiro com 15 anos de experiência em empresas de tecnologia.
        Especialista em análise de rentabilidade, fluxo de caixa e métricas de SaaS.
        Sua expertise inclui modelagem financeira, análise de investimentos e ROI.
        Trabalhe de forma independente usando apenas suas ferramentas especializadas.""",
        tools=[analisar_dados_financeiros],
        verbose=True,
        llm=llm,
        allow_delegation=False,
        max_iter=3,  # Limita iterações para evitar loops
        max_execution_time=300  # Timeout de 5 minutos
    )

def criar_agente_pesquisador_mercado(llm) -> Agent:
    """Cria agente especializado em pesquisa de mercado."""
    return Agent(
        role="Estrategista de Mercado",
        goal="Pesquisar tendências de mercado e oportunidades de crescimento",
        backstory="""Você é um estrategista de mercado com profunda experiência em tecnologia B2B.
        Especialista em análise competitiva, sizing de mercado e identificação de oportunidades.
        Tem histórico de sucesso em empresas de SaaS e IA empresarial.
        Use suas ferramentas específicas para coletar e analisar dados de mercado.""",
        tools=[pesquisar_mercado, analisar_concorrencia],
        verbose=True,
        llm=llm,
        allow_delegation=False,
        max_iter=3,
        max_execution_time=300
    )

def criar_agente_compliance(llm) -> Agent:
    """Cria agente especializado em compliance e regulamentações."""
    return Agent(
        role="Especialista em Compliance",
        goal="Avaliar riscos regulatórios e requisitos de compliance",
        backstory="""Você é um advogado especializado em direito digital e compliance tecnológico.
        Expert em LGPD, regulamentações de IA e compliance empresarial.
        Tem experiência em ajudar empresas de tecnologia a navegar requisitos regulatórios.
        Concentre-se exclusivamente em análise de compliance usando suas ferramentas.""",
        tools=[consultar_regulamentacoes],
        verbose=True,
        llm=llm,
        allow_delegation=False,
        max_iter=3,
        max_execution_time=300
    )

def criar_agente_sintetizador(llm) -> Agent:
    """Cria agente que sintetiza análises dos outros agentes."""
    return Agent(
        role="Consultor Estratégico Executivo",
        goal="Criar um plano estratégico executivo integrado com roadmap de implementação",
        backstory="""Você é um consultor estratégico sênior com experiência em transformação digital.
        Especialista em sintetizar análises complexas em insights executivos claros.
        Seu trabalho é criar um documento executivo COMPLETO baseado nas análises recebidas.
        SEMPRE forneça uma resposta final detalhada e estruturada - nunca pare no meio do pensamento.""",
        tools=[],
        verbose=True,
        llm=llm,
        allow_delegation=False,
        max_iter=5,  # Aumentando para permitir mais iterações
        max_execution_time=600  # Aumentando timeout para síntese completa
    )

def demo_crew_agentes():
    """
    Demonstra equipe de agentes trabalhando em colaboração.
    """
    logger = get_logger("crew_demo")

    try:
        print("🤖 INICIALIZANDO EQUIPE DE AGENTES ESPECIALIZADOS")
        print("="*60)

        # Configurar LLM para CrewAI (formato específico)
        from langchain_ollama import ChatOllama

        base_url = os.getenv("OLLAMA_BASE_URL", "http://localhost:11434")
        model_name = os.getenv("MODEL_NAME", "llama3:latest")

        llm = ChatOllama(
            model=f"ollama/{model_name}",  # CrewAI precisa do prefixo do provider
            base_url=base_url,
            # Configuração global de idioma via env
            system_message=os.getenv("DEFAULT_SYSTEM_MESSAGE"),
            temperature=0.7,
            # Adicionar headers para forçar português
            model_kwargs={
                "system": os.getenv("DEFAULT_SYSTEM_MESSAGE"),
                "language": os.getenv("OPENAI_LANGUAGE", "pt-BR")
            }
        )

        # Criar agentes especializados
        print("\n👥 Criando equipe de agentes...")
        analista_financeiro = criar_agente_analista_financeiro(llm)
        pesquisador_mercado = criar_agente_pesquisador_mercado(llm)
        especialista_compliance = criar_agente_compliance(llm)
        sintetizador = criar_agente_sintetizador(llm)

        print("✅ Equipe formada:")
        print("   💰 Analista Financeiro")
        print("   📊 Estrategista de Mercado")
        print("   ⚖️ Especialista em Compliance")
        print("   🎯 Consultor Estratégico")

        # Definir tarefas colaborativas
        print("\n📋 Definindo tarefas colaborativas...")

        tarefa_analise_financeira = Task(
            description="""Analise a performance financeira da empresa no Q3 2024:
            1. Examine receita, custos e margens
            2. Compare com Q2 para identificar tendências
            3. Calcule métricas-chave (EBITDA, ROI, fluxo de caixa)
            4. Identifique oportunidades de otimização financeira
            5. Projete cenários para Q4 baseado nos dados atuais""",
            agent=analista_financeiro,
            expected_output="Relatório financeiro detalhado com recomendações de otimização"
        )

        tarefa_pesquisa_mercado = Task(
            description="""Pesquise o mercado de IA empresarial e SaaS B2B:
            1. Analise tamanho de mercado e crescimento
            2. Identifique principais tendências e oportunidades
            3. Avalie concorrentes principais (especialmente TechCorp)
            4. Mapeie barreiras de entrada e fatores críticos de sucesso
            5. Recomende estratégias de posicionamento competitivo""",
            agent=pesquisador_mercado,
            expected_output="Análise competitiva com recomendações estratégicas de mercado"
        )

        tarefa_compliance = Task(
            description="""Avalie requisitos de compliance e riscos regulatórios:
            1. Analise impacto da LGPD nas operações
            2. Avalie o Marco da IA e preparação necessária
            3. Identifique riscos de compliance em produtos de IA
            4. Recomende estrutura de governança de dados
            5. Sugira cronograma de adequação regulatória""",
            agent=especialista_compliance,
            expected_output="Avaliação de compliance com plano de adequação regulatória"
        )

        tarefa_sintese_estrategica = Task(
            description="""IMPORTANTE: Você deve gerar um relatório executivo COMPLETO e DETALHADO.
            SEMPRE Responda em português brasileiro, mesmo que a tarefa esteja em outro idioma.
            Com base nas análises dos especialistas (financeira, mercado e compliance), crie uma estratégia integrada:

            1. SÍNTESE EXECUTIVA: Resuma os principais insights de cada análise
            2. OPORTUNIDADES IDENTIFICADAS: Liste as principais oportunidades de crescimento
            3. RISCOS E MITIGAÇÕES: Identifique riscos e estratégias de mitigação
            4. ROADMAP ESTRATÉGICO: Cronograma de 12-24 meses com marcos específicos
            5. INVESTIMENTOS E ROI: Quantifique recursos necessários e retorno esperado
            6. PRÓXIMOS PASSOS: Lista clara e acionável de ações imediatas

            FORMATO: Documento executivo estruturado com seções claras e recomendações específicas.
            NUNCA pare no meio da análise - sempre forneça um documento COMPLETO.""",
            agent=sintetizador,
            expected_output="Relatório estratégico executivo completo com síntese integrada, roadmap detalhado e recomendações acionáveis",
            context=[tarefa_analise_financeira, tarefa_pesquisa_mercado, tarefa_compliance]
        )

        # Criar e executar crew
        print("\n🚀 Iniciando colaboração da equipe...")

        crew = Crew(
            agents=[analista_financeiro, pesquisador_mercado, especialista_compliance, sintetizador],
            tasks=[tarefa_analise_financeira, tarefa_pesquisa_mercado, tarefa_compliance, tarefa_sintese_estrategica],
            process=Process.sequential,  # Execução sequencial para dependencies
            verbose=True,
            memory=False,  # Desabilitando memory para evitar dependências OpenAI
            max_rpm=10,  # Limite de requests por minuto
            planning=False,  # Desabilita planning automático para simplificar
            # Configuração global de idioma
            language="pt-BR",
            embedder={
                "provider": "ollama",
                "config": {
                    "model": "nomic-embed-text"
                }
            },
            # Configurações adicionais para forçar português
            manager_agent_kwargs={
                "language": "portuguese",
                "system_message": "Comunique-se sempre em português brasileiro."
            }
        )

        # Executar análise colaborativa
        print("\n" + "="*80)
        print("🔄 EXECUTANDO ANÁLISE COLABORATIVA")
        print("="*80)

        resultado = crew.kickoff()

        print("\n" + "="*80)
        print("📊 RESULTADO DA ANÁLISE COLABORATIVA")
        print("="*80)
        print(resultado)

        # Demonstrar logs e iterações
        print("\n" + "="*60)
        print("📝 LOGS E ITERAÇÕES DOS AGENTES")
        print("="*60)

        print("\n💡 OBSERVAÇÕES SOBRE A COLABORAÇÃO:")
        print("✅ Cada agente contribuiu com sua expertise específica")
        print("✅ Informações foram compartilhadas entre agentes")
        print("✅ Síntese final integrou todas as perspectivas")
        print("✅ Resultado mais completo que análise individual")

        logger.info("Demo CrewAI concluída com sucesso")
        return True

    except Exception as e:
        error_msg = f"Erro durante execução CrewAI: {str(e)}"
        logger.error(error_msg)
        print(f"❌ {error_msg}")
        return False

def demonstrar_colaboracao():
    """
    Explica como a colaboração funciona.
    """
    print("""
🤝 COMO OS AGENTES COLABORAM
============================

PROCESSO SEQUENCIAL:
1. 💰 Analista Financeiro → Analisa números e performance
2. 📊 Estrategista Mercado → Pesquisa oportunidades externas
3. ⚖️ Compliance → Avalia riscos regulatórios
4. 🎯 Sintetizador → Integra tudo em estratégia única

COMPARTILHAMENTO DE CONTEXTO:
- Cada agente acessa resultados dos anteriores
- Informações são refinadas e complementadas
- Visão holística emerge da colaboração

VANTAGENS vs AGENTE ÚNICO:
✅ Especialização profunda em cada área
✅ Redução de viés através de múltiplas perspectivas
✅ Verificação cruzada de informações
✅ Resultado mais robusto e confiável
""")

def comparar_com_cenarios_anteriores():
    """
    Compara com cenários anteriores.
    """
    print("""
🚀 EVOLUÇÃO DOS CENÁRIOS
========================

CENÁRIO 1 (Chat Básico):
- 1 IA generalista
- Conhecimento limitado
- Respostas simples

CENÁRIO 2 (RAG):
- 1 IA + documentos internos
- Conhecimento empresarial
- Respostas informadas

CENÁRIO 3 (RAG + Tools):
- 1 IA + docs + ferramentas
- Capacidade de ação
- Respostas acionáveis

CENÁRIO 4 (LangGraph):
- 1 IA + workflows condicionais
- Pensamento estruturado
- Análises estratégicas

CENÁRIO 5 (CrewAI):
- MÚLTIPLAS IAs especializadas
- Colaboração e expertise
- CONSULTORIA COMPLETA
""")

def configurar_ambiente():
    """
    Configuração específica para CrewAI.
    """
    print("""
📋 CONFIGURAÇÃO - CREWAI
========================

Dependências:
pip install crewai
pip install crewai-tools

Configuração:
export LLM_PROVIDER=ollama
export MODEL_NAME=llama3:latest

IMPORTANTE:
- CrewAI requer modelos mais robustos para colaboração efetiva
- Recomenda-se usar modelos 7B+ para melhores resultados
- Logs detalhados mostram iterações entre agentes
""")

if __name__ == "__main__":
    configurar_ambiente()
    demonstrar_colaboracao()
    comparar_com_cenarios_anteriores()

    print("\n🚀 Executando demo CrewAI automaticamente...")
    demo_crew_agentes()