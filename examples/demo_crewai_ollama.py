import os
from dotenv import load_dotenv
from crewai import Agent, Task, Crew, Process
from langchain_ollama import ChatOllama

# Carregar variáveis de ambiente
load_dotenv()

# Desabilitar traces online do CrewAI
os.environ["CREWAI_TELEMETRY_ENABLED"] = "false"

def run_crewai_ollama_demo():
    """
    Demonstração de um time de agentes CrewAI com Ollama,
    usando um ambiente com versões compatíveis.
    """
    print("🚀 Iniciando Demo com Ambiente Corrigido...")

    try:
        # 1. Configurar o LLM da forma correta e simples
        print("   Passo 1: A configurar LLM local...")
        modelo_ollama = os.getenv("OLLAMA_MODEL", "llama3")
        base_url = os.getenv("OLLAMA_BASE_URL", "http://localhost:11434")

        # Configurar LLM com system prompt forçando português
        ollama_llm = ChatOllama(
            model=f"ollama/{modelo_ollama}",
            base_url=base_url,
            temperature=0.7,
            system="Você é um assistente que SEMPRE responde em português brasileiro. NUNCA responda em inglês ou outros idiomas. Todas as suas respostas devem ser claras, profissionais e exclusivamente em português do Brasil."
        )
        print(f"   Resultado: LLM '{modelo_ollama}' configurado com sucesso.")

        # 2. Definir os Agentes
        print("   Passo 2: A criar os agentes...")
        pesquisador = Agent(
            role='Pesquisador Sênior de IA',
            goal='Encontrar os desenvolvimentos e impactos mais recentes da IA no desenvolvimento de software',
            backstory="Você é um pesquisador experiente, mestre em destilar informações complexas. SEMPRE responda em português.",
            llm=ollama_llm,
            verbose=True,
            allow_delegation=False,
        )
        escritor = Agent(
            role='Escritor Técnico Especialista',
            goal='Criar um relatório executivo de 2 parágrafos sobre o impacto da IA no desenvolvimento de software',
            backstory="""Você é um escritor especializado em relatórios executivos.
            REGRAS IMPORTANTES:
            1. NUNCA responda apenas com 'Thought' ou 'I now can give a great answer'
            2. SEMPRE forneça o relatório completo de 2 parágrafos
            3. SEMPRE escreva em português brasileiro
            4. Sua resposta deve ter pelo menos 200 caracteres
            5. Comece diretamente com o conteúdo do relatório""",
            llm=ollama_llm,
            verbose=True,
            allow_delegation=False,
        )
        print("   Resultado: Agentes criados.")

        # 3. Definir as Tarefas
        print("   Passo 3: A definir as tarefas...")
        tarefa_pesquisa = Task(
            description=(
                "Pesquise o impacto da IA no ciclo de vida do desenvolvimento de software (SDLC), "
                "identificando ferramentas, benefícios (produtividade) e desafios (qualidade do código, segurança)."
            ),
            expected_output='Um boletim com os pontos principais, exemplos de ferramentas e uma análise de prós e contras.',
            agent=pesquisador,
        )
        tarefa_escrita = Task(
            description="""
            ===== INSTRUÇÕES OBRIGATÓRIAS - LEIA COM ATENÇÃO =====

            IDIOMA: PORTUGUÊS BRASILEIRO OBRIGATÓRIO
            - TODA a resposta deve ser em português brasileiro
            - PROIBIDO usar inglês, incluindo palavras como "Thought", "Final Answer", etc.
            - Se aparecer qualquer palavra em inglês, reescreva em português

            CONTEÚDO:
            1. Escreva um relatório executivo de EXATAMENTE 2 parágrafos em português brasileiro
            2. PARÁGRAFO 1: Benefícios da IA no desenvolvimento (produtividade, qualidade, ferramentas)
            3. PARÁGRAFO 2: Desafios da IA (segurança, qualidade do código, limitações)
            4. Use linguagem profissional para executivos brasileiros
            5. Mínimo 400 caracteres
            6. Comece diretamente com o conteúdo em português

            EXEMPLO DE INÍCIO CORRETO:
            "A inteligência artificial tem revolucionado..."

            PROIBIDO:
            - Thought:
            - I now can...
            - Final Answer:
            - Qualquer palavra em inglês

            Com base no contexto da pesquisa anterior, crie este relatório em português brasileiro agora.
            """,
            expected_output='Relatório executivo completo com exatamente 2 parágrafos sobre IA no desenvolvimento de software, mínimo 400 caracteres, escrito inteiramente em português brasileiro, sem nenhuma palavra em inglês.',
            agent=escritor,
            context=[tarefa_pesquisa],
        )
        print("   Resultado: Tarefas definidas.")

        # 4. Montar e Executar o Crew
        print("   Passo 4: A montar e executar o time...")
        time_de_ia = Crew(
            agents=[pesquisador, escritor],
            tasks=[tarefa_pesquisa, tarefa_escrita],
            process=Process.sequential,
            verbose=True,
        )
        
        print("\n   [AGUARDE] A chamada 'kickoff()' foi iniciada. A IA está a pensar...\n")
        resultado_final = time_de_ia.kickoff()
        print("\n   [SUCESSO] A chamada 'kickoff()' terminou.")

        # 5. Apresentar o Resultado Final
        print("\n" + "="*50)
        print("✅ Trabalho do time concluído com sucesso!")
        print("="*50)
        print("\n📄 Relatório Final Gerado:\n")

        # Verificar se o resultado é válido
        resultado_str = str(resultado_final).strip()

        # Verificar se contém palavras problemáticas ou em inglês
        palavras_problematicas = [
            'Thought:', 'I now can give a great answer', 'great answer', 'Final Answer:',
            'I understand', 'Here is', 'The integration', 'While the benefits',
            'However', 'Additionally', 'Moreover', 'Furthermore', 'Nevertheless'
        ]
        tem_problema = any(palavra in resultado_str for palavra in palavras_problematicas)

        # Verificar se tem muito texto em inglês (mais de 20% de palavras comuns em inglês)
        palavras_ingles = ['the', 'and', 'of', 'to', 'in', 'is', 'that', 'with', 'for', 'as', 'are', 'this', 'be', 'development', 'software', 'can', 'has', 'also', 'benefits', 'challenges']
        palavras_texto = resultado_str.lower().split()
        palavras_em_ingles = sum(1 for palavra in palavras_texto if palavra in palavras_ingles)
        percentual_ingles = (palavras_em_ingles / len(palavras_texto)) * 100 if palavras_texto else 0

        if resultado_final and len(resultado_str) > 200 and not tem_problema and percentual_ingles < 20:
            print(resultado_final)
        else:
            print("⚠️ AVISO: Resultado inadequado detectado!")
            print(f"Tamanho: {len(resultado_str)} caracteres")
            print(f"Percentual de inglês: {percentual_ingles:.1f}%")
            print(f"Tem palavras problemáticas: {tem_problema}")
            print(f"Resultado recebido: '{resultado_final}'")
            print("\n💡 Sugestões para resolver:")
            print("1. O modelo pode estar respondendo em inglês por padrão")
            print("2. Tente executar novamente - às vezes funciona na segunda tentativa")
            print("3. Considere usar 'ollama pull mistral' que pode ter melhor suporte ao português")

        print("\n" + "="*50)

    except Exception as e:
        print(f"❌ ERRO na função principal: {e}")
        print("   Por favor, verifique se o Ollama está a rodar (`ollama serve`) e se o modelo foi descarregado (`ollama pull llama3`).")

if __name__ == "__main__":
    run_crewai_ollama_demo()
    print("✅ Script concluído.")