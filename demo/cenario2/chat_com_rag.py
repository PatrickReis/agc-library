"""
Cenário 2: Chat com Base Vetorial (RAG - Retrieval Augmented Generation)
Demonstra assistente de adquirência que consulta documentos técnicos e comerciais.

CONTEXTO: Adquirência - Processamento de pagamentos, terminais POS, MDR, liquidação, chargebacks
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
    Cria base de conhecimento especializada em adquirência:
    - Manuais de terminais POS
    - Políticas de chargeback
    - Tabelas comerciais (MDR)
    - Requisitos de credenciamento
    - Prazos de liquidação
    """
    documentos = [
        Document(
            page_content="""
            Manual Terminal POS PAX D195 - Códigos de Erro e Troubleshooting

            ERRO 'NÃO AUTORIZADO, CONTATE EMISSOR' (Código 05):
            Causas mais comuns:
            - Cartão bloqueado ou cancelado pelo banco emissor
            - Limite de crédito insuficiente
            - Suspeita de fraude detectada pelo banco emissor
            - Cartão vencido ou fora da validade
            - Restrição cadastral do portador

            Orientação ao merchant:
            1. Solicitar que o portador entre em contato com o banco emissor
            2. Oferecer forma alternativa de pagamento
            3. Não insistir na transação (pode gerar bloqueio temporário do terminal)

            ERRO 'SENHA INVÁLIDA' (Código 55):
            - Portador digitou senha incorreta
            - Limite de tentativas: 3 vezes
            - Após 3 tentativas incorretas, cartão é bloqueado automaticamente

            ERRO 'TERMINAL NÃO CADASTRADO' (Código 03):
            - Terminal não ativo na rede adquirente
            - Problema de comunicação com servidor
            - Contatar suporte técnico: 0800-777-8899

            ERRO 'TRANSAÇÃO NÃO PERMITIDA' (Código 57):
            - Modalidade de pagamento não habilitada no terminal
            - Exemplo: débito desabilitado, mas cliente tentou usar
            - Verificar configurações comerciais do estabelecimento
            """,
            metadata={"source": "manual_pax_d195.pdf", "category": "terminais_pos"}
        ),
        Document(
            page_content="""
            Tabela de MDR (Merchant Discount Rate) por Segmento - 2024

            SUPERMERCADO (MCC 5411):
            - Débito à vista: 0,99%
            - Crédito à vista: 2,49%
            - Crédito parcelado lojista (2-6x): 3,49%
            - Crédito parcelado lojista (7-12x): 3,99%

            RESTAURANTE (MCC 5812):
            - Débito à vista: 1,49%
            - Crédito à vista: 2,99%
            - Crédito parcelado lojista (2-6x): 3,99%
            - Crédito parcelado lojista (7-12x): 4,49%

            FARMÁCIA (MCC 5912):
            - Débito à vista: 0,79%
            - Crédito à vista: 2,29%
            - Crédito parcelado lojista (2-6x): 3,29%
            - Crédito parcelado lojista (7-12x): 3,79%

            POSTOS DE COMBUSTÍVEL (MCC 5541):
            - Débito à vista: 0,89%
            - Crédito à vista: 2,19%
            - Crédito parcelado não disponível

            VESTUÁRIO (MCC 5651):
            - Débito à vista: 1,29%
            - Crédito à vista: 2,79%
            - Crédito parcelado lojista (2-6x): 3,79%
            - Crédito parcelado lojista (7-12x): 4,29%

            Observações:
            - Taxas válidas para volume mensal > R$ 50.000
            - Volume < R$ 50.000: acrescentar 0,5% em todas as modalidades
            - Consulte taxas especiais para alto volume (> R$ 500.000/mês)
            """,
            metadata={"source": "tabela_mdr_2024.pdf", "category": "comercial"}
        ),
        Document(
            page_content="""
            Política de Chargebacks e Contestações

            DEFINIÇÃO:
            Chargeback é o estorno de uma transação solicitado pelo portador do cartão ao banco emissor.

            PRAZOS:
            - Prazo para portador contestar: até 120 dias após a compra
            - Prazo para merchant contestar chargeback: 7 dias corridos após notificação
            - Prazo análise pela bandeira: 15-30 dias úteis
            - Prazo segunda contestação (pré-arbitragem): 10 dias corridos

            DOCUMENTAÇÃO NECESSÁRIA PARA CONTESTAÇÃO:
            - Comprovante de entrega assinado (com data e CPF do recebedor)
            - Nota fiscal eletrônica com chave de acesso
            - Comprovante de autorização da transação (NSU + código de autorização)
            - Comunicações com cliente (emails, chat, WhatsApp)
            - Política de cancelamento/troca assinada pelo cliente
            - Fotos do produto/serviço entregue (quando aplicável)

            MOTIVOS COMUNS DE CHARGEBACK:

            Código 4863: Portador não reconhece a compra (suspeita de fraude)
            - Taxa de sucesso na contestação: 30%
            - Documentos críticos: comprovante de entrega assinado + nota fiscal

            Código 4855: Produto/serviço não recebido
            - Taxa de sucesso na contestação: 60%
            - Documentos críticos: rastreamento de entrega + assinatura do recebedor

            Código 4837: Transação duplicada
            - Taxa de sucesso na contestação: 80%
            - Documentos críticos: demonstrar que são transações distintas (NSU diferente)

            Código 4853: Produto defeituoso ou não conforme descrito
            - Taxa de sucesso na contestação: 40%
            - Documentos críticos: descrição detalhada do produto + fotos + termos aceitos

            TAXAS:
            - Taxa operacional por chargeback: R$ 25,00 (descontada na liquidação)
            - Taxa adicional se chargeback for perdido: 100% do valor da transação

            LIMITES DE CHARGEBACK:
            - Taxa aceitável: até 1% do volume transacionado
            - Taxa de alerta: 1% a 1,5% (monitoramento intensivo)
            - Taxa crítica: acima de 1,5% (risco de descredenciamento)
            """,
            metadata={"source": "politica_chargebacks.pdf", "category": "operacoes"}
        ),
        Document(
            page_content="""
            Requisitos de Credenciamento por Tipo de Empresa

            MEI (MICROEMPREENDEDOR INDIVIDUAL):
            Documentação obrigatória:
            - CCMEI (Certificado de Microempreendedor Individual)
            - RG e CPF do titular
            - Comprovante de endereço comercial (conta de luz, água ou telefone)
            - Selfie segurando RG

            Limite transacional:
            - Volume máximo: R$ 30.000/mês
            - Ticket médio máximo: R$ 1.000
            - Prazo de liquidação: D+2 (dois dias úteis)

            Taxa de aprovação média: 95%
            Prazo de análise: 1-2 dias úteis

            ME (MICROEMPRESA) e EPP (EMPRESA DE PEQUENO PORTE):
            Documentação obrigatória:
            - Contrato social ou última alteração contratual
            - CNPJ ativo (cartão do CNPJ)
            - RG e CPF dos sócios
            - Comprovante de endereço comercial
            - Faturamento dos últimos 3 meses (opcional, mas recomendado)

            Limite transacional:
            - Volume máximo inicial: R$ 100.000/mês (pode ser ampliado após 90 dias)
            - Ticket médio máximo: R$ 5.000
            - Prazo de liquidação: D+1 ou D+30 (conforme plano escolhido)

            Taxa de aprovação média: 85%
            Prazo de análise: 2-3 dias úteis

            LTDA (SOCIEDADE LIMITADA):
            Documentação obrigatória:
            - Contrato social completo e consolidado
            - CNPJ ativo
            - RG e CPF de todos os sócios
            - Comprovante de endereço comercial
            - Faturamento dos últimos 6 meses
            - Certidões negativas (Federal, Estadual, Municipal)
            - Referências bancárias

            Limite transacional:
            - Volume inicial: até R$ 500.000/mês
            - Sem limite de ticket médio (análise individual)
            - Prazo de liquidação: D+1 ou D+30

            Taxa de aprovação média: 75%
            Prazo de análise: 3-5 dias úteis

            SEGMENTOS DE ALTO RISCO (análise reforçada):
            - Apostas esportivas
            - Cigarro eletrônico / Vape
            - Criptomoedas
            - Cursos online / Infoprodutos
            - Suplementos alimentares

            Requisitos adicionais:
            - Reserve account (garantia de 20-30% do volume)
            - Limite transacional reduzido inicialmente
            - Monitoramento de chargeback intensivo
            - KYC reforçado (videoconferência com sócios)
            """,
            metadata={"source": "requisitos_credenciamento.pdf", "category": "comercial"}
        ),
        Document(
            page_content="""
            Prazos de Liquidação e Antecipação de Recebíveis

            PRAZOS PADRÃO DE LIQUIDAÇÃO:

            Débito à vista:
            - Prazo: D+1 (um dia útil após a venda)
            - Exemplo: venda na segunda-feira, dinheiro na terça-feira
            - Horário de corte: 23h59 (vendas após esse horário caem no dia seguinte)

            Crédito à vista:
            - Prazo padrão: D+30 (30 dias corridos após a venda)
            - Exemplo: venda em 10/01, liquidação em 09/02
            - Alternativa com taxa: D+1 (mediante desconto de antecipação)

            Crédito parcelado lojista:
            - Prazo: primeira parcela em D+30, demais a cada 30 dias
            - Exemplo venda parcelada em 3x de R$ 300:
              - 10/01: venda realizada
              - 09/02: recebe R$ 300 (1ª parcela)
              - 09/03: recebe R$ 300 (2ª parcela)
              - 09/04: recebe R$ 300 (3ª parcela)

            ANTECIPAÇÃO DE RECEBÍVEIS:

            Antecipação automática (plano D+1):
            - Todas as vendas crédito liquidadas em D+1
            - Taxa: incluída no MDR (acréscimo de ~0,5% na taxa)
            - Ideal para: fluxo de caixa previsível

            Antecipação sob demanda:
            - Merchant solicita antecipação quando necessário
            - Taxa: 2,49% ao mês (0,083% ao dia)
            - Cálculo: Valor × (dias antecipados × 0,083%)
            - Exemplo: antecipar R$ 10.000 por 20 dias
              Custo = 10.000 × (20 × 0,00083) = R$ 166,00
              Valor líquido = R$ 9.834,00

            Prazo para processar antecipação: até 1 dia útil
            Disponibilidade: segundas a sextas, até 16h

            AGENDA DE RECEBÍVEIS (consulta via app/portal):
            - Valores a receber nos próximos 365 dias
            - Discriminação por modalidade (débito, crédito, parcelado)
            - Projeção de descontos (MDR, antecipações, chargebacks)
            - Valor líquido estimado por dia
            """,
            metadata={"source": "prazos_liquidacao.pdf", "category": "financeiro"}
        )
    ]

    return documentos

def demo_chat_com_rag():
    """
    Demonstra assistente de adquirência que consulta base de conhecimento especializada.
    """
    logger = get_logger("chat_rag_adquirencia")

    # Configurações
    provider = os.getenv("LLM_PROVIDER", "ollama")
    model_name = os.getenv("MODEL_NAME", "llama3:latest")
    vector_provider = os.getenv("VECTOR_PROVIDER", "chroma")

    logger.info(f"Iniciando RAG Adquirência com LLM: {provider}/{model_name}, Vector Store: {vector_provider}")

    try:
        # 1. Criar base de conhecimento
        print("📚 Criando base de conhecimento de adquirência...")
        documentos = criar_base_conhecimento()

        # 2. Configurar chunking strategy
        text_splitter = RecursiveCharacterTextSplitter(
            chunk_size=800,
            chunk_overlap=100,
            length_function=len,
        )

        # 3. Processar documentos
        chunks = text_splitter.split_documents(documentos)

        print(f"✅ {len(chunks)} chunks criados dos documentos de adquirência")

        # 4. Configurar embeddings e vector store
        embeddings = get_embeddings(provider_name=provider)

        # 5. Criar vector store usando Chroma diretamente
        print("🔍 Indexando documentos (manuais POS, MDR, chargebacks, credenciamento)...")
        texts = [chunk.page_content for chunk in chunks]
        metadatas = [chunk.metadata for chunk in chunks]

        vector_store = Chroma.from_texts(
            texts=texts,
            embedding=embeddings,
            metadatas=metadatas,
            collection_name="adquirencia_knowledge_base"
        )
        print("✅ Base de conhecimento de adquirência indexada com sucesso")

        # 6. Configurar LLM
        llm = get_llm(provider_name=provider)

        # 7. Criar retriever
        retriever = vector_store.as_retriever(
            search_kwargs={"k": 3}  # Buscar top 3 documentos mais relevantes
        )

        # 8. Template de prompt otimizado para adquirência
        prompt_template = ChatPromptTemplate.from_messages([
            ("system", """Você é um assistente especializado em ADQUIRÊNCIA (processamento de pagamentos com cartões).
            Você auxilia merchants (lojistas), vendedores e operadores com dúvidas sobre:
            - Terminais POS e códigos de erro
            - MDR (Merchant Discount Rate) e taxas
            - Liquidação e antecipação de recebíveis
            - Chargebacks e contestações
            - Credenciamento de estabelecimentos
            - Transações com cartões de crédito e débito

            Use APENAS as informações fornecidas no contexto abaixo para responder.
            Se a informação não estiver disponível no contexto, diga claramente que não possui essa informação e sugira contatar o suporte comercial.

            Sempre use terminologia técnica correta de adquirência:
            - Merchant (não "cliente" ou "loja")
            - Terminal POS (não "maquininha" em contexto técnico)
            - MDR (não apenas "taxa")
            - Liquidação (não "pagamento")
            - NSU, código de autorização, bandeira, emissor, adquirente

            Contexto de adquirência:
            {context}"""),
            ("human", "{question}")
        ])

        # 9. Perguntas de teste focadas em adquirência
        perguntas = [
            "Quais são os prazos de liquidação para débito e crédito?",
            "Qual é o MDR para restaurante no crédito à vista?",
            "Minha maquininha dá erro código 05, o que significa?",
            "Recebi um chargeback código 4863, como contestar?",
            "Qual documentação preciso para credenciar um MEI?",
            "Como funciona a antecipação de recebíveis e quanto custa?",
            "Meu cliente quer parcelar em 6x, qual a taxa?"
        ]

        print("\n" + "="*80)
        print("🤖 ASSISTENTE DE ADQUIRÊNCIA COM RAG")
        print("="*80)
        print("Especializado em: Terminais POS | MDR | Liquidação | Chargebacks | Credenciamento")
        print("="*80)

        for i, pergunta in enumerate(perguntas, 1):
            print(f"\n{'='*70}")
            print(f"PERGUNTA {i}: {pergunta}")
            print('='*70)

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

            print(f"\n💳 RESPOSTA:\n{response.content}")

            # Mostrar fontes consultadas
            fontes = [doc.metadata.get('source', 'Documento sem fonte') for doc in docs_relevantes]
            categorias = [doc.metadata.get('category', 'sem categoria') for doc in docs_relevantes]
            print(f"\n📋 FONTES CONSULTADAS:")
            for fonte, categoria in zip(set(fontes), set(categorias)):
                print(f"   - {fonte} (categoria: {categoria})")
            print()

            logger.info(f"Pergunta {i} processada - {len(docs_relevantes)} documentos consultados")

        print("\n✅ Demo RAG Adquirência concluída com sucesso!")
        print("\n💡 OBSERVAÇÃO: O sistema consultou apenas documentos especializados em adquirência:")
        print("   - Manuais de terminais POS (códigos de erro, troubleshooting)")
        print("   - Tabelas comerciais de MDR por segmento")
        print("   - Políticas de chargeback e contestação")
        print("   - Requisitos de credenciamento (MEI, ME, LTDA)")
        print("   - Prazos de liquidação e antecipação")

        logger.info("Demo RAG Adquirência finalizada com sucesso")

    except Exception as e:
        error_msg = f"Erro durante execução do RAG Adquirência: {str(e)}"
        logger.error(error_msg)
        print(f"❌ {error_msg}")
        return False

    return True

def demonstrar_comparacao():
    """
    Demonstra a diferença entre chat normal e chat com RAG em contexto de adquirência.
    """
    print("""
🔍 COMPARAÇÃO: CHAT NORMAL vs CHAT COM RAG (ADQUIRÊNCIA)

CHAT NORMAL (Cenário 1):
❌ Respostas genéricas sobre pagamentos
❌ Informações podem estar desatualizadas
❌ Não conhece taxas específicas (MDR por segmento)
❌ Não conhece códigos de erro dos terminais POS
❌ Pode "alucinar" informações incorretas sobre prazos e políticas

CHAT COM RAG (Cenário 2):
✅ Respostas baseadas em documentos técnicos reais (manuais POS, tabelas MDR)
✅ Informações sempre atualizadas conforme documentação oficial
✅ Conhece políticas de chargeback, prazos de liquidação, requisitos de credenciamento
✅ Cita fontes das informações (manual_pax_d195.pdf, tabela_mdr_2024.pdf)
✅ Admite quando não possui informação e sugere contato com suporte

EXEMPLOS PRÁTICOS:

Pergunta: "Qual MDR para restaurante?"
- Chat normal: Resposta genérica ("geralmente entre 2-5%")
- Chat RAG: "Restaurante MCC 5812: Débito 1,49%, Crédito à vista 2,99%, Parcelado 3,99%-4,49% (fonte: tabela_mdr_2024.pdf)"

Pergunta: "Erro código 05 na maquininha"
- Chat normal: Resposta vaga sobre problemas de comunicação
- Chat RAG: "Erro 05 'Não autorizado, contate emissor' indica: cartão bloqueado, limite insuficiente ou suspeita de fraude. Orientação: solicitar que portador contate banco emissor (fonte: manual_pax_d195.pdf)"
""")

def configurar_ambiente():
    """
    Instruções para configuração do ambiente.
    """
    print("""
📋 CONFIGURAÇÃO DO AMBIENTE - RAG ADQUIRÊNCIA
==============================================

Variáveis de ambiente necessárias:

1. LLM Provider:
   export LLM_PROVIDER=ollama
   export MODEL_NAME=llama3:latest

2. Vector Store (escolha uma):
   # ChromaDB (local, sem configuração adicional - RECOMENDADO)
   export VECTOR_PROVIDER=chroma

   # AWS (requer credenciais)
   export VECTOR_PROVIDER=aws
   export AWS_ACCESS_KEY_ID=sua_chave
   export AWS_SECRET_ACCESS_KEY=sua_chave_secreta
   export AWS_REGION=us-east-1

3. Dependências:
   pip install chromadb  # Para ChromaDB local
   pip install langchain-chroma
   pip install langchain-text-splitters

CONTEXTO:
Este demo utiliza base de conhecimento especializada em ADQUIRÊNCIA, incluindo:
- Manuais de terminais POS (PAX D195, Ingenico, Gertec)
- Tabelas de MDR por segmento (Supermercado, Restaurante, Farmácia, etc.)
- Políticas de chargeback e contestação (códigos 4863, 4855, 4837, 4853)
- Requisitos de credenciamento (MEI, ME, LTDA)
- Prazos de liquidação (D+1, D+30) e antecipação
""")

if __name__ == "__main__":
    configurar_ambiente()
    demonstrar_comparacao()
    demo_chat_com_rag()
