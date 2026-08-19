import os
from dotenv import load_dotenv

os.environ["OTEL_SDK_DISABLED"] = "true"
os.environ["CREWAI_TELEMETRY_OPT_OUT"] = "true"

from crewai import Agent, Task, Crew, Process, LLM
import litellm
from database import obter_configuracoes_agentes

load_dotenv()
litellm.drop_params = True

# Configuração com o provedor Groq
groq_api_key = os.getenv("GROQ_API_KEY")
os.environ["GROQ_API_KEY"] = groq_api_key
os.environ["OPENAI_API_KEY"] = groq_api_key
os.environ["OPENAI_API_BASE"] = "https://api.groq.com/openai/v1"

def criar_llm():
    return LLM(
        model="openai/openai/gpt-oss-20b",
        api_key=groq_api_key,
        base_url="https://api.groq.com/openai/v1",
        temperature=0.3,
        max_tokens=2500
    )

def instanciar_agentes():
    """Instancia os 8 agentes com base nas diretrizes ativas salvas no banco de dados."""
    configs = obter_configuracoes_agentes()
    llm_instance = criar_llm()
    
    agentes = {}
    icones = {
        "ceo": "👑",
        "cto": "💻",
        "cpo": "🎓",
        "conteudo": "✍️",
        "growth": "📈",
        "cfo": "💰",
        "cs": "🎧",
        "legal": "⚖️"
    }
    
    for chave, dados in configs.items():
        agente = Agent(
            role=f"{dados['cargo']} do SimuladoApp",
            goal=dados['meta'],
            backstory=dados['diretrizes'],
            llm=llm_instance,
            verbose=False,
            allow_delegation=(chave == "ceo")
        )
        agentes[chave] = (agente, f"{icones.get(chave, '👔')} {dados['cargo']}")
        
    return agentes

MAPA_NOMES_ICONES = {
    "ceo": "👑 CEO & Estrategista Chefe",
    "cto": "💻 CTO & Arquiteto Tech",
    "cpo": "🎓 CPO & Especialista Pedagógico",
    "conteudo": "✍️ Head de Conteúdo & Social Media",
    "growth": "📈 Head de Growth & Tráfego",
    "cfo": "💰 CFO & Controller Financeiro",
    "cs": "🎧 Head de CS & Suporte",
    "legal": "⚖️ Consultor Jurídico & Compliance",
}

def normalizar_agente(nome: str) -> str:
    nome_clean = nome.lower().replace("@", "").replace("/", "").strip()
    if nome_clean in ["tech", "dev", "ti", "arquitetura"]:
        return "cto"
    if nome_clean in ["produto", "pedagogico", "pedagógico", "ux"]:
        return "cpo"
    if nome_clean in ["marketing", "trafego", "tráfego", "ads"]:
        return "growth"
    if nome_clean in ["reels", "copy", "redes", "social"]:
        return "conteudo"
    if nome_clean in ["financeiro", "financas", "finanças", "split"]:
        return "cfo"
    if nome_clean in ["suporte", "operacoes", "operações", "retencao", "retenção"]:
        return "cs"
    if nome_clean in ["juridico", "jurídico", "lgpd", "compliance", "dpo"]:
        return "legal"
    return nome_clean

async def executar_consulta_estrategica(demanda_usuario: str, agentes_alvo: list[str] | str | None = None) -> str:
    """
    Executa a demanda com os agentes selecionados ou com toda a Mesa Diretora.
    Carrega dinamicamente as diretrizes customizadas pelo fundador.
    """
    mapa_agentes = instanciar_agentes()
    
    # Normalização de agentes_alvo
    if isinstance(agentes_alvo, str):
        agentes_alvo = [agentes_alvo]
        
    if agentes_alvo:
        agentes_normalizados = [normalizar_agente(a) for a in agentes_alvo if normalizar_agente(a) in mapa_agentes]
    else:
        agentes_normalizados = []

    # CASO 1: Consulta individual direta (Ultra econômico em tokens - 1 único agente)
    if len(agentes_normalizados) == 1:
        chave = agentes_normalizados[0]
        agente_escolhido, titulo_agente = mapa_agentes[chave]
        
        if chave == "ceo":
            desc_tarefa = (
                f"Reunião 1-a-1 confidencial e estratégica diretamente com o fundador do SimuladoApp.\n\n"
                f"Demanda / Ideia do Fundador: \"{demanda_usuario}\"\n\n"
                f"Como CEO & Co-fundador Executivo:\n"
                f"- Faça um sparring estratégico rigoroso (visão Hormozi, Lean e SaaS unit economics).\n"
                f"- Dê feedbacks honestos sobre a viabilidade, riscos e pontos cegos.\n"
                f"- Ajude a lapidar a ideia e sugira como direcionar a demanda para os outros diretores (CTO, Growth, CFO, etc.) quando estiver pronta."
            )
            out_esperado = "Feedback estratégico 1-a-1 executivo, direto e construtivo do CEO."
        else:
            desc_tarefa = (
                f"O fundador solicitou uma demanda direta para o seu cargo ({titulo_agente}):\n\n"
                f"\"{demanda_usuario}\"\n\n"
                f"Responda diretamente e de forma especializada como {titulo_agente}, sem rodeios, "
                f"entregando o formato técnico/específico da sua área (ex: Mini-PRD para CTO, Roteiro para Conteúdo, DRE para CFO)."
            )
            out_esperado = f"Parecer e entregável especializado direto do {titulo_agente}."

        tarefa_direta = Task(
            description=desc_tarefa,
            expected_output=out_esperado,
            agent=agente_escolhido
        )
        
        tripulacao = Crew(
            agents=[agente_escolhido],
            tasks=[tarefa_direta],
            process=Process.sequential,
            verbose=False
        )
        resultado = await tripulacao.kickoff_async()
        return f"**[{titulo_agente}]**\n\n{str(resultado)}"

    # CASO 2: Consulta a um subgrupo específico de agentes (ex: CTO + CFO)
    elif len(agentes_normalizados) > 1 and len(agentes_normalizados) < len(mapa_agentes):
        agentes_objs = [mapa_agentes[k][0] for k in agentes_normalizados]
        titulos = ", ".join([mapa_agentes[k][1] for k in agentes_normalizados])
        ceo_obj = mapa_agentes["ceo"][0]
        
        tarefa_subgrupo = Task(
            description=(
                f"Demanda do fundador: '{demanda_usuario}'.\n\n"
                f"Especialistas convocados: {titulos}.\n"
                f"Cada especialista deve fornecer sua contribuição direta e o CEO/Líder deve consolidar um plano rápido."
            ),
            expected_output="Parecer integrado dos especialistas convocados.",
            agent=ceo_obj
        )
        
        tripulacao = Crew(
            agents=agentes_objs,
            tasks=[tarefa_subgrupo],
            process=Process.sequential,
            verbose=False
        )
        resultado = await tripulacao.kickoff_async()
        return str(resultado)

    # CASO 3: Mesa Completa (Conselho Geral com todos os 8 agentes)
    else:
        ceo_obj = mapa_agentes["ceo"][0]
        todos_agentes = [ag[0] for ag in mapa_agentes.values()]
        
        tarefa_ceo = Task(
            description=(
                f"O fundador solicitou a seguinte demanda estratégica: '{demanda_usuario}'.\n\n"
                f"Como CEO & Orquestrador da Mesa Diretora, convoque as perspectivas necessárias dos 8 diretores "
                f"e consolide a resposta estritamente no seguinte padrão executivo:\n"
                f"1. **Veredito Executivo & Direcionamento Geral** (Alinhamento global e split societário 33/33/33)\n"
                f"2. **Contribuição dos Especialistas Convocados** (Mini-PRD do CTO, UX do CPO, Campanhas Growth, Roteiro Conteúdo, Scripts CS, DRE CFO ou Parecer Legal)\n"
                f"3. **Plano de Ação Tático: O que Você (Fundador) Deve Fazer** (Ações práticas e decisões humanas)\n"
                f"4. **Automações & Regras Internas** (Gatilhos de sistema, rotinas e queries)\n"
                f"5. **Alerta de Riscos & Mitigações**"
            ),
            expected_output="Plano Executivo Consolidado objetivo e direto em 5 seções estruturadas.",
            agent=ceo_obj
        )
        
        conselho = Crew(
            agents=todos_agentes,
            tasks=[tarefa_ceo],
            process=Process.sequential,
            verbose=False
        )
        resultado = await conselho.kickoff_async()
        return str(resultado)