# AgentCore

Uma biblioteca Python abrangente para construir agentes de IA com integração de ferramentas e suporte a múltiplos provedores LLM.

## 🚀 Características Principais

- **Multi-provedor LLM**: AWS Bedrock (principal), OpenAI, Ollama, Google Gemini
- **Conversão automática de APIs**: Transforme especificações OpenAPI em ferramentas LangGraph
- **Base vetorial integrada**: Suporte nativo ao ChromaDB
- **Orquestração de agentes**: Baseado em LangGraph para fluxos complexos
- **Logging profissional**: Sistema de logs estruturado e colorido
- **Fácil instalação**: Disponível via pip

## 📦 Instalação

### Instalação básica
```bash
pip install agentcore
```

### Instalação com provedores específicos
```bash
# AWS Bedrock (recomendado para produção)
pip install agentcore[aws]

# OpenAI
pip install agentcore[openai]

# Ollama (desenvolvimento local)
pip install agentcore[ollama]

# Google Gemini
pip install agentcore[google]

# Todas as dependências
pip install agentcore[aws,openai,ollama,google]
```

### Para desenvolvimento
```bash
pip install agentcore[dev]
```

## 🛠️ Uso Rápido

### 1. Conversão de API para Ferramentas

A funcionalidade principal da biblioteca é converter especificações OpenAPI em ferramentas utilizáveis:

```python
from agentCore.utils import api2tool

# Converter OpenAPI para ferramentas LangGraph
tools = api2tool("./openapi.json")

# Ou de uma URL
tools = api2tool("https://petstore.swagger.io/v2/swagger.json")

# Especificar URL base customizada
tools = api2tool("./openapi.json", base_url="https://api.exemplo.com")
```

### 2. Diferentes Formatos de Saída

```python
# Lista de ferramentas (padrão)
tools = api2tool("./openapi.json", output_format="tools")

# Dicionário com operation_id como chave
tools_dict = api2tool("./openapi.json", output_format="dict")

# Gerar arquivo Python
code = api2tool("./openapi.json", output_format="file")

# Apenas nomes das ferramentas
names = api2tool("./openapi.json", output_format="names")

# Informações sobre a API
info = api2tool("./openapi.json", output_format="info")
```

### 3. Configuração de LLM

#### AWS Bedrock (Recomendado para Produção)
```python
from agentCore.providers import get_llm, get_embeddings

# Configurar AWS Bedrock (padrão)
llm = get_llm("bedrock")
embeddings = get_embeddings("bedrock")
```

Variáveis de ambiente necessárias:
```bash
export AWS_REGION=us-east-1
export BEDROCK_MODEL=anthropic.claude-3-sonnet-20240229-v1:0
export AWS_ACCESS_KEY_ID=your_access_key
export AWS_SECRET_ACCESS_KEY=your_secret_key
# ou configure via AWS CLI / IAM roles
```

#### Outros Provedores
```python
# OpenAI
llm = get_llm("openai")  # Requer OPENAI_API_KEY

# Ollama (desenvolvimento local)
llm = get_llm("ollama")  # Requer Ollama rodando localmente

# Google Gemini
llm = get_llm("gemini")  # Requer GEMINI_API_KEY
```

### 4. Criação de Agente Completo

```python
from agentCore.utils import api2tool
from agentCore.providers import get_llm
from agentCore.graphs import create_agent_graph

# 1. Configurar LLM (Bedrock por padrão)
llm = get_llm()

# 2. Converter API para ferramentas
tools = api2tool("./openapi.json")
tool_functions = [tool['function'] for tool in tools]

# 3. Criar agente com grafo
agent = create_agent_graph(llm, tools=tool_functions)

# 4. Usar o agente
from langchain_core.messages import HumanMessage

result = agent.invoke({
    "messages": [HumanMessage(content="Qual é o clima hoje?")]
})

print(result["messages"][-1].content)
```

## ⚙️ Configuração Avançada

### Arquivo .env
```bash
# Provedor principal (padrão: bedrock)
MAIN_PROVIDER=bedrock

# AWS Bedrock
AWS_REGION=us-east-1
BEDROCK_MODEL=anthropic.claude-3-sonnet-20240229-v1:0
BEDROCK_EMBEDDINGS_MODEL=amazon.titan-embed-text-v1
AWS_ACCESS_KEY_ID=your_access_key
AWS_SECRET_ACCESS_KEY=your_secret_key

# OpenAI (opcional)
OPENAI_API_KEY=your_openai_key
OPENAI_MODEL=gpt-4

# Ollama (opcional)
OLLAMA_BASE_URL=http://localhost:11434
OLLAMA_MODEL=llama3:latest

# Google Gemini (opcional)
GEMINI_API_KEY=your_gemini_key
GEMINI_MODEL=gemini-1.5-flash
```

### Logging Personalizado
```python
from agentCore.logger import get_logger

# Logger específico para seu componente
logger = get_logger("minha_aplicacao")

logger.info("Aplicação iniciada")
logger.success("Operação concluída com sucesso")
logger.error("Erro na aplicação")
```

## 📚 Exemplos Completos

### Exemplo 1: Agente de Clima
```python
from agentCore.utils import api2tool
from agentCore.providers import get_llm
from agentCore.graphs import create_agent_graph
from langchain_core.messages import HumanMessage

# Configurar LLM
llm = get_llm("bedrock")

# Carregar ferramentas de API de clima
tools = api2tool("https://api.openweathermap.org/data/2.5/swagger.json")
tool_functions = [tool['function'] for tool in tools]

# Criar agente
agent = create_agent_graph(llm, tools=tool_functions)

# Usar agente
response = agent.invoke({
    "messages": [HumanMessage(content="Qual a temperatura em São Paulo?")]
})

print(response["messages"][-1].content)
```

### Exemplo 2: Sistema Multi-API
```python
from agentCore.utils import api2tool
from agentCore.providers import get_llm
from agentCore.graphs import create_agent_graph

# Combinar múltiplas APIs
weather_tools = api2tool("./weather_api.json")
news_tools = api2tool("./news_api.json")

# Combinar todas as ferramentas
all_tools = []
all_tools.extend([tool['function'] for tool in weather_tools])
all_tools.extend([tool['function'] for tool in news_tools])

# Criar agente único com todas as ferramentas
llm = get_llm()
agent = create_agent_graph(llm, tools=all_tools)
```

## 🏗️ Arquitetura

```
agentCore/
├── utils/           # Utilidades principais
│   ├── api2tool.py     # Conversão OpenAPI → Ferramentas
│   └── openapi_to_tools.py
├── providers/       # Provedores LLM
│   └── llm_providers.py
├── graphs/         # Orquestração LangGraph
│   └── graph.py
└── logger/         # Sistema de logging
    └── logger.py
```

## 🔧 Desenvolvimento

### Configurar ambiente de desenvolvimento
```bash
git clone <repositorio>
cd agentcore
pip install -e .[dev]
```

### Executar testes
```bash
pytest
pytest --cov=agentCore  # com cobertura
```

### Formatação de código
```bash
black agentCore/
isort agentCore/
flake8 agentCore/
```

## 📄 Licença

MIT License - veja o arquivo [LICENSE](LICENSE) para detalhes.

## 🤝 Contribuindo

1. Fork o projeto
2. Crie uma branch para sua feature (`git checkout -b feature/AmazingFeature`)
3. Commit suas mudanças (`git commit -m 'Add some AmazingFeature'`)
4. Push para a branch (`git push origin feature/AmazingFeature`)
5. Abra um Pull Request

## 📞 Suporte

- **Issues**: [GitHub Issues](https://github.com/your-org/agent-core/issues)
- **Documentação**: [ReadTheDocs](https://agent-core.readthedocs.io)
- **Discussões**: [GitHub Discussions](https://github.com/your-org/agent-core/discussions)