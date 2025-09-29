# Guia de Uso - AgentCore

Este guia mostra como usar a biblioteca AgentCore depois de instalada.

## 🎯 Conceitos Principais

A AgentCore é baseada em alguns conceitos fundamentais:

1. **api2tool**: Função principal que converte APIs OpenAPI em ferramentas utilizáveis
2. **Provedores LLM**: Sistema unificado para diferentes provedores (Bedrock, OpenAI, etc.)
3. **Agentes**: Orquestração inteligente usando LangGraph
4. **Logging**: Sistema profissional de logs

## 🚀 Início Rápido

### Uso Básico
```python
from agentCore.utils import api2tool

# Converter OpenAPI para ferramentas
tools = api2tool("./api.json")
print(f"Geradas {len(tools)} ferramentas")
```

### Uso Completo
```python
from agentCore.utils import api2tool
from agentCore.providers import get_llm
from agentCore.graphs import create_agent_graph
from langchain_core.messages import HumanMessage

# 1. Configurar LLM
llm = get_llm()  # Usa AWS Bedrock por padrão

# 2. Converter API para ferramentas
tools = api2tool("./api.json")
tool_functions = [tool['function'] for tool in tools]

# 3. Criar agente
agent = create_agent_graph(llm, tools=tool_functions)

# 4. Usar agente
response = agent.invoke({
    "messages": [HumanMessage(content="Sua pergunta aqui")]
})

print(response["messages"][-1].content)
```

## 📡 Trabalhando com APIs

### 1. Diferentes Fontes de OpenAPI

```python
# Arquivo local
tools = api2tool("./openapi.json")

# URL remota
tools = api2tool("https://api.exemplo.com/swagger.json")

# Dicionário Python
openapi_dict = {"openapi": "3.0.0", ...}
tools = api2tool(openapi_dict)
```

### 2. Formatos de Saída

```python
# Lista de ferramentas (padrão)
tools = api2tool("api.json", output_format="tools")

# Dicionário indexado
tools_dict = api2tool("api.json", output_format="dict")

# Gerar arquivo Python
python_code = api2tool("api.json", output_format="file")

# Apenas nomes
names = api2tool("api.json", output_format="names")

# Informações da API
info = api2tool("api.json", output_format="info")
```

### 3. Especificar URL Base

```python
tools = api2tool("api.json", base_url="https://production-api.com")
```

## 🤖 Provedores LLM

### AWS Bedrock (Recomendado)

```python
from agentCore.providers import get_llm, get_embeddings, get_provider_info

# Usar Bedrock (padrão)
llm = get_llm("bedrock")
embeddings = get_embeddings("bedrock")

# Ver informações
info = get_provider_info("bedrock")
print(info)
```

### Outros Provedores

```python
# OpenAI
llm = get_llm("openai")

# Ollama (local)
llm = get_llm("ollama")

# Google Gemini
llm = get_llm("gemini")

# Provedor automático (baseado em MAIN_PROVIDER)
llm = get_llm()
```

## 🔧 Configuração Avançada

### 1. Variáveis de Ambiente

```bash
# Provedor principal
MAIN_PROVIDER=bedrock

# AWS Bedrock
AWS_REGION=us-east-1
BEDROCK_MODEL=anthropic.claude-3-sonnet-20240229-v1:0

# OpenAI
OPENAI_API_KEY=sua_chave
OPENAI_MODEL=gpt-4

# Ollama
OLLAMA_BASE_URL=http://localhost:11434
OLLAMA_MODEL=llama3:latest
```

### 2. Arquivo .env
Crie um arquivo `.env` no seu projeto:

```env
MAIN_PROVIDER=bedrock
AWS_REGION=us-east-1
BEDROCK_MODEL=anthropic.claude-3-sonnet-20240229-v1:0
```

### 3. Logging Personalizado

```python
from agentCore.logger import get_logger

logger = get_logger("minha_app")

logger.info("Aplicação iniciada")
logger.success("Operação bem-sucedida")
logger.error("Erro na aplicação")
logger.tool_execution("minha_ferramenta")
```

## 📊 Interface CLI

A AgentCore inclui uma interface de linha de comando:

### Comandos Principais

```bash
# Ver versão
agentcore version

# Ver informações do provedor
agentcore info

# Converter OpenAPI
agentcore convert api.json -o tools.py

# Validar OpenAPI
agentcore validate api.json
```

### Exemplos CLI

```bash
# Gerar ferramentas de uma API
agentcore convert https://petstore.swagger.io/v2/swagger.json

# Especificar URL base
agentcore convert api.json -b https://api.producao.com

# Diferentes formatos
agentcore convert api.json -f info  # mostrar informações
agentcore convert api.json -f names # listar nomes
```

## 🎨 Casos de Uso Avançados

### 1. Multi-API Agent

```python
from agentCore.utils import api2tool
from agentCore.providers import get_llm
from agentCore.graphs import create_agent_graph

# Combinar múltiplas APIs
weather_tools = api2tool("weather_api.json")
news_tools = api2tool("news_api.json")
calendar_tools = api2tool("calendar_api.json")

# Juntar todas as ferramentas
all_tools = []
all_tools.extend([t['function'] for t in weather_tools])
all_tools.extend([t['function'] for t in news_tools])
all_tools.extend([t['function'] for t in calendar_tools])

# Criar agente super poderoso
llm = get_llm()
agent = create_agent_graph(llm, tools=all_tools)

# Usar para tarefas complexas
result = agent.invoke({
    "messages": [HumanMessage(content="Qual o clima hoje e agende uma reunião às 15h")]
})
```

### 2. Customizar Comportamento

```python
# Usar provedor específico mesmo com padrão configurado
llm = get_llm("openai")  # forçar OpenAI

# Gerar arquivo customizado
code = api2tool("api.json", output_format="file")
with open("minhas_tools.py", "w") as f:
    f.write(code)

# Adicionar logging personalizado
from agentCore.logger import get_logger
logger = get_logger("meu_agente")

def meu_agente_personalizado():
    logger.info("Iniciando meu agente")
    # ... sua lógica aqui
    logger.success("Agente concluído")
```

### 3. Integração com Frameworks

#### FastAPI
```python
from fastapi import FastAPI
from agentCore.utils import api2tool
from agentCore.providers import get_llm

app = FastAPI()
llm = get_llm()

@app.post("/chat")
async def chat(message: str):
    # Usar agente aqui
    return {"response": "..."}
```

#### Flask
```python
from flask import Flask, request
from agentCore.utils import api2tool

app = Flask(__name__)
tools = api2tool("api.json")

@app.route("/api", methods=["POST"])
def api_endpoint():
    # Usar ferramentas aqui
    return {"result": "..."}
```

## 📚 Exemplos Práticos

### Exemplo 1: Agente de E-commerce

```python
from agentCore.utils import api2tool
from agentCore.providers import get_llm
from agentCore.graphs import create_agent_graph

# Carregar API de e-commerce
tools = api2tool("ecommerce_api.json", base_url="https://loja.com/api")
tool_functions = [tool['function'] for tool in tools]

# Criar agente
llm = get_llm()
agent = create_agent_graph(llm, tools=tool_functions)

# Usar agente
questions = [
    "Mostre produtos em promoção",
    "Qual o status do pedido #12345?",
    "Adicione produto X ao carrinho"
]

for q in questions:
    result = agent.invoke({"messages": [HumanMessage(content=q)]})
    print(f"P: {q}")
    print(f"R: {result['messages'][-1].content}\n")
```

### Exemplo 2: Sistema de Monitoramento

```python
from agentCore.utils import api2tool
from agentCore.logger import get_logger

logger = get_logger("monitor")

# APIs de monitoramento
monitoring_tools = api2tool("monitoring_api.json")

def check_system_health():
    logger.info("Iniciando verificação de saúde do sistema")

    # Usar ferramentas para verificar métricas
    for tool in monitoring_tools:
        try:
            result = tool['function']()
            logger.success(f"Check OK: {tool['schema']['name']}")
        except Exception as e:
            logger.error(f"Check FAILED: {tool['schema']['name']}: {e}")
```

## 🔍 Debug e Troubleshooting

### Verificar Configuração

```python
from agentCore.providers import get_provider_info

# Ver configuração atual
info = get_provider_info()
print(f"Provedor: {info['provider']}")
print(f"Configurado: {info}")

# Testar conexão
try:
    llm = get_llm()
    response = llm.invoke("test")
    print("✅ LLM funcionando")
except Exception as e:
    print(f"❌ Erro no LLM: {e}")
```

### Logs Detalhados

```python
from agentCore.logger import get_logger

# Logger mais verboso
logger = get_logger("debug", level="DEBUG")
logger.debug("Informação detalhada")
```

### Testar APIs

```python
# Verificar se API está acessível
info = api2tool("api.json", output_format="info")
print(f"API: {info['title']}")
print(f"Ferramentas: {info['tool_count']}")

# Listar ferramentas disponíveis
names = api2tool("api.json", output_format="names")
print("Ferramentas:", names)
```

## 🚀 Deploy em Produção

### 1. Configuração para Produção

```python
import os
os.environ['MAIN_PROVIDER'] = 'bedrock'
os.environ['AWS_REGION'] = 'us-east-1'

# Usar IAM roles em vez de chaves hardcoded
from agentCore.providers import get_llm
llm = get_llm()  # Será configurado via IAM role
```

### 2. Docker

```dockerfile
FROM python:3.11-slim
RUN pip install agentcore[aws]
COPY . .
CMD ["python", "app.py"]
```

### 3. Variáveis de Ambiente Seguras

```bash
# Use secrets managers em produção
export BEDROCK_MODEL=anthropic.claude-3-sonnet-20240229-v1:0
export AWS_REGION=us-east-1
# Não inclua chaves de API em variáveis - use IAM roles
```

## 📈 Performance e Otimização

### Cache de Ferramentas
```python
# Gerar uma vez, reutilizar
tools = api2tool("api.json")
# Salvar tools se necessário para reuso
```

### Logging Eficiente
```python
from agentCore.logger import get_logger

# Logger específico para cada componente
api_logger = get_logger("api")
agent_logger = get_logger("agent")
```

### Modelos Otimizados
```python
# Usar modelos menores para tarefas simples
os.environ['BEDROCK_MODEL'] = 'anthropic.claude-3-haiku-20240307-v1:0'
```

---

Para mais exemplos e documentação completa, consulte o README.md e os arquivos de exemplo inclusos na biblioteca.