import os
import sys
from dotenv import load_dotenv

# Importações Padrão
from agentCore.providers import get_llm
from agentCore.logger import get_logger
from crewai import Agent, Task, Crew, Process
from langchain_ollama import ChatOllama
from agentCore.evaluation import PromptEvaluator

load_dotenv()

# Desabilitar traces online do CrewAI
os.environ["CREWAI_TELEMETRY_ENABLED"] = "false"

logger = get_logger("crewai_ollama_demo")

def criar_e_executar_time_ia(llm_instance):
    pesquisador = Agent(
        role='Pesquisador Sênior de IA',
        goal='Encontrar os desenvolvimentos e impactos mais recentes da IA no desenvolvimento de software',
        backstory="Você é um pesquisador experiente, mestre em encontrar informações complexas e destilar os pontos-chave. SEMPRE responda em português brasileiro.",
        verbose=True,
        allow_delegation=False,
        llm=llm_instance,
    )
    escritor = Agent(
        role='Escritor Técnico Especialista',
        goal='Criar um relatório claro, conciso e informativo sobre o impacto da IA no desenvolvimento de software',
        backstory="Você é um escritor renomado por transformar dados técnicos em narrativas envolventes para executivos. SEMPRE escreva em português brasileiro.",
        verbose=True,
        allow_delegation=False,
        llm=llm_instance,
    )
    tarefa_pesquisa = Task(
        description=("1. Pesquise as principais maneiras pelas quais a IA está mudando o ciclo de vida do desenvolvimento de software (SDLC).\n"
                     "2. Identifique 3 a 5 ferramentas de IA populares que desenvolvedores estão usando hoje.\n"
                     "3. Analise tanto os benefícios (ex: produtividade) quanto os desafios (ex: qualidade do código, segurança).\n"
                     "4. Compile suas descobertas em notas detalhadas para o escritor.\n"
                     "IMPORTANTE: Responda sempre em português brasileiro."),
        expected_output='Um boletim com os pontos principais, exemplos de ferramentas e uma análise de prós e contras.',
        agent=pesquisador,
    )
    tarefa_escrita = Task(
        description=("USANDO O CONTEXTO FORNECIDO, que contém as notas detalhadas de um pesquisador, siga estes passos:\n"
                     "1. Escreva um relatório de 2 parágrafos sobre o impacto da IA no desenvolvimento de software.\n"
                     "2. O relatório deve ser direcionado a um público de gestão (executivos, diretores), evitando jargões muito técnicos.\n"
                     "3. Comece com um resumo do impacto geral, depois detalhe os benefícios e desafios encontrados no contexto.\n"
                     "4. Finalize com uma conclusão sobre o futuro do desenvolvimento de software com IA.\n"
                     "NÃO use ferramentas. Toda a informação de que precisa está no contexto.\n"
                     "IMPORTANTE: Escreva sempre em português brasileiro."),
        expected_output='Um relatório bem estruturado em formato markdown, baseado unicamente nas notas da pesquisa fornecidas.',
        agent=escritor,
        context=[tarefa_pesquisa]
    )
    time_de_ia = Crew(
        agents=[pesquisador, escritor],
        tasks=[tarefa_pesquisa, tarefa_escrita],
        process=Process.sequential,
        verbose=True
    )
    logger.progress(f"🚀 A executar o time de agentes com o modelo: {getattr(llm_instance, 'model', 'unknown')}...")
    resultado = time_de_ia.kickoff()
    return resultado

def demo_model_comparison():
    logger.info("⚔️ Iniciando Demo de Comparação de Modelos")
    modelos_para_comparar = ["llama3", "mistral"]
    resultados_por_modelo = []
    base_url = os.getenv("OLLAMA_BASE_URL", "http://localhost:11434")

    for nome_modelo in modelos_para_comparar:
        print("\n" + "="*50)
        logger.info(f"⚙️ A preparar a execução para o modelo: {nome_modelo}")
        
        # Criamos uma instância especial do LLM para o CrewAI com o prefixo
        llm_para_crewai = ChatOllama(model=f"ollama/{nome_modelo}", base_url=base_url)
        
        # Executamos o time com esta instância especial
        resultado = criar_e_executar_time_ia(llm_para_crewai)
        
        print(f"\n📄 Relatório Gerado por '{nome_modelo}':\n{resultado}")
        
        resultados_por_modelo.append({
            "provider": nome_modelo,
            "prompt": "Gerar um relatório sobre o impacto da IA no desenvolvimento de software.",
            "actual": resultado
        })

    logger.info("⚖️ A comparar os resultados gerados...")
    
    # O avaliador usará o get_llm() padrão, que agora está corrigido e não usa o prefixo.
    # Ele usará o modelo definido em OLLAMA_MODEL ou o padrão 'llama3' para julgar.
    os.environ['OLLAMA_MODEL'] = 'llama3' # Usamos sempre o mesmo juiz
    evaluator = PromptEvaluator(llm_provider="ollama")
    scores = {}

    for res in resultados_por_modelo:
        avaliacao = evaluator.evaluate_single(
            prompt=f"Você é um especialista em tecnologia. Avalie a qualidade e clareza do seguinte relatório numa escala de 0.0 a 1.0. Relatório: '{res['actual']}'",
            expected=("Um relatório excelente, conciso e bem estruturado sobre o impacto da IA no SDLC, "
                      "mencionando ferramentas, benefícios e desafios, com uma linguagem clara para executivos."),
            eval_type="semantic_similarity"
        )
        scores[res['provider']] = avaliacao.score

    print("\n" + "="*50)
    logger.success("⚔️ Resultado da Comparação ⚔️")
    print("="*50)
    for modelo, score in scores.items():
        print(f"🎖️ Modelo: {modelo:<10} | Score: {score:.2f}")
    
    melhor_modelo = max(scores, key=scores.get)
    print(f"\n🏆 Melhor Modelo para esta tarefa: {melhor_modelo.upper()}")
    print("="*50)

if __name__ == "__main__":
    demo_model_comparison()
    print("✅ Script concluído.")