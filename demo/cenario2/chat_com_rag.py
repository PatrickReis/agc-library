"""
Cenário 2: Chat com Base Vetorial (RAG - Retrieval Augmented Generation)
Demonstra chat inteligente que consulta documentos próprios da empresa.
"""

from agentCore import get_llm, get_embeddings, get_logger
from langchain_core.messages import HumanMessage, SystemMessage
from langchain_core.documents import Document
from langchain.chains import RetrievalQA
from langchain.prompts import ChatPromptTemplate
from langchain_text_splitters import RecursiveCharacterTextSplitter
from langchain_chroma import Chroma
import os
from dotenv import load_dotenv

load_dotenv()

def criar_base_conhecimento():
    """
    Cria uma base de conhecimento exemplo com documentos da empresa.
    """
    documentos = [
        Document(
            page_content="""
            Política de Recursos Humanos - Benefícios

            Nossa empresa oferece os seguintes benefícios:
            - Vale refeição: R$ 30,00 por dia útil
            - Vale alimentação: R$ 400,00 mensais
            - Plano de saúde: cobertura nacional com coparticipação
            - Plano odontológico: 100% custeado pela empresa
            - Seguro de vida: 2x o salário anual
            - Auxílio creche: até R$ 600,00 para filhos até 5 anos
            - Gympass: acesso a academias e apps de bem-estar
            """,
            metadata={"source": "rh_beneficios.pdf", "category": "recursos_humanos"}
        ),
        Document(
            page_content="""
            Política de Home Office

            O trabalho remoto é permitido seguindo estas diretrizes:
            - Máximo 3 dias por semana em home office
            - Presença obrigatória nas segundas e sextas-feiras
            - Reuniões importantes presenciais devem ter prioridade
            - Equipamentos fornecidos: notebook, monitor adicional, cadeira ergonômica
            - Internet: auxílio de R$ 100,00 mensais para banda larga
            - Horário flexível: entrada entre 8h e 10h
            """,
            metadata={"source": "politica_home_office.pdf", "category": "recursos_humanos"}
        ),
        Document(
            page_content="""
            Produtos e Serviços - Catálogo 2024

            Oferecemos as seguintes soluções tecnológicas:
            - Desenvolvimento de software customizado
            - Consultoria em transformação digital
            - Implementação de sistemas ERP
            - Soluções de inteligência artificial
            - Análise de dados e Business Intelligence
            - Segurança cibernética e compliance
            - Cloud computing e migração AWS/Azure
            """,
            metadata={"source": "catalogo_produtos.pdf", "category": "comercial"}
        ),
        Document(
            page_content="""
            Processo de Vendas

            Nosso processo comercial segue estas etapas:
            1. Qualificação do lead (1-2 dias)
            2. Reunião de descoberta com cliente (1 semana)
            3. Elaboração de proposta técnica (1-2 semanas)
            4. Apresentação comercial (1 semana)
            5. Negociação e fechamento (1-2 semanas)
            6. Kick-off do projeto (1 semana)

            Prazo médio total: 6-8 semanas da prospecção ao início do projeto.
            """,
            metadata={"source": "processo_vendas.pdf", "category": "comercial"}
        ),
        Document(
            page_content="""
            Suporte Técnico - SLA

            Níveis de suporte oferecidos:
            - Crítico (P1): Resposta em 1 hora, resolução em 4 horas
            - Alto (P2): Resposta em 4 horas, resolução em 1 dia útil
            - Médio (P3): Resposta em 1 dia útil, resolução em 3 dias úteis
            - Baixo (P4): Resposta em 2 dias úteis, resolução em 1 semana

            Canais de atendimento:
            - Email: suporte@empresa.com
            - Telefone: (11) 1234-5678
            - Chat: disponível 24/7 no portal do cliente
            """,
            metadata={"source": "sla_suporte.pdf", "category": "tecnico"}
        )
    ]

    return documentos

def demo_chat_com_rag():
    """
    Demonstra chat inteligente que consulta base de conhecimento interna.
    """
    logger = get_logger("chat_rag")

    # Configurações
    provider = os.getenv("LLM_PROVIDER", "ollama")
    model_name = os.getenv("MODEL_NAME", "llama3:latest")
    vector_provider = os.getenv("VECTOR_PROVIDER", "chroma")

    logger.info(f"Iniciando RAG com LLM: {provider}/{model_name}, Vector Store: {vector_provider}")

    try:
        # 1. Criar base de conhecimento
        print("📚 Criando base de conhecimento...")
        documentos = criar_base_conhecimento()

        # 2. Configurar chunking strategy
        text_splitter = RecursiveCharacterTextSplitter(
            chunk_size=500,
            chunk_overlap=50,
            length_function=len,
        )

        # 3. Processar documentos
        chunks = text_splitter.split_documents(documentos)

        print(f"✅ {len(chunks)} chunks criados dos documentos")

        # 4. Configurar embeddings e vector store
        embeddings = get_embeddings(provider_name=provider)

        # 5. Criar vector store usando Chroma diretamente
        print("🔍 Indexando documentos...")
        texts = [chunk.page_content for chunk in chunks]
        metadatas = [chunk.metadata for chunk in chunks]

        vector_store = Chroma.from_texts(
            texts=texts,
            embedding=embeddings,
            metadatas=metadatas,
            collection_name="knowledge_base_demo"
        )
        print("✅ Documentos indexados com sucesso")

        # 6. Configurar LLM
        llm = get_llm(provider_name=provider)

        # 7. Criar retriever
        retriever = vector_store.as_retriever(
            search_kwargs={"k": 3}  # Buscar top 3 documentos mais relevantes
        )

        # 8. Template de prompt otimizado para RAG
        prompt_template = ChatPromptTemplate.from_messages([
            ("system", """Você é um assistente especializado em responder dúvidas sobre nossa empresa.
            Use APENAS as informações fornecidas no contexto abaixo para responder.
            Se a informação não estiver disponível no contexto, diga claramente que não possui essa informação.

            Contexto:
            {context}"""),
            ("human", "{question}")
        ])

        # 9. Perguntas de exemplo
        perguntas = [
            "Quais são os benefícios oferecidos pela empresa?",
            "Como funciona a política de home office?",
            "Qual é o prazo médio do processo de vendas?",
            "Quais são os níveis de SLA do suporte técnico?",
            "A empresa oferece auxílio para internet em home office?"
        ]

        print("\n" + "="*80)
        print("🤖 ASSISTENTE EMPRESARIAL COM RAG")
        print("="*80)

        for i, pergunta in enumerate(perguntas, 1):
            print(f"\n{'='*60}")
            print(f"PERGUNTA {i}: {pergunta}")
            print('='*60)

            # Recuperar documentos relevantes
            docs_relevantes = retriever.get_relevant_documents(pergunta)

            # Preparar contexto
            contexto = "\n\n".join([doc.page_content for doc in docs_relevantes])

            # Gerar resposta
            messages = prompt_template.format_messages(
                context=contexto,
                question=pergunta
            )

            response = llm.invoke(messages)

            print(f"RESPOSTA: {response.content}")

            # Mostrar fontes consultadas
            fontes = [doc.metadata.get('source', 'Documento sem fonte') for doc in docs_relevantes]
            print(f"\n📋 FONTES CONSULTADAS: {', '.join(set(fontes))}")
            print()

            logger.info(f"Pergunta {i} processada - {len(docs_relevantes)} documentos consultados")

        print("\n✅ Demo RAG concluída com sucesso!")
        print("\n💡 OBSERVAÇÃO: O sistema consultou apenas documentos internos da empresa,")
        print("   garantindo respostas precisas e alinhadas com políticas internas.")

        logger.info("Demo RAG finalizada com sucesso")

    except Exception as e:
        error_msg = f"Erro durante execução do RAG: {str(e)}"
        logger.error(error_msg)
        print(f"❌ {error_msg}")
        return False

    return True

def demonstrar_comparacao():
    """
    Demonstra a diferença entre chat normal e chat com RAG.
    """
    print("""
🔍 COMPARAÇÃO: CHAT NORMAL vs CHAT COM RAG

CHAT NORMAL (Cenário 1):
❌ Respostas genéricas sobre recursos humanos
❌ Informações podem estar desatualizadas
❌ Não conhece políticas específicas da empresa
❌ Pode "alucinar" informações incorretas

CHAT COM RAG (Cenário 2):
✅ Respostas baseadas em documentos reais da empresa
✅ Informações sempre atualizadas conforme documentação
✅ Conhece políticas, processos e procedimentos específicos
✅ Cita fontes das informações
✅ Admite quando não possui informação
""")

def configurar_ambiente():
    """
    Instruções para configuração do ambiente.
    """
    print("""
📋 CONFIGURAÇÃO DO AMBIENTE - RAG
==================================

Variáveis de ambiente necessárias:

1. LLM Provider:
   export LLM_PROVIDER=ollama
   export MODEL_NAME=llama3:latest

2. Vector Store (escolha uma):
   # ChromaDB (local, sem configuração adicional)
   export VECTOR_PROVIDER=chroma

   # AWS (requer credenciais)
   export VECTOR_PROVIDER=aws
   export AWS_ACCESS_KEY_ID=sua_chave
   export AWS_SECRET_ACCESS_KEY=sua_chave_secreta
   export AWS_REGION=us-east-1

3. Dependências:
   pip install chromadb  # Para ChromaDB local
   pip install langchain-chroma
""")

if __name__ == "__main__":
    configurar_ambiente()
    demonstrar_comparacao()

    resposta = input("\nDeseja executar o demo RAG? (s/n): ")
    if resposta.lower() in ['s', 'sim', 'y', 'yes']:
        demo_chat_com_rag()
    else:
        print("Demo cancelado.")