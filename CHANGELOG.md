# Changelog

Todas as mudanças notáveis neste projeto serão documentadas neste arquivo.

O formato é baseado em [Keep a Changelog](https://keepachangelog.com/pt-BR/1.0.0/),
e este projeto adere ao [Semantic Versioning](https://semver.org/lang/pt-BR/).

## [1.0.0] - 2024-12-29

### Adicionado
- **Funcionalidade principal `api2tool`**: Conversão automática de especificações OpenAPI para ferramentas LangGraph
- **Suporte multi-provedor LLM**:
  - AWS Bedrock (provedor principal para produção)
  - OpenAI
  - Ollama (desenvolvimento local)
  - Google Gemini
- **Sistema de logging profissional** com suporte a múltiplos níveis e formatação colorida
- **Orquestração de agentes** baseada em LangGraph
- **Integração com ChromaDB** para base vetorial
- **Configuração flexível** via variáveis de ambiente
- **Documentação completa** com exemplos de uso
- **Testes unitários** e cobertura de código
- **Suporte para instalação via pip**

### Características Principais
- Interface principal `from agentCore.utils import api2tool`
- Múltiplos formatos de saída: tools, dict, file, names, info
- Configuração automática de provedores LLM
- Sistema de logs estruturado
- Suporte a desenvolvimento e produção
- Arquitetura modular e extensível

### Configuração AWS
- Suporte completo ao AWS Bedrock
- Modelos Claude 3 Sonnet como padrão
- Configuração via AWS CLI, IAM roles ou variáveis de ambiente
- Integração com Amazon Titan para embeddings

### Documentação
- README detalhado com exemplos
- Configuração via arquivo .env
- Guias de desenvolvimento e contribuição
- Exemplos de uso completos

## Próximas Versões

### Planejado para [1.1.0]
- Suporte a mais provedores LLM
- Melhorias na conversão OpenAPI
- Cache de ferramentas
- Interface CLI expandida
- Mais exemplos e templates

### Planejado para [1.2.0]
- Interface web para gerenciamento
- Métricas e monitoramento
- Suporte a plugins
- Integração com mais bases vetoriais