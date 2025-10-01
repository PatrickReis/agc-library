"""
Cenário 1: Chat Simples com LangChain e LLM
Demonstra a funcionalidade básica de chat usando a biblioteca agentCore.
"""

from agentCore import get_llm, get_logger
from langchain_core.messages import HumanMessage, SystemMessage
import os
from dotenv import load_dotenv

load_dotenv()

def demo_chat_simples():
    """
    Demonstra um chat simples usando diferentes provedores de LLM.
    """
    logger = get_logger("chat_simples")

    # Configuração do modelo (pode ser alterada via variáveis de ambiente)
    provider = os.getenv("LLM_PROVIDER", "ollama")  # ollama, openai, aws_bedrock, google
    model_name = os.getenv("MODEL_NAME", "llama3:latest")

    logger.info(f"Iniciando chat simples com provider: {provider}, modelo: {model_name}")

    try:
        # Obtém o modelo LLM usando a biblioteca agentCore
        llm = get_llm(provider_name=provider)

        # Mensagens de exemplo para demonstração
        perguntas = [
            "Olá! Você pode me explicar o que é inteligência artificial?",
            "Quais são as principais aplicações de IA no mercado hoje?",
            "Como a IA pode ajudar empresas a melhorar sua eficiência?"
        ]

        # Sistema de instruções
        system_message = SystemMessage(
            content="Você é um assistente especializado em tecnologia e negócios. "
                   "Responda de forma clara e objetiva, focando em aspectos práticos."
        )

        for i, pergunta in enumerate(perguntas, 1):
            print(f"\n{'='*60}")
            print(f"PERGUNTA {i}: {pergunta}")
            print('='*60)

            # Prepara as mensagens
            messages = [system_message, HumanMessage(content=pergunta)]

            # Invoca o modelo
            logger.info(f"Enviando pergunta {i} para o modelo")
            response = llm.invoke(messages)

            # Exibe a resposta
            print(f"RESPOSTA: {response.content}")
            print()

            logger.info(f"Resposta {i} recebida com sucesso")

        print("\n✅ Demo concluída com sucesso!")
        logger.info("Chat simples finalizado com sucesso")

    except Exception as e:
        error_msg = f"Erro durante execução do chat: {str(e)}"
        logger.error(error_msg)
        print(f"❌ {error_msg}")
        return False

    return True

def configurar_ambiente():
    """
    Fornece instruções para configuração do ambiente.
    """
    print("""
📋 CONFIGURAÇÃO DO AMBIENTE
============================

Para executar este demo, configure as seguintes variáveis de ambiente:

1. Para Ollama (recomendado para teste local):
   export LLM_PROVIDER=ollama
   export MODEL_NAME=llama3:latest

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
""")

if __name__ == "__main__":
    configurar_ambiente()

    resposta = input("\nDeseja executar o demo? (s/n): ")
    if resposta.lower() in ['s', 'sim', 'y', 'yes']:
        demo_chat_simples()
    else:
        print("Demo cancelado.")