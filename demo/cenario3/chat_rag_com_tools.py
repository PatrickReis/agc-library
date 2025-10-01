"""
Cenário 3: Chat com Base Vetorial + Tools de Adquirência
Demonstra assistente que consulta documentos E executa ações através de ferramentas especializadas.

CONTEXTO: Adquirência - Combina RAG (manuais, políticas) com Tools (APIs de transações, cálculos, chamados)
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
from datetime import datetime, timedelta
from dotenv import load_dotenv

load_dotenv()

def criar_tool_consultar_transacoes():
    """
    Ferramenta para consultar transações de um merchant (simula API de adquirência).
    """
    def consultar_transacoes(merchant_id: str) -> str:
        """Consulta transações recentes de um merchant específico."""
        try:
            # Simular API de transações
            transacoes_db = {
                "12345": [
                    {
                        "nsu": "987654321",
                        "data_hora": "2024-10-14 14:23:15",
                        "valor_bruto": 5800.00,
                        "modalidade": "credito_vista",
                        "bandeira": "Visa",
                        "parcelas": 1,
                        "status": "aprovada",
                        "codigo_autorizacao": "ABC123",
                        "mdr": 2.99,
                        "valor_mdr": 173.42,
                        "valor_liquido": 5626.58,
                        "liquidacao_prevista": "2024-11-14",
                        "terminal": "PAX-D195-001"
                    },
                    {
                        "nsu": "987654320",
                        "data_hora": "2024-10-14 10:15:30",
                        "valor_bruto": 1250.00,
                        "modalidade": "debito",
                        "bandeira": "Mastercard",
                        "parcelas": 1,
                        "status": "aprovada",
                        "codigo_autorizacao": "XYZ789",
                        "mdr": 1.49,
                        "valor_mdr": 18.63,
                        "valor_liquido": 1231.37,
                        "liquidacao_prevista": "2024-10-15",
                        "terminal": "PAX-D195-001"
                    },
                    {
                        "nsu": "987654319",
                        "data_hora": "2024-10-13 16:45:00",
                        "valor_bruto": 3200.00,
                        "modalidade": "credito_parcelado",
                        "bandeira": "Visa",
                        "parcelas": 6,
                        "status": "aprovada",
                        "codigo_autorizacao": "DEF456",
                        "mdr": 3.99,
                        "valor_mdr": 127.68,
                        "valor_liquido": 3072.32,
                        "liquidacao_prevista": "2024-11-13",
                        "terminal": "PAX-D195-001"
                    }
                ],
                "67890": [
                    {
                        "nsu": "555444333",
                        "data_hora": "2024-10-14 18:30:00",
                        "valor_bruto": 8500.00,
                        "modalidade": "credito_vista",
                        "bandeira": "Mastercard",
                        "parcelas": 1,
                        "status": "aprovada",
                        "codigo_autorizacao": "GHI789",
                        "mdr": 2.49,
                        "valor_mdr": 211.65,
                        "valor_liquido": 8288.35,
                        "liquidacao_prevista": "2024-11-14",
                        "terminal": "INGENICO-MOVE5000-002"
                    }
                ]
            }

            if merchant_id in transacoes_db:
                transacoes = transacoes_db[merchant_id]
                resultado = f"Transações do merchant {merchant_id}:\n\n"

                for i, txn in enumerate(transacoes, 1):
                    resultado += f"Transação {i}:\n"
                    resultado += f"  NSU: {txn['nsu']}\n"
                    resultado += f"  Data/Hora: {txn['data_hora']}\n"
                    resultado += f"  Valor Bruto: R$ {txn['valor_bruto']:,.2f}\n"
                    resultado += f"  Modalidade: {txn['modalidade']}\n"
                    resultado += f"  Bandeira: {txn['bandeira']}\n"
                    resultado += f"  Status: {txn['status']}\n"
                    resultado += f"  MDR: {txn['mdr']}% (R$ {txn['valor_mdr']:,.2f})\n"
                    resultado += f"  Valor Líquido: R$ {txn['valor_liquido']:,.2f}\n"
                    resultado += f"  Liquidação Prevista: {txn['liquidacao_prevista']}\n"
                    resultado += f"  Terminal: {txn['terminal']}\n\n"

                total_bruto = sum(t['valor_bruto'] for t in transacoes)
                total_liquido = sum(t['valor_liquido'] for t in transacoes)
                resultado += f"TOTAIS:\n"
                resultado += f"  Valor Bruto Total: R$ {total_bruto:,.2f}\n"
                resultado += f"  Valor Líquido Total: R$ {total_liquido:,.2f}\n"

                return resultado
            else:
                return f"Nenhuma transação encontrada para merchant {merchant_id}. Merchant IDs disponíveis para demo: 12345, 67890"

        except Exception as e:
            return f"Erro ao consultar transações: {str(e)}"

    return Tool(
        name="consultar_transacoes",
        description="Consulta transações de um merchant específico. Use quando perguntarem sobre vendas, valores, liquidação. Input: merchant_id (exemplo: 12345)",
        func=consultar_transacoes
    )

def criar_tool_calcular_mdr():
    """
    Ferramenta para calcular MDR por segmento e modalidade.
    """
    def calcular_mdr(parametros: str) -> str:
        """Calcula MDR para um segmento e modalidade. Input no formato 'segmento,modalidade' (exemplo: 'restaurante,credito_vista')"""
        try:
            # Parse dos parâmetros
            parts = parametros.split(',')
            if len(parts) != 2:
                return "Erro: forneça os parâmetros no formato 'segmento,modalidade' (exemplo: 'restaurante,credito_vista')"

            segmento = parts[0].strip().lower()
            modalidade = parts[1].strip().lower()

            # Tabela de MDR
            tabela_mdr = {
                "supermercado": {
                    "debito": 0.99,
                    "credito_vista": 2.49,
                    "credito_parcelado_2_6": 3.49,
                    "credito_parcelado_7_12": 3.99
                },
                "restaurante": {
                    "debito": 1.49,
                    "credito_vista": 2.99,
                    "credito_parcelado_2_6": 3.99,
                    "credito_parcelado_7_12": 4.49
                },
                "farmacia": {
                    "debito": 0.79,
                    "credito_vista": 2.29,
                    "credito_parcelado_2_6": 3.29,
                    "credito_parcelado_7_12": 3.79
                },
                "posto_combustivel": {
                    "debito": 0.89,
                    "credito_vista": 2.19
                },
                "vestuario": {
                    "debito": 1.29,
                    "credito_vista": 2.79,
                    "credito_parcelado_2_6": 3.79,
                    "credito_parcelado_7_12": 4.29
                }
            }

            if segmento in tabela_mdr:
                if modalidade in tabela_mdr[segmento]:
                    mdr = tabela_mdr[segmento][modalidade]
                    return f"MDR para {segmento.upper()} - {modalidade.replace('_', ' ').title()}: {mdr}%\n\nObservação: Taxas válidas para volume mensal > R$ 50.000. Para volumes menores, acrescentar 0,5%."
                else:
                    modalidades_disponiveis = ', '.join(tabela_mdr[segmento].keys())
                    return f"Modalidade '{modalidade}' não disponível para {segmento}. Modalidades disponíveis: {modalidades_disponiveis}"
            else:
                segmentos_disponiveis = ', '.join(tabela_mdr.keys())
                return f"Segmento '{segmento}' não encontrado. Segmentos disponíveis: {segmentos_disponiveis}"

        except Exception as e:
            return f"Erro ao calcular MDR: {str(e)}"

    return Tool(
        name="calcular_mdr",
        description="Calcula MDR (taxa) para um segmento e modalidade. Input: 'segmento,modalidade' (exemplos: 'restaurante,credito_vista' ou 'farmacia,debito')",
        func=calcular_mdr
    )

def criar_tool_simular_antecipacao():
    """
    Ferramenta para simular antecipação de recebíveis.
    """
    def simular_antecipacao(parametros: str) -> str:
        """Simula antecipação de recebíveis. Input no formato 'valor,dias' (exemplo: '10000,14')"""
        try:
            # Parse dos parâmetros
            parts = parametros.split(',')
            if len(parts) != 2:
                return "Erro: forneça os parâmetros no formato 'valor,dias' (exemplo: '10000,14')"

            valor = float(parts[0].strip())
            dias = int(parts[1].strip())

            # Taxa padrão de antecipação: 2.49% a.m. = 0.083% ao dia
            taxa_mensal = 2.49
            taxa_diaria = taxa_mensal / 30

            # Cálculo do custo
            custo_percentual = taxa_diaria * dias
            custo_reais = valor * (custo_percentual / 100)
            valor_liquido = valor - custo_reais

            resultado = f"""SIMULAÇÃO DE ANTECIPAÇÃO DE RECEBÍVEIS

Valor Original: R$ {valor:,.2f}
Dias Antecipados: {dias} dias
Taxa Diária: {taxa_diaria:.3f}%
Taxa Total: {custo_percentual:.2f}%

Custo da Antecipação: R$ {custo_reais:,.2f}
Valor Líquido a Receber: R$ {valor_liquido:,.2f}

Prazo de Processamento: 1 dia útil
Disponibilidade: Segunda a sexta, até 16h

Observação: Taxa referencial 2.49% a.m. Taxas podem variar conforme volume e relacionamento."""

            return resultado

        except ValueError:
            return "Erro: forneça valores numéricos válidos (exemplo: '10000,14')"
        except Exception as e:
            return f"Erro ao simular antecipação: {str(e)}"

    return Tool(
        name="simular_antecipacao",
        description="Simula antecipação de recebíveis. Input: 'valor,dias' (exemplo: '10000,14' para antecipar R$ 10.000 por 14 dias)",
        func=simular_antecipacao
    )

def criar_tool_abrir_chamado():
    """
    Ferramenta para abrir chamado técnico (simula sistema de suporte).
    """
    def abrir_chamado(parametros: str) -> str:
        """Abre chamado técnico. Input no formato 'tipo,descricao' (exemplo: 'terminal_pos,terminal nao liga')"""
        try:
            # Parse dos parâmetros
            parts = parametros.split(',', 1)
            if len(parts) != 2:
                return "Erro: forneça os parâmetros no formato 'tipo,descricao' (exemplo: 'terminal_pos,terminal nao liga')"

            tipo = parts[0].strip()
            descricao = parts[1].strip()

            # Gerar ID do chamado
            chamado_id = f"CH{datetime.now().strftime('%Y%m%d%H%M%S')}"

            # Definir SLA baseado no tipo
            sla_map = {
                "terminal_pos": "4 horas (P1 - Crítico)",
                "liquidacao": "4 horas (P1 - Crítico)",
                "chargeback": "1 dia útil (P2 - Alto)",
                "credenciamento": "1 dia útil (P2 - Alto)",
                "mdr": "2 dias úteis (P3 - Médio)",
                "geral": "2 dias úteis (P3 - Médio)"
            }

            sla = sla_map.get(tipo.lower(), sla_map["geral"])

            resultado = f"""CHAMADO TÉCNICO ABERTO COM SUCESSO

Número do Chamado: {chamado_id}
Tipo: {tipo.upper()}
Descrição: {descricao}
Data/Hora Abertura: {datetime.now().strftime('%d/%m/%Y %H:%M:%S')}
Status: ABERTO
Prioridade: Conforme tipo
SLA de Resposta: {sla}

Canais de acompanhamento:
- Portal: https://suporte.adquirencia.com/chamado/{chamado_id}
- WhatsApp: (11) 98765-4321
- Email: suporte@adquirencia.com
- Telefone: 0800-777-8899

Você receberá notificações por email e SMS sobre atualizações do chamado.
"""

            return resultado

        except Exception as e:
            return f"Erro ao abrir chamado: {str(e)}"

    return Tool(
        name="abrir_chamado",
        description="Abre chamado técnico para suporte. Input: 'tipo,descricao'. Tipos: terminal_pos, liquidacao, chargeback, credenciamento, mdr, geral. Exemplo: 'terminal_pos,maquininha nao liga'",
        func=abrir_chamado
    )

def criar_base_conhecimento():
    """
    Cria base de conhecimento de adquirência (manuais, políticas, tabelas).
    """
    documentos = [
        Document(
            page_content="""
            Manual Terminal POS PAX D195 - Troubleshooting

            PROBLEMA: Terminal não liga
            Soluções:
            1. Verificar se bateria está carregada (conectar na tomada por 2 horas)
            2. Pressionar botão POWER por 5 segundos
            3. Se não ligar, verificar carregador (LED verde deve acender)
            4. Caso persista, abrir chamado técnico para troca

            PROBLEMA: Transação não autorizada (código 05)
            Causas:
            - Cartão bloqueado ou limite insuficiente
            - Orientação: cliente deve contatar banco emissor

            PROBLEMA: Erro de comunicação
            Soluções:
            1. Verificar conexão WiFi ou chip de dados
            2. Reiniciar terminal
            3. Verificar sinal (mínimo 2 barras necessárias)
            """,
            metadata={"source": "manual_pax_d195.pdf", "category": "terminais_pos"}
        ),
        Document(
            page_content="""
            Política de Chargebacks

            CÓDIGO 4863: Portador não reconhece compra
            Documentação para contestação:
            - Comprovante de entrega assinado
            - Nota fiscal
            - Prazo: 7 dias corridos

            CÓDIGO 4855: Produto não recebido
            Documentação:
            - Rastreamento de entrega
            - Comprovante de recebimento

            Taxa por chargeback: R$ 25,00
            Limite aceitável: até 1% do volume
            """,
            metadata={"source": "politica_chargebacks.pdf", "category": "operacoes"}
        ),
        Document(
            page_content="""
            Tabelas Comerciais - MDR e Prazos

            LIQUIDAÇÃO:
            - Débito: D+1 (1 dia útil)
            - Crédito à vista: D+30 (30 dias corridos)
            - Crédito parcelado: D+30 primeira parcela, demais a cada 30 dias

            ANTECIPAÇÃO:
            - Taxa: 2.49% ao mês (0.083% ao dia)
            - Processamento: 1 dia útil
            - Disponível: Segunda a sexta até 16h
            """,
            metadata={"source": "tabelas_comerciais.pdf", "category": "comercial"}
        )
    ]

    return documentos

def demo_chat_rag_com_tools():
    """
    Demonstra assistente de adquirência com RAG + Tools especializadas.
    """
    logger = get_logger("chat_rag_tools_adquirencia")

    # Configurações
    provider = os.getenv("LLM_PROVIDER", "ollama")
    model_name = os.getenv("MODEL_NAME", "llama3:latest")
    vector_provider = os.getenv("VECTOR_PROVIDER", "chroma")

    logger.info(f"Iniciando RAG+Tools Adquirência com LLM: {provider}/{model_name}")

    try:
        print("🛠️ Configurando ferramentas de adquirência...")

        # 1. Criar ferramentas especializadas em adquirência
        tools = [
            criar_tool_consultar_transacoes(),
            criar_tool_calcular_mdr(),
            criar_tool_simular_antecipacao(),
            criar_tool_abrir_chamado()
        ]

        print(f"✅ {len(tools)} ferramentas de adquirência configuradas")
        print("🔧 Ferramentas disponíveis:")
        for tool in tools:
            print(f"   - {tool.name}: {tool.description[:80]}...")
        print()

        # 2. Criar base de conhecimento
        print("📚 Criando base de conhecimento de adquirência...")
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
            collection_name="rag_tools_adquirencia"
        )
        print("✅ Base de conhecimento de adquirência indexada")

        # 5. Configurar LLM
        llm = get_llm(provider_name=provider)

        # 6. Criar retriever como ferramenta
        retriever = vector_store.as_retriever(search_kwargs={"k": 2})

        def consultar_documentos(pergunta: str) -> str:
            """Consulta documentos internos de adquirência (manuais POS, políticas de chargeback, tabelas comerciais)."""
            docs = retriever.invoke(pergunta)
            if docs:
                contexto = "\n\n".join([doc.page_content for doc in docs])
                fontes = [doc.metadata.get('source', 'sem fonte') for doc in docs]
                return f"Informações encontradas:\n{contexto}\n\nFontes: {', '.join(set(fontes))}"
            return "Nenhuma informação encontrada nos documentos internos de adquirência."

        # Adicionar retriever como ferramenta
        retriever_tool = Tool(
            name="consultar_documentos",
            description="Consulta documentos de adquirência: manuais de terminais POS, políticas de chargeback, tabelas de MDR e prazos de liquidação.",
            func=consultar_documentos
        )
        tools.append(retriever_tool)

        # 7. Criar prompt personalizado para adquirência
        prompt_template = """Você é um assistente especializado em ADQUIRÊNCIA (processamento de pagamentos).

Ferramentas disponíveis:
{tools}

Use este formato EXATAMENTE:

Question: [pergunta do usuário]
Thought: [seu raciocínio sobre qual ferramenta usar]
Action: [nome da ferramenta, uma de: {tool_names}]
Action Input: [entrada sem aspas]
Observation: [resultado]
... (repita Thought/Action/Observation quantas vezes necessário)
Thought: Agora sei a resposta
Final Answer: [resposta completa em português]

REGRAS IMPORTANTES:
1. Action Input deve ser SEM aspas (exemplo: farmacia,credito_vista e NÃO 'farmacia,credito_vista')
2. Use EXATAMENTE o segmento mencionado (farmacia = farmacia, restaurante = restaurante)
3. Depois de ter todas as informações, dê Final Answer
4. Responda em português brasileiro

EXEMPLOS DE USO CORRETO:

Exemplo 1:
Question: Qual MDR para farmacia?
Thought: Preciso calcular MDR para farmacia
Action: calcular_mdr
Action Input: farmacia,credito_vista
Observation: MDR para FARMACIA - Credito Vista: 2.29%
Thought: Agora sei a resposta
Final Answer: O MDR para farmácia no crédito à vista é 2.29%.

Exemplo 2:
Question: Simular antecipação de 10000 por 14 dias
Thought: Preciso simular antecipação
Action: simular_antecipacao
Action Input: 10000,14
Observation: [resultado da simulação]
Thought: Agora sei a resposta
Final Answer: Você receberá R$ 9.883,80 após descontos.

Comece!

Question: {input}
Thought:{agent_scratchpad}"""

        prompt = ChatPromptTemplate.from_template(prompt_template)

        # 8. Criar agente ReAct com melhor handling de erros
        agent = create_react_agent(llm, tools, prompt)

        def _handle_error(error) -> str:
            return f"Erro ao processar: {str(error)}. Tente novamente com formato correto ou passe para Final Answer com o que você já sabe."

        agent_executor = AgentExecutor(
            agent=agent,
            tools=tools,
            verbose=True,
            handle_parsing_errors=_handle_error,
            max_iterations=8,
            max_execution_time=45,
            early_stopping_method="generate",
            return_intermediate_steps=True
        )

        # 9. Perguntas que combinam RAG + Tools
        perguntas = [
            "Cadê o dinheiro da venda de ontem? Sou o merchant 12345 e fiz uma venda de R$ 5.800",
            "Qual MDR para farmácia no crédito à vista e quanto custaria antecipar R$ 10.000 por 14 dias?",
            "Minha maquininha não liga, o que faço? Preciso abrir chamado?",
            "Recebi chargeback código 4863, como contestar e qual documentação preciso?",
            "Quero antecipar R$ 15.000 por 20 dias, quanto vou receber?"
        ]

        print("\n" + "="*80)
        print("🤖 ASSISTENTE DE ADQUIRÊNCIA COM RAG + FERRAMENTAS")
        print("="*80)
        print("Combina: Documentação (RAG) + APIs (Transações, MDR, Antecipação, Chamados)")
        print("="*80)

        for i, pergunta in enumerate(perguntas, 1):
            print(f"\n{'='*70}")
            print(f"PERGUNTA {i}: {pergunta}")
            print('='*70)

            # Executar agente
            try:
                response = agent_executor.invoke({"input": pergunta})

                if 'output' in response:
                    print(f"\n💳 RESPOSTA FINAL:\n{response['output']}")
                else:
                    print(f"\n⚠️ Resposta processada sem formato esperado.")
                    # Fallback para resposta direta
                    print("Tentando resposta direta...")
                    direct_response = llm.invoke([HumanMessage(content=pergunta)])
                    print(f"💳 RESPOSTA DIRETA:\n{direct_response.content}")

            except Exception as agent_error:
                print(f"\n⚠️ Erro no agente: {str(agent_error)}")
                print("Tentando resposta direta sem ferramentas...")

                try:
                    # Fallback: resposta direta do LLM
                    direct_response = llm.invoke([
                        SystemMessage(content="Você é um assistente de adquirência. Responda de forma concisa."),
                        HumanMessage(content=pergunta)
                    ])
                    print(f"💳 RESPOSTA DIRETA:\n{direct_response.content}")
                except Exception as direct_error:
                    print(f"❌ Erro na resposta direta: {str(direct_error)}")

            print()
            logger.info(f"Pergunta {i} processada")

        print("\n✅ Demo RAG + Tools Adquirência concluída com sucesso!")
        print("\n💡 DEMONSTRAÇÃO:")
        print("   O assistente combinou:")
        print("   ✅ Consulta de documentos (manuais POS, políticas)")
        print("   ✅ API de transações (consultar vendas e liquidação)")
        print("   ✅ Calculadora de MDR (taxas por segmento)")
        print("   ✅ Simulador de antecipação (custo e valor líquido)")
        print("   ✅ Sistema de chamados (abertura de tickets técnicos)")

        logger.info("Demo RAG + Tools Adquirência finalizada com sucesso")

    except Exception as e:
        error_msg = f"Erro durante execução do RAG + Tools Adquirência: {str(e)}"
        logger.error(error_msg)
        print(f"❌ {error_msg}")
        return False

    return True

def demonstrar_evolucao():
    """
    Mostra a evolução dos cenários no contexto de adquirência.
    """
    print("""
🚀 EVOLUÇÃO DOS CENÁRIOS - ADQUIRÊNCIA

CENÁRIO 1 (Chat Básico):
💬 Conversa simples sobre adquirência
❌ Conhecimento limitado ao treinamento do modelo
❌ Não acessa dados reais de transações
❌ Não executa ações

CENÁRIO 2 (RAG):
📚 + Acesso a documentos de adquirência
✅ Consulta manuais POS, tabelas MDR, políticas de chargeback
✅ Respostas baseadas em documentação oficial
❌ Ainda não consulta transações reais
❌ Não executa ações (abrir chamado, calcular antecipação)

CENÁRIO 3 (RAG + Tools):
🛠️ + Ferramentas de adquirência
✅ Consulta documentos E executa ações
✅ Acessa API de transações (consulta vendas e liquidação)
✅ Calcula MDR por segmento
✅ Simula antecipação de recebíveis
✅ Abre chamados técnicos
✅ Assistente verdadeiramente útil e operacional

EXEMPLOS PRÁTICOS:

"Cadê o dinheiro da venda de ontem?"
- Cenário 1: Resposta genérica sobre prazos
- Cenário 2: Explica prazos D+1 e D+30 (baseado em docs)
- Cenário 3: CONSULTA transações reais do merchant + explica prazo específico

"Qual MDR para farmácia e quanto custa antecipar R$ 10.000?"
- Cenário 1: Resposta genérica
- Cenário 2: Informa MDR de farmácia (tabela) mas não calcula antecipação
- Cenário 3: CALCULA MDR + SIMULA antecipação com valores exatos
""")

def configurar_ambiente():
    """
    Instruções de configuração.
    """
    print("""
📋 CONFIGURAÇÃO DO AMBIENTE - RAG + TOOLS ADQUIRÊNCIA
======================================================

Variáveis obrigatórias:
export LLM_PROVIDER=ollama
export MODEL_NAME=llama3:latest
export VECTOR_PROVIDER=chroma

Dependências:
pip install langchain-community
pip install langchain-chroma
pip install chromadb

CONTEXTO - ADQUIRÊNCIA:
Este demo combina:

1. RAG (Retrieval Augmented Generation):
   - Manuais de terminais POS (troubleshooting, códigos de erro)
   - Políticas de chargeback e contestação
   - Tabelas comerciais (MDR, prazos de liquidação)

2. TOOLS (Ferramentas especializadas):
   - consultar_transacoes: API de transações (NSU, valores, liquidação)
   - calcular_mdr: Calculadora de taxas por segmento
   - simular_antecipacao: Simulador de antecipação de recebíveis
   - abrir_chamado: Sistema de chamados técnicos

MERCHANT IDs DISPONÍVEIS PARA TESTE:
- 12345: Merchant com 3 transações (débito, crédito, parcelado)
- 67890: Merchant com 1 transação grande
""")

if __name__ == "__main__":
    configurar_ambiente()
    demonstrar_evolucao()

    print("\n🚀 Executando demo RAG + Tools Adquirência automaticamente...")
    demo_chat_rag_com_tools()
