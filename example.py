#!/usr/bin/env python3
"""
Exemplo de uso da biblioteca AgentCore

Este exemplo demonstra como:
1. Configurar um provedor LLM (AWS Bedrock)
2. Converter uma API OpenAPI para ferramentas
3. Criar um agente com as ferramentas
4. Usar o agente para responder perguntas
"""

import os
from pathlib import Path

# Importar componentes da biblioteca AgentCore
from agentCore.utils import api2tool
from agentCore.providers import get_llm, get_provider_info
from agentCore.graphs import create_agent_graph
from agentCore.logger import get_logger
from langchain_core.messages import HumanMessage

# Configurar logging
logger = get_logger("example")

def main():
    """Exemplo principal de uso da AgentCore"""

    print("🚀 Exemplo AgentCore - Criando um Agente com API Tools")
    print("=" * 60)

    # 1. Configurar LLM Provider (AWS Bedrock é padrão)
    print("\n1. 🔧 Configurando provedor LLM...")

    try:
        # Obter informações do provedor atual
        provider_info = get_provider_info()
        print(f"   Provedor: {provider_info['provider']}")

        if provider_info['provider'] == 'bedrock':
            print(f"   Região AWS: {provider_info.get('region', 'N/A')}")
            print(f"   Modelo: {provider_info.get('model', 'N/A')}")
            print(f"   Credenciais configuradas: {provider_info.get('credentials_configured', False)}")

        # Inicializar LLM
        llm = get_llm()
        print("   ✅ LLM configurado com sucesso!")

    except Exception as e:
        print(f"   ❌ Erro ao configurar LLM: {e}")
        print("\n💡 Dica: Configure as variáveis de ambiente:")
        print("   export AWS_REGION=us-east-1")
        print("   export AWS_ACCESS_KEY_ID=your_key")
        print("   export AWS_SECRET_ACCESS_KEY=your_secret")
        print("   Ou use AWS CLI / IAM roles")
        return

    # 2. Exemplo com OpenAPI fictício
    print("\n2. 📄 Convertendo OpenAPI para ferramentas...")

    # Criar um exemplo de OpenAPI spec
    example_openapi = {
        "openapi": "3.0.0",
        "info": {
            "title": "Exemplo API",
            "version": "1.0.0",
            "description": "API de exemplo para demonstração"
        },
        "servers": [
            {"url": "https://api.exemplo.com"}
        ],
        "paths": {
            "/weather/{city}": {
                "get": {
                    "operationId": "get_weather",
                    "summary": "Obter clima de uma cidade",
                    "description": "Retorna informações climáticas para uma cidade específica",
                    "parameters": [
                        {
                            "name": "city",
                            "in": "path",
                            "required": True,
                            "schema": {"type": "string"},
                            "description": "Nome da cidade"
                        },
                        {
                            "name": "units",
                            "in": "query",
                            "required": False,
                            "schema": {"type": "string", "enum": ["metric", "imperial"]},
                            "description": "Unidade de temperatura"
                        }
                    ]
                }
            },
            "/news": {
                "get": {
                    "operationId": "get_news",
                    "summary": "Obter últimas notícias",
                    "description": "Retorna as últimas notícias",
                    "parameters": [
                        {
                            "name": "category",
                            "in": "query",
                            "required": False,
                            "schema": {"type": "string"},
                            "description": "Categoria das notícias"
                        }
                    ]
                }
            }
        }
    }

    try:
        # Converter OpenAPI para ferramentas
        tools = api2tool(example_openapi)

        print(f"   ✅ {len(tools)} ferramentas geradas:")
        for tool in tools:
            print(f"      - {tool['schema']['name']}: {tool['schema']['description']}")

        # Extrair funções das ferramentas
        tool_functions = [tool['function'] for tool in tools]

    except Exception as e:
        print(f"   ❌ Erro ao converter OpenAPI: {e}")
        return

    # 3. Criar agente com ferramentas
    print("\n3. 🤖 Criando agente com ferramentas...")

    try:
        agent = create_agent_graph(llm, tools=tool_functions)
        print("   ✅ Agente criado com sucesso!")

    except Exception as e:
        print(f"   ❌ Erro ao criar agente: {e}")
        return

    # 4. Testar o agente
    print("\n4. 💬 Testando o agente...")

    test_questions = [
        "Qual é o clima em São Paulo?",
        "Me dê as últimas notícias sobre tecnologia",
        "Olá, como você está?"  # Esta não deve usar ferramentas
    ]

    for i, question in enumerate(test_questions, 1):
        print(f"\n   Pergunta {i}: {question}")
        print("   " + "-" * 50)

        try:
            result = agent.invoke({
                "messages": [HumanMessage(content=question)]
            })

            response = result["messages"][-1].content
            print(f"   Resposta: {response[:200]}...")

        except Exception as e:
            print(f"   ❌ Erro: {e}")

    # 5. Demonstrar outros formatos de saída
    print("\n5. 📊 Outros formatos de saída da api2tool:")

    try:
        # Informações sobre a API
        info = api2tool(example_openapi, output_format="info")
        print(f"   📋 Info: {info['title']} v{info['version']} - {info['tool_count']} ferramentas")

        # Apenas nomes das ferramentas
        names = api2tool(example_openapi, output_format="names")
        print(f"   🏷️  Nomes: {', '.join(names)}")

        # Gerar arquivo Python (comentado para não criar arquivo)
        # code = api2tool(example_openapi, output_format="file")
        # print(f"   📝 Código Python gerado: {len(code)} caracteres")

    except Exception as e:
        print(f"   ❌ Erro nos formatos alternativos: {e}")

    print("\n" + "=" * 60)
    print("🎉 Exemplo concluído!")
    print("\n💡 Próximos passos:")
    print("   1. Configure suas credenciais AWS para usar Bedrock")
    print("   2. Substitua o OpenAPI de exemplo por uma API real")
    print("   3. Teste com diferentes tipos de perguntas")
    print("   4. Explore os outros provedores LLM disponíveis")

def example_with_real_api():
    """
    Exemplo usando uma API real (descomentado quando necessário)
    """
    print("📡 Exemplo com API real (Petstore)")

    # Usar a API de exemplo do Swagger Petstore
    petstore_url = "https://petstore.swagger.io/v2/swagger.json"

    try:
        # Obter informações sobre a API
        info = api2tool(petstore_url, output_format="info")
        print(f"API encontrada: {info['title']} - {info['tool_count']} ferramentas disponíveis")

        # Listar ferramentas disponíveis
        names = api2tool(petstore_url, output_format="names")
        print("Ferramentas disponíveis:")
        for name in names[:5]:  # Mostrar apenas as primeiras 5
            print(f"  - {name}")
        if len(names) > 5:
            print(f"  ... e mais {len(names) - 5} ferramentas")

    except Exception as e:
        print(f"Erro ao acessar API real: {e}")

if __name__ == "__main__":
    main()

    # Descomente para testar com API real
    # print("\n" + "=" * 60)
    # example_with_real_api()