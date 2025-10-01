"""
Cenário 3: Chat com Base Vetorial + Tools
Demonstra assistente que consulta documentos E executa ações através de ferramentas.
"""

from agentCore import get_llm, get_embeddings, get_logger
from langchain_text_splitters import RecursiveCharacterTextSplitter
from langchain_chroma import Chroma
from langchain_core.messages import HumanMessage, SystemMessage
from langchain_core.documents import Document
from langchain.tools import Tool
from langchain.agents import create_react_agent, AgentExecutor
from langchain import hub
from langchain.prompts import ChatPromptTemplate
import os
import json
import requests
from datetime import datetime, timedelta
from dotenv import load_dotenv

load_dotenv()

def criar_weather_tool():
    """
    Cria uma ferramenta para consultar clima usando API OpenWeatherMap.
    """
    def consultar_clima(cidade: str) -> str:
        """Consulta informações de clima para uma cidade específica."""
        try:
            # API key para demonstração (usar API real em produção)
            api_key = os.getenv("OPENWEATHER_API_KEY", "demo_key")

            # Para demo, simular resposta da API
            if api_key == "demo_key":
                return f"""Clima em {cidade}:
                Temperatura: 25°C
                Descrição: Ensolarado
                Umidade: 60%
                Vento: 15 km/h

                (Dados simulados para demonstração)"""

            # Código real da API (comentado para demo)
            # url = f"https://api.openweathermap.org/data/2.5/weather?q={cidade}&appid={api_key}&units=metric&lang=pt"
            # response = requests.get(url)
            # data = response.json()
            # return f"Temperatura em {cidade}: {data['main']['temp']}°C, {data['weather'][0]['description']}"

        except Exception as e:
            return f"Erro ao consultar clima: {str(e)}"

    return Tool(
        name="consultar_clima",
        description="Consulta informações meteorológicas para uma cidade específica. Use quando perguntarem sobre tempo/clima.",
        func=consultar_clima
    )

def criar_calculadora_tool():
    """
    Cria ferramenta para cálculos matemáticos.
    """
    def calcular(expressao: str) -> str:
        """Realiza cálculos matemáticos seguros."""
        try:
            # Limpar a expressão removendo espaços extras e caracteres desnecessários
            expressao_limpa = expressao.strip()

            # Lista de operações permitidas para segurança
            allowed_chars = "0123456789+-*/.() "
            if not all(c in allowed_chars for c in expressao_limpa):
                return f"Erro: Expressão '{expressao_limpa}' contém caracteres não permitidos. Use apenas números e operações básicas (+, -, *, /, (), .)."

            result = eval(expressao_limpa)
            return f"Resultado: {result:,.2f}"
        except Exception as e:
            return f"Erro no cálculo: {str(e)}"

    return Tool(
        name="calculadora",
        description="Realiza cálculos matemáticos. Use quando precisar calcular valores, percentuais, etc.",
        func=calcular
    )

def criar_agenda_tool():
    """
    Cria ferramenta para simular consulta de agenda.
    """
    def consultar_agenda(data: str) -> str:
        """Consulta agenda para uma data específica."""
        try:
            # Simular agenda para demonstração
            agenda_demo = {
                "hoje": [
                    "09:00 - Reunião de equipe",
                    "11:00 - Call com cliente ABC",
                    "14:00 - Revisão de projeto",
                    "16:00 - Entrevista candidato"
                ],
                "today": [
                    "09:00 - Reunião de equipe",
                    "11:00 - Call com cliente ABC",
                    "14:00 - Revisão de projeto",
                    "16:00 - Entrevista candidato"
                ],
                "amanha": [
                    "08:30 - Standup daily",
                    "10:00 - Apresentação para diretoria",
                    "15:00 - Workshop interno"
                ],
                "outubro": [
                    "Workshop de inovação: 15/10 (dia todo)",
                    "Apresentação de resultados: 25/10 (14h)",
                    "Confraternização de equipe: 31/10 (18h)"
                ],
                "geral": [
                    "Standup diário: 9h (exceto sexta-feira)",
                    "Board meeting: primeira segunda-feira do mês (10h)",
                    "All hands: última sexta-feira do mês (16h)",
                    "Revisão de projetos: toda quinta-feira (14h)"
                ]
            }

            data_lower = data.lower().strip()

            # Busca por palavras-chave
            if any(keyword in data_lower for keyword in ["hoje", "today"]):
                compromissos = "\n".join(agenda_demo["hoje"])
                return f"Agenda para hoje:\n{compromissos}\n\nInformações adicionais:\n" + "\n".join(agenda_demo["geral"])
            elif "outubro" in data_lower:
                compromissos = "\n".join(agenda_demo["outubro"])
                return f"Reuniões especiais em outubro:\n{compromissos}\n\nReunião fixa:\n" + "\n".join(agenda_demo["geral"])
            elif "standup" in data_lower:
                return "Standup diário: 9h (exceto sexta-feira)"
            elif data_lower in agenda_demo:
                compromissos = "\n".join(agenda_demo[data_lower])
                return f"Agenda para {data}:\n{compromissos}"
            else:
                return f"Agenda para {data}:\nNenhum compromisso específico. Reuniões fixas:\n" + "\n".join(agenda_demo["geral"])

        except Exception as e:
            return f"Erro ao consultar agenda: {str(e)}"

    return Tool(
        name="consultar_agenda",
        description="Consulta agenda/compromissos. Use quando perguntarem sobre horários, reuniões, etc.",
        func=consultar_agenda
    )

def criar_base_conhecimento():
    """
    Cria base de conhecimento da empresa com foco em informações que podem precisar de ferramentas.
    """
    documentos = [
        Document(
            page_content="""
            Política de Viagens Corporativas

            Procedimentos para viagens a trabalho:
            - Solicitar aprovação com 15 dias de antecedência
            - Verificar condições climáticas do destino
            - Reservas de hotel: até R$ 300,00 por diária
            - Alimentação: R$ 150,00 por dia
            - Transporte: classe econômica para voos nacionais
            - Reembolso mediante apresentação de notas fiscais
            - Seguro viagem obrigatório para viagens internacionais

            Contato: viagens@empresa.com
            """,
            metadata={"source": "politica_viagens.pdf", "category": "rh"}
        ),
        Document(
            page_content="""
            Relatório Financeiro - Indicadores Q3 2024

            Principais métricas do trimestre:
            - Receita: R$ 2.500.000 (crescimento de 15% vs Q2)
            - EBITDA: R$ 750.000 (30% da receita)
            - Margem líquida: 18%
            - Inadimplência: 2.1%
            - ROI médio dos projetos: 340%
            - Meta anual: R$ 12.000.000 (83% alcançado)

            Projeção Q4: R$ 3.200.000 (considerar sazonalidade)
            """,
            metadata={"source": "relatorio_financeiro_q3.pdf", "category": "financeiro"}
        ),
        Document(
            page_content="""
            Cronograma de Reuniões - Outubro 2024

            Reuniões fixas mensais:
            - Board meeting: primeira segunda-feira do mês (10h)
            - All hands: última sexta-feira do mês (16h)
            - Revisão de projetos: toda quinta-feira (14h)
            - Standup: diário às 9h (exceto sexta-feira)

            Reuniões especiais outubro:
            - Workshop de inovação: 15/10 (dia todo)
            - Apresentação de resultados: 25/10 (14h)
            - Confraternização de equipe: 31/10 (18h)
            """,
            metadata={"source": "cronograma_reunioes.pdf", "category": "gestao"}
        )
    ]

    return documentos

def demo_chat_rag_com_tools():
    """
    Demonstra chat com RAG + ferramentas externas.
    """
    logger = get_logger("chat_rag_tools")

    # Configurações
    provider = os.getenv("LLM_PROVIDER", "ollama")
    model_name = os.getenv("MODEL_NAME", "llama3:latest")
    vector_provider = os.getenv("VECTOR_PROVIDER", "chroma")

    logger.info(f"Iniciando RAG+Tools com LLM: {provider}/{model_name}")

    try:
        print("🛠️ Configurando ferramentas...")

        # 1. Criar ferramentas
        tools = [
            criar_weather_tool(),
            criar_calculadora_tool(),
            criar_agenda_tool()
        ]

        print(f"✅ {len(tools)} ferramentas configuradas")
        print("🔧 Ferramentas disponíveis:")
        for tool in tools:
            print(f"   - {tool.name}: {tool.description}")
        print()

        # 2. Criar base de conhecimento
        print("📚 Criando base de conhecimento...")
        documentos = criar_base_conhecimento()

        # 3. Processar documentos
        text_splitter = RecursiveCharacterTextSplitter(
            chunk_size=500,
            chunk_overlap=50,
            length_function=len,
        )
        chunks = text_splitter.split_documents(documentos)

        # 4. Configurar vector store
        embeddings = get_embeddings(provider_name=provider)

        # Criar vector store usando Chroma diretamente
        texts = [chunk.page_content for chunk in chunks]
        metadatas = [chunk.metadata for chunk in chunks]

        vector_store = Chroma.from_texts(
            texts=texts,
            embedding=embeddings,
            metadatas=metadatas,
            collection_name="rag_tools_demo"
        )
        print("✅ Base de conhecimento indexada")

        # 5. Configurar LLM
        llm = get_llm(provider_name=provider)

        # 6. Criar retriever como ferramenta
        retriever = vector_store.as_retriever(search_kwargs={"k": 3})

        def consultar_documentos(pergunta: str) -> str:
            """Consulta documentos internos da empresa."""
            docs = retriever.invoke(pergunta)
            if docs:
                contexto = "\n\n".join([doc.page_content for doc in docs])
                fontes = [doc.metadata.get('source', 'sem fonte') for doc in docs]
                return f"Informações encontradas:\n{contexto}\n\nFontes: {', '.join(set(fontes))}"
            return "Nenhuma informação encontrada nos documentos internos."

        # Adicionar retriever como ferramenta
        retriever_tool = Tool(
            name="consultar_documentos",
            description="Consulta documentos internos da empresa sobre políticas, procedimentos, relatórios, etc.",
            func=consultar_documentos
        )
        tools.append(retriever_tool)

        # 7. Criar prompt personalizado para melhor compatibilidade com Ollama
        prompt_template = """Responda às seguintes perguntas da melhor forma possível. Você tem acesso às seguintes ferramentas:

{tools}

Use EXATAMENTE o seguinte formato:

Question: a pergunta de entrada que você deve responder
Thought: você deve sempre pensar sobre o que fazer
Action: a ação a ser tomada, deve ser EXATAMENTE uma das ferramentas: [{tool_names}]
Action Input: a entrada para a ação (apenas o texto/valor, sem formatação extra)
Observation: o resultado da ação
... (este processo Thought/Action/Action Input/Observation pode repetir N vezes)
Thought: Agora eu sei a resposta final
Final Answer: a resposta final à pergunta original

IMPORTANTE:
- Use APENAS os nomes exatos das ferramentas: {tool_names}
- Para Action Input, forneça apenas o valor necessário, sem aspas ou formatação extra
- SEMPRE termine com "Final Answer:" seguido da resposta completa
- Exemplos corretos:
  Action: consultar_clima
  Action Input: São Paulo
  Observation: Clima em São Paulo: 25°C
  Thought: Agora eu sei a resposta final
  Final Answer: O clima em São Paulo está 25°C

  Action: calculadora
  Action Input: 2500000 * 0.15
  Observation: Resultado: 375,000.00
  Thought: Agora eu sei a resposta final
  Final Answer: 15% de 2.500.000 é igual a 375.000,00

Comece!

Question: {input}
Thought:{agent_scratchpad}"""

        prompt = ChatPromptTemplate.from_template(prompt_template)

        # 8. Criar agente ReAct (compatível com Ollama)
        agent = create_react_agent(llm, tools, prompt)
        agent_executor = AgentExecutor(
            agent=agent,
            tools=tools,
            verbose=True,
            handle_parsing_errors=True,
            max_iterations=3,
            return_intermediate_steps=True
        )

        # 9. Perguntas de exemplo que requerem diferentes ferramentas
        perguntas = [
            "Qual é a política de viagens da empresa e como está o clima em São Paulo hoje?",
            "Preciso calcular 15% de crescimento sobre nossa receita atual de R$ 2.500.000. Quanto seria?",
            "Quais são as reuniões programadas para hoje e que horas é o standup?",
            "Qual é nossa margem EBITDA e quanto precisamos para atingir a meta anual?",
            "Há alguma reunião especial em outubro e como está o tempo para a confraternização?"
        ]

        print("\n" + "="*80)
        print("🤖 ASSISTENTE EMPRESARIAL COM RAG + FERRAMENTAS")
        print("="*80)

        for i, pergunta in enumerate(perguntas, 1):
            print(f"\n{'='*70}")
            print(f"PERGUNTA {i}: {pergunta}")
            print('='*70)

            # Executar agente com tratamento de erro melhorado
            try:
                response = agent_executor.invoke({"input": pergunta})

                if 'output' in response:
                    print(f"RESPOSTA: {response['output']}")
                else:
                    # Fallback para respostas sem formato correto
                    print(f"RESPOSTA: Não foi possível processar a pergunta completamente.")

                    # Tentar resposta direta sem agente
                    print("Tentando resposta direta...")
                    direct_response = llm.invoke([HumanMessage(content=pergunta)])
                    print(f"RESPOSTA DIRETA: {direct_response.content}")

            except Exception as agent_error:
                print(f"⚠️ Erro no agente: {str(agent_error)}")
                print("Tentando resposta direta sem ferramentas...")

                try:
                    # Fallback: resposta direta do LLM
                    direct_response = llm.invoke([HumanMessage(content=pergunta)])
                    print(f"RESPOSTA DIRETA: {direct_response.content}")
                except Exception as direct_error:
                    print(f"❌ Erro na resposta direta: {str(direct_error)}")

            print()

            logger.info(f"Pergunta {i} processada com sucesso")

        print("\n✅ Demo RAG + Tools concluída com sucesso!")
        print("\n💡 OBSERVAÇÃO: O assistente combinou informações de documentos internos")
        print("   com ferramentas externas para fornecer respostas completas e acionáveis.")

        logger.info("Demo RAG + Tools finalizada com sucesso")

    except Exception as e:
        error_msg = f"Erro durante execução do RAG + Tools: {str(e)}"
        logger.error(error_msg)
        print(f"❌ {error_msg}")
        return False

    return True

def demonstrar_evolucao():
    """
    Mostra a evolução dos cenários.
    """
    print("""
🚀 EVOLUÇÃO DOS CENÁRIOS DE CHAT

CENÁRIO 1 (Chat Básico):
📝 Conversa simples com IA
❌ Conhecimento limitado ao treinamento do modelo
❌ Não acessa informações em tempo real
❌ Não executa ações

CENÁRIO 2 (RAG):
📚 + Acesso a documentos internos
✅ Respostas baseadas em conhecimento empresarial
❌ Ainda não executa ações externas
❌ Informações apenas estáticas

CENÁRIO 3 (RAG + Tools):
🛠️ + Ferramentas externas
✅ Consulta documentos E executa ações
✅ Informações em tempo real (clima, cálculos)
✅ Integração com sistemas externos
✅ Assistente verdadeiramente útil e acionável
""")

def configurar_ambiente():
    """
    Instruções de configuração.
    """
    print("""
📋 CONFIGURAÇÃO DO AMBIENTE - RAG + TOOLS
=========================================

Variáveis obrigatórias:
export LLM_PROVIDER=ollama
export MODEL_NAME=llama3:latest
export VECTOR_PROVIDER=chroma

Variáveis opcionais:
export OPENWEATHER_API_KEY=sua_chave_api  # Para clima real

Dependências:
pip install langchain-community
pip install requests
""")

if __name__ == "__main__":
    configurar_ambiente()
    demonstrar_evolucao()

    print("\n🚀 Executando demo RAG + Tools automaticamente...")
    demo_chat_rag_com_tools()