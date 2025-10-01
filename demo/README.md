# 🚀 Demos da Biblioteca AgentCore 

Este diretório contém 9 cenários progressivos que demonstram como implementar sistemas de IA para o segmento de **adquirência** (processamento de pagamentos com cartão), desde assistentes básicos até sistemas avançados de análise e otimização.

## 📋 Visão Geral dos Cenários

### 🔰 **Cenários Básicos (1-3): Assistentes para Adquirência**
- **Cenário 1**: Chat básico - Atendimento a merchants, vendedores e operações
- **Cenário 2**: RAG - Base de conhecimento (manuais POS, políticas, regulamentações)
- **Cenário 3**: RAG + Tools - Integração com APIs (transações, cadastro, CRM)

### 🧠 **Cenários Avançados (4-5): Orquestração Inteligente**
- **Cenário 4**: LangGraph - Workflows condicionais (credenciamento, risco, chargebacks)
- **Cenário 5**: CrewAI - Equipe de especialistas (transações, risco, compliance, comercial)

### 🔬 **Cenários de Qualidade (6-7): Garantia de Precisão**
- **Cenário 6**: Evals Básico - Validação de qualidade (liquidação, MDR, compliance)
- **Cenário 7**: Evals Avançado - A/B testing e otimização científica

### 📊 **Cenários de Otimização (8-9): Performance Técnica**
- **Cenário 8**: Model Selection - Escolha do modelo ideal por caso de uso
- **Cenário 9**: Chunking - Otimização de precisão em documentos técnicos

## 🎯 Jornada de Aprendizado para Adquirência

### **Para Equipe de Atendimento/Suporte**
```
Cenário 1 → Cenário 2 → Cenário 6
```
Chat básico para merchants → Base de conhecimento (manuais POS) → Validação de qualidade

### **Para Desenvolvedores de Produto**
```
Cenário 1 → Cenário 3 → Cenário 4
```
Chat básico → Integração com APIs → Workflows inteligentes (credenciamento, risco)

### **Para Arquitetos de Sistemas**
```
Cenário 3 → Cenário 4 → Cenário 5 → Cenário 8
```
APIs + RAG → Workflows → Equipe de agentes → Otimização de modelos

### **Para Líderes de Tecnologia**
```
Leia explicações executivas dos Cenários 3, 5, 7, 8, 9
Execute: Cenário 5 (multi-agentes), 7 (A/B testing)
```
Visão estratégica focada em casos de uso habilitadores para o negócio.

## 🏗️ Estrutura de Cada Cenário

Cada cenário contém:

### **📁 Arquivos Principais**
- **`codigo_implementacao.py`**: Implementação técnica funcional
- **`explicacao_executiva.md`**: Casos de uso habilitadores para adquirência

### **🎯 O que Você Aprenderá**

#### **Código de Implementação**:
- Como usar a biblioteca agentCore
- Integração com APIs de adquirência (transações, cadastro, risco)
- Configurações e otimizações
- Tratamento de erros e logging

#### **Explicação Executiva**:
- **Casos de uso habilitadores** para adquirência
- Exemplos práticos: merchants, força de vendas, operações
- Benefícios específicos do segmento
- Jornada de implementação
- Considerações de compliance (PCI-DSS, LGPD, Bacen)

## 📊 Matriz de Complexidade para Adquirência

| Cenário | Complexidade | Caso de Uso Principal | Tempo Impl. | Impacto |
|---------|--------------|----------------------|-------------|---------|
| 1       | ⭐           | Atendimento básico merchants | 1-2 semanas | Médio |
| 2       | ⭐⭐         | Manuais POS + políticas | 2-3 semanas | Alto |
| 3       | ⭐⭐⭐       | APIs + RAG (transações, cadastro) | 4-6 semanas | Alto |
| 4       | ⭐⭐⭐⭐     | Workflows (credenciamento, risco) | 6-8 semanas | Muito Alto |
| 5       | ⭐⭐⭐⭐⭐   | Multi-agentes especializados | 8-12 semanas | Muito Alto |
| 6       | ⭐⭐         | Validação de qualidade | 3-4 semanas | Médio |
| 7       | ⭐⭐⭐⭐     | A/B testing e otimização | 4-6 semanas | Alto |
| 8       | ⭐⭐⭐       | Seleção de modelo por caso de uso | 4-5 semanas | Médio |
| 9       | ⭐⭐⭐       | Otimização chunking (manuais) | 3-4 semanas | Alto |

## 🚀 Como Executar os Demos

### **Pré-requisitos**
```bash
# 1. Instalar biblioteca
pip install -e .

# 2. Configurar variáveis de ambiente
cp .env.example .env
# Editar .env com suas credenciais

# 3. Instalar dependências específicas
pip install -r requirements.txt
```

### **Execução Individual**
```bash
# Navegar para o cenário desejado
cd demo/cenario1

# Executar o demo
python chat_simples.py

# Ler a explicação executiva
cat explicacao_executiva.md
```

### **Configurações Recomendadas**

#### **Para Desenvolvimento Local**:
```bash
export LLM_PROVIDER=ollama
export MODEL_NAME=llama3.2
export VECTOR_PROVIDER=chroma
```

#### **Para Ambiente Produção**:
```bash
export LLM_PROVIDER=openai
export MODEL_NAME=gpt-4
export VECTOR_PROVIDER=aws
export AWS_ACCESS_KEY_ID=sua_chave
export AWS_SECRET_ACCESS_KEY=sua_chave_secreta
```

## 💡 Dicas de Implementação

### **Início Rápido (2 horas)**
1. **Cenário 1**: Entenda os conceitos básicos
2. **Cenário 2**: Veja o poder do RAG
3. **Cenário 6**: Aprenda sobre qualidade

### **Prova de Conceito (1 semana)**
1. **Cenário 3**: Implemente com ferramentas
2. **Cenário 7**: Configure avaliações
3. **Teste com dados reais** da sua empresa

### **Implementação Produção (1 mês)**
1. **Cenário 5**: Sistema completo de agentes
2. **Cenário 8**: Otimize modelo ideal
3. **Cenário 9**: Otimize chunking
4. **Deploy e monitoramento**

## 🎯 Casos de Uso Específicos de Adquirência

### **💳 Atendimento a Merchants (Estabelecimentos Comerciais)**
- **Cenários Recomendados**: 1, 2, 3, 6, 9
- **Casos de Uso**:
  - Consulta de transações e liquidações
  - Suporte técnico a terminais POS
  - Dúvidas sobre MDR, taxas e prazos
  - Troubleshooting de problemas (códigos de erro, conectividade)
  - Gestão de chargebacks e contestações

### **🎯 Força de Vendas**
- **Cenários Recomendados**: 2, 3, 4, 8
- **Casos de Uso**:
  - Credenciamento de novos merchants
  - Consulta a tabelas comerciais e condições
  - Simulações de taxas e antecipação
  - Status de propostas em análise
  - Documentação necessária por tipo de empresa

### **🛡️ Gestão de Risco e Antifraude**
- **Cenários Recomendados**: 4, 5, 6, 7
- **Casos de Uso**:
  - Análise de risco de credenciamento
  - Detecção de padrões de fraude
  - Investigação de chargebacks suspeitos
  - Score de crédito e limite transacional
  - Monitoramento de merchants de alto risco

### **⚖️ Compliance e Regulatório**
- **Cenários Recomendados**: 2, 5, 6, 9
- **Casos de Uso**:
  - Consulta a circulares do Banco Central
  - Validação de conformidade PCI-DSS
  - Interpretação de normas regulatórias
  - Auditoria e documentação de processos
  - LGPD e tratamento de dados

### **⚙️ Operações e Conciliação**
- **Cenários Recomendados**: 3, 4, 5, 7
- **Casos de Uso**:
  - Processos de liquidação e conciliação
  - Split de pagamento (marketplaces)
  - Gestão de disputas e contestações
  - Reconciliação bancária
  - Automação de processos operacionais

## 📈 Roadmap de Implementação para Adquirência

### **Fase 1: Quick Wins (Mês 1-2)**
- **Cenários 1-2**: Assistente básico + base de conhecimento
- **Foco**: Atendimento a merchants (liquidação, terminais POS)
- **Resultado**: Redução de escalações para atendimento humano

### **Fase 2: Automação com Integração (Mês 2-4)**
- **Cenário 3**: RAG + APIs (transações, cadastro, CRM)
- **Foco**: Consultas em tempo real + ações automatizadas
- **Resultado**: Resolução completa de ponta a ponta

### **Fase 3: Processos Complexos (Mês 4-6)**
- **Cenários 4-5**: Workflows + Multi-agentes
- **Foco**: Credenciamento, análise de risco, investigação de fraude
- **Resultado**: Processos críticos automatizados com qualidade

### **Fase 4: Otimização e Excelência (Mês 6+)**
- **Cenários 6-9**: Evals + A/B testing + Model selection + Chunking
- **Foco**: Qualidade garantida, otimização científica, custos otimizados
- **Resultado**: Sistema production-ready de classe mundial


### **Recursos de Ajuda**

#### **Documentação**
- [Guia de Configuração](../README.md)
- [API Reference](../docs/api/)
- [Troubleshooting Guide](../docs/troubleshooting.md)

#### **Comunidade**
- GitHub Issues: Para bugs e features


## 🔮 Próximos Passos

### **Começando**
1. **Escolha seu perfil** (Atendimento, Desenvolvimento, Arquitetura, Liderança)
2. **Siga a jornada recomendada** para seu perfil
3. **Leia as explicações executivas** antes de implementar
4. **Execute os demos** com dados de teste da Cielo

### **Customização para Seu Negócio**
1. **Adapte exemplos**: Use seus manuais POS, políticas e tabelas comerciais
2. **Integre APIs reais**: Transações, cadastro, CRM, antifraude
3. **Implemente Evals**: Valide qualidade com casos reais do seu negócio
4. **Otimize continuamente**: A/B testing, model selection, chunking

### **Expansões Avançadas para Cielo**
- **Análise preditiva**: Previsão de chargebacks e fraude
- **Pricing dinâmico**: Otimização de MDR em tempo real
- **Customer success**: Análise de satisfação e churn de merchants
- **Forecast**: Projeções de volume e receita

