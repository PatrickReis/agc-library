"""
Cenário 1: Chat Simples para Adquirência
Demonstra assistente básico para atendimento a merchants, vendedores e operações.
"""

from agentCore import get_llm, get_logger
from langchain_core.messages import HumanMessage, SystemMessage
import os
from dotenv import load_dotenv

load_dotenv()

def demo_chat_simples():
    """
    Demonstra chat simples focado em casos de uso de adquirência.
    """
    logger = get_logger("chat_simples_adquirencia")

    # Configuração do modelo
    provider = os.getenv("LLM_PROVIDER", "ollama")
    model_name = os.getenv("MODEL_NAME", "llama3.2")

    logger.info(f"Iniciando chat para adquirência - Provider: {provider}, Modelo: {model_name}")

    try:
        # Obtém o modelo LLM
        llm = get_llm(provider_name=provider)

        # Perguntas típicas de adquirência
        perguntas = [
            "Por que minha liquidação ainda não caiu? A venda foi feita há 2 dias no débito.",
            "Qual é minha taxa de MDR para vendas no crédito à vista?",
            "Minha maquininha não está ligando, o que faço?",
            "Recebi um chargeback, o que fazer agora?",
            "Qual documentação preciso para credenciar um MEI como merchant?"
        ]

        # System message especializado em adquirência
        system_message = SystemMessage(
            content="""Você é um assistente especializado em adquirência (processamento de pagamentos com cartão).

            Ajude merchants (estabelecimentos comerciais), vendedores e operadores com dúvidas sobre:
            - Transações e liquidações (D+1 para débito, D+30 para crédito)
            - Terminais POS (maquininhas de cartão)
            - MDR (Merchant Discount Rate - taxa cobrada do lojista)
            - Chargebacks e contestações
            - Credenciamento de novos merchants
            - Antecipação de recebíveis

            Responda de forma clara, objetiva e prática, focando em resolver o problema do usuário.
            Use termos do setor quando apropriado, mas explique se necessário.
            Sempre responda em português brasileiro.
            """
        )

        print("\n" + "="*80)
        print("🏦 ASSISTENTE DE ADQUIRÊNCIA - CHAT SIMPLES")
        print("="*80)
        print("\nContexto: Atendimento a merchants, vendedores e operações")
        print("Casos de uso: Liquidação, MDR, terminais POS, chargebacks, credenciamento\n")

        for i, pergunta in enumerate(perguntas, 1):
            print(f"\n{'='*70}")
            print(f"💬 PERGUNTA {i} (Merchant/Vendedor):")
            print(f"   {pergunta}")
            print('='*70)

            # Prepara as mensagens
            messages = [system_message, HumanMessage(content=pergunta)]

            # Invoca o modelo
            logger.info(f"Processando pergunta {i} sobre adquirência")
            response = llm.invoke(messages)

            # Exibe a resposta
            print(f"\n🤖 RESPOSTA:")
            print(f"   {response.content}\n")

            logger.info(f"Resposta {i} gerada com sucesso")

        print("\n" + "="*70)
        print("✅ Demo de Chat Simples para Adquirência concluída!")
        print("\n💡 OBSERVAÇÕES:")
        print("   - Respostas focadas em contexto de pagamentos")
        print("   - Terminologia específica de adquirência (MDR, liquidação, chargebacks)")
        print("   - Casos de uso realistas do segmento")
        print("="*70 + "\n")

        logger.info("Chat simples de adquirência finalizado com sucesso")

    except Exception as e:
        error_msg = f"Erro durante execução do chat: {str(e)}"
        logger.error(error_msg)
        print(f"\n❌ {error_msg}\n")
        return False

    return True

def demonstrar_contexto():
    """
    Demonstra a diferença entre chat genérico e chat especializado em adquirência.
    """
    print("""
╔═══════════════════════════════════════════════════════════════════════════╗
║                    CONTEXTO: CHAT PARA ADQUIRÊNCIA                        ║
╚═══════════════════════════════════════════════════════════════════════════╝

📊 SEGMENTO: Adquirência (Processamento de Pagamentos com Cartão)

🎯 USUÁRIOS ATENDIDOS:
   • Merchants (Estabelecimentos Comerciais) - Dúvidas sobre vendas e liquidação
   • Força de Vendas - Informações sobre produtos e credenciamento
   • Operações - Processos de conciliação e gestão de riscos

💬 CASOS DE USO COMUNS:

   Para Merchants:
   ├─ "Por que minha liquidação ainda não caiu?"
   ├─ "Qual minha taxa de MDR?"
   ├─ "Minha maquininha está com erro"
   ├─ "Recebi um chargeback"
   └─ "Como antecipar meus recebíveis?"

   Para Vendedores:
   ├─ "Documentação para credenciar MEI"
   ├─ "Tabela de taxas por segmento"
   ├─ "Status de proposta de cliente"
   └─ "Simulação de antecipação"

   Para Operações:
   ├─ "Processo de conciliação"
   ├─ "Gestão de chargebacks"
   ├─ "Compliance PCI-DSS"
   └─ "Split de pagamento"

🔑 TERMINOLOGIA DO SETOR:
   • MDR: Merchant Discount Rate (taxa cobrada do merchant)
   • Terminal POS: Maquininha de cartão
   • Liquidação: Quando o dinheiro cai na conta do merchant
   • Chargeback: Contestação de compra pelo portador do cartão
   • Credenciamento: Processo de cadastro de novo merchant
   • Antecipação: Receber antes do prazo mediante taxa

📅 PRAZOS TÍPICOS:
   • Débito: D+1 (1 dia útil)
   • Crédito à vista: D+30 (30 dias)
   • Crédito parcelado: Conforme parcelas

═══════════════════════════════════════════════════════════════════════════
""")

def configurar_ambiente():
    """
    Fornece instruções para configuração do ambiente.
    """
    print("""
📋 CONFIGURAÇÃO DO AMBIENTE
════════════════════════════════════════════════════════════════════════

Para executar este demo de adquirência, configure:

1. Para Ollama (recomendado para teste local):
   export LLM_PROVIDER=ollama
   export MODEL_NAME=llama3.2

2. Para OpenAI:
   export LLM_PROVIDER=openai
   export MODEL_NAME=gpt-4
   export OPENAI_API_KEY=sua_chave_aqui

3. Para AWS Bedrock:
   export LLM_PROVIDER=aws_bedrock
   export MODEL_NAME=anthropic.claude-3-sonnet-20240229-v1:0
   export AWS_ACCESS_KEY_ID=sua_chave
   export AWS_SECRET_ACCESS_KEY=sua_chave_secreta
   export AWS_REGION=us-east-1

4. Para Google Gemini:
   export LLM_PROVIDER=google
   export MODEL_NAME=gemini-pro
   export GOOGLE_API_KEY=sua_chave_aqui

════════════════════════════════════════════════════════════════════════
""")

if __name__ == "__main__":
    demonstrar_contexto()
    configurar_ambiente()
    demo_chat_simples()
