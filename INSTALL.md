# Guia de Instalação - AgentCore

Este guia fornece instruções detalhadas para instalar e configurar a biblioteca AgentCore.

## 📋 Requisitos do Sistema

- Python 3.8 ou superior
- pip (gerenciador de pacotes Python)
- Acesso à internet para download das dependências

### Requisitos Opcionais por Provedor

#### AWS Bedrock (Recomendado)
- Conta AWS ativa
- Credenciais AWS configuradas
- Acesso ao serviço Bedrock na sua região

#### OpenAI
- Chave da API OpenAI
- Créditos na conta OpenAI

#### Ollama (Desenvolvimento Local)
- Ollama instalado localmente
- Modelos baixados (ex: llama3)

#### Google Gemini
- Chave da API Google Gemini
- Acesso ao Google AI Studio

## 🚀 Instalação Rápida

### Opção 1: Instalação Básica
```bash
pip install agentcore
```

### Opção 2: Instalação com Provedores Específicos

#### Para uso com AWS Bedrock (Produção)
```bash
pip install agentcore[aws]
```

#### Para uso com OpenAI
```bash
pip install agentcore[openai]
```

#### Para desenvolvimento local com Ollama
```bash
pip install agentcore[ollama]
```

#### Para uso com Google Gemini
```bash
pip install agentcore[google]
```

#### Instalação completa (todos os provedores)
```bash
pip install agentcore[aws,openai,ollama,google]
```

### Opção 3: Para Desenvolvimento
```bash
pip install agentcore[dev]
```

## ⚙️ Configuração

### 1. Configuração AWS Bedrock (Recomendado)

#### Método 1: AWS CLI (Recomendado)
```bash
# Instalar AWS CLI se não tiver
pip install awscli

# Configurar credenciais
aws configure
```

#### Método 2: Variáveis de Ambiente
```bash
export AWS_ACCESS_KEY_ID=seu_access_key
export AWS_SECRET_ACCESS_KEY=sua_secret_key
export AWS_REGION=us-east-1
```

#### Método 3: IAM Roles (Para EC2, Lambda, etc.)
Se executando em serviços AWS, configure uma role IAM com permissões Bedrock.

#### Configurações Específicas do Bedrock
```bash
export BEDROCK_MODEL=anthropic.claude-3-sonnet-20240229-v1:0
export BEDROCK_EMBEDDINGS_MODEL=amazon.titan-embed-text-v1
```

### 2. Configuração OpenAI
```bash
export OPENAI_API_KEY=sua_chave_openai
export OPENAI_MODEL=gpt-4  # opcional, padrão: gpt-3.5-turbo
```

### 3. Configuração Ollama
```bash
# Instalar Ollama (se não tiver)
curl -fsSL https://ollama.ai/install.sh | sh

# Baixar modelo
ollama pull llama3

# Iniciar Ollama
ollama serve

# Configurar AgentCore
export OLLAMA_BASE_URL=http://localhost:11434
export OLLAMA_MODEL=llama3:latest
```

### 4. Configuração Google Gemini
```bash
export GEMINI_API_KEY=sua_chave_gemini
export GEMINI_MODEL=gemini-1.5-flash  # opcional
```

### 5. Arquivo .env (Recomendado)

Crie um arquivo `.env` na raiz do seu projeto:

```bash
# Provedor principal
MAIN_PROVIDER=bedrock

# AWS Bedrock (recomendado para produção)
AWS_REGION=us-east-1
AWS_ACCESS_KEY_ID=seu_access_key
AWS_SECRET_ACCESS_KEY=sua_secret_key
BEDROCK_MODEL=anthropic.claude-3-sonnet-20240229-v1:0
BEDROCK_EMBEDDINGS_MODEL=amazon.titan-embed-text-v1

# OpenAI (opcional)
OPENAI_API_KEY=sua_chave_openai
OPENAI_MODEL=gpt-4

# Ollama (opcional)
OLLAMA_BASE_URL=http://localhost:11434
OLLAMA_MODEL=llama3:latest

# Google Gemini (opcional)
GEMINI_API_KEY=sua_chave_gemini
GEMINI_MODEL=gemini-1.5-flash
```

## ✅ Verificação da Instalação

### 1. Teste via Python
```python
# Testar importação
from agentCore.utils import api2tool
from agentCore.providers import get_llm, get_provider_info

# Verificar provedor configurado
info = get_provider_info()
print(f"Provedor ativo: {info['provider']}")

# Testar LLM
llm = get_llm()
print("✅ LLM configurado com sucesso!")
```

### 2. Teste via CLI
```bash
# Verificar versão
agentcore version

# Verificar informações do provedor
agentcore info

# Testar conversão de OpenAPI
agentcore validate https://petstore.swagger.io/v2/swagger.json
```

### 3. Executar Exemplo
```bash
# Baixar exemplo (se instalado via git)
python example.py

# Ou criar um teste simples
python -c "
from agentCore.utils import api2tool
tools = api2tool('https://petstore.swagger.io/v2/swagger.json', output_format='info')
print(f'API encontrada: {tools[\"title\"]} - {tools[\"tool_count\"]} ferramentas')
"
```

## 🔧 Instalação para Desenvolvimento

### 1. Clone do Repositório
```bash
git clone <url-do-repositorio>
cd agentcore
```

### 2. Instalação em Modo Desenvolvimento
```bash
# Criar ambiente virtual
python -m venv venv
source venv/bin/activate  # Linux/Mac
# ou
venv\Scripts\activate  # Windows

# Instalar em modo desenvolvimento
pip install -e .[dev]
```

### 3. Configurar Ferramentas de Desenvolvimento
```bash
# Instalar pre-commit hooks
pre-commit install

# Executar testes
pytest

# Executar testes com cobertura
pytest --cov=agentCore

# Formatar código
black agentCore/
isort agentCore/
```

## 🐳 Instalação com Docker

### 1. Dockerfile de Exemplo
```dockerfile
FROM python:3.11-slim

WORKDIR /app

COPY requirements.txt .
RUN pip install -r requirements.txt

# Instalar AgentCore
RUN pip install agentcore[aws]

COPY . .

CMD ["python", "app.py"]
```

### 2. Docker Compose
```yaml
version: '3.8'

services:
  agentcore-app:
    build: .
    environment:
      - AWS_REGION=us-east-1
      - BEDROCK_MODEL=anthropic.claude-3-sonnet-20240229-v1:0
      - MAIN_PROVIDER=bedrock
    volumes:
      - ~/.aws:/root/.aws:ro  # Compartilhar credenciais AWS
```

## 🚨 Solução de Problemas

### Erro: "langchain-aws não está instalado"
```bash
pip install langchain-aws boto3
# ou
pip install agentcore[aws]
```

### Erro: "OPENAI_API_KEY não configurada"
```bash
export OPENAI_API_KEY=sua_chave
# ou adicione ao arquivo .env
```

### Erro: "Erro ao conectar com provedor LLM"
#### Para Bedrock:
- Verifique credenciais AWS
- Confirme acesso ao Bedrock na sua região
- Verifique se o modelo está disponível

#### Para Ollama:
```bash
# Verificar se Ollama está rodando
ollama list

# Iniciar Ollama
ollama serve
```

### Erro de Importação
```bash
# Verificar instalação
pip list | grep agentcore

# Reinstalar se necessário
pip uninstall agentcore
pip install agentcore
```

### Problemas de Dependências
```bash
# Atualizar pip
pip install --upgrade pip

# Limpar cache do pip
pip cache purge

# Reinstalar dependências
pip install --force-reinstall agentcore
```
# 🔧 Instalação Local
Opção 1: Instalação em modo desenvolvimento (Recomendado)
# No diretório do projeto agc-lib
pip install -e .
O -e (editable) permite que mudanças no código sejam refletidas imediatamente sem reinstalar.
Opção 2: Instalação local direta
# No diretório do projeto
pip install .
Opção 3: Build e instalação
# Construir distribuição
python -m build

# Instalar do arquivo gerado
pip install dist/agentcore-1.0.0-py3-none-any.whl
📦 Verificar Instalação
Após instalar, teste:
import agentCore
from agentCore.providers import get_llm
from agentCore.utils import api2tool

print("AgentCore instalado com sucesso!")
🛠️ Para Desenvolvimento
Se você vai desenvolver no projeto:
# Instalar com dependências de desenvolvimento
pip install -e .[dev]

# Instalar todas as dependências opcionais
pip install -e .[aws,openai,ollama,google,dev]
🐍 Ambiente Virtual (Recomendado)
# Criar ambiente virtual
python -m venv venv

# Ativar (Linux/Mac)
source venv/bin/activate

# Ativar (Windows)
venv\Scripts\activate

# Instalar projeto
pip install -e .
✅ Verificação Final
# Testar CLI
agentcore --help

# Executar demo
python e2e_demo.py

# Executar testes
pytest tests/ -v


## 📚 Próximos Passos

Após a instalação bem-sucedida:

1. **Leia o README.md** para exemplos de uso
2. **Execute o example.py** para ver a biblioteca em ação
3. **Configure seu provedor LLM preferido**
4. **Teste com suas próprias APIs OpenAPI**
5. **Explore a documentação completa**

## 📞 Suporte

Se encontrar problemas durante a instalação:

- Verifique os [Issues no GitHub](https://github.com/your-org/agent-core/issues)
- Consulte a [Documentação](https://agent-core.readthedocs.io)

