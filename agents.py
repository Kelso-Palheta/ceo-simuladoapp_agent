import os
from dotenv import load_dotenv

os.environ["OTEL_SDK_DISABLED"] = "true"
os.environ["CREWAI_TELEMETRY_OPT_OUT"] = "true"

from crewai import Agent, Task, Crew, Process, LLM
import litellm

load_dotenv()
litellm.drop_params = True

# Configuração com o provedor Groq
groq_api_key = os.getenv("GROQ_API_KEY")
os.environ["GROQ_API_KEY"] = groq_api_key
os.environ["OPENAI_API_KEY"] = groq_api_key
os.environ["OPENAI_API_BASE"] = "https://api.groq.com/openai/v1"

llm = LLM(
    model="openai/openai/gpt-oss-20b",
    api_key=groq_api_key,
    base_url="https://api.groq.com/openai/v1",
    temperature=0.3,
    max_tokens=2500
)

# 1. Agente CEO & Estrategista Chefe
ceo_agent = Agent(
    role="CEO & Estrategista Chefe do SimuladoApp",
    goal=(
        "Orquestrar o Conselho Executivo do SimuladoApp, assegurar a governança rigorosa do Split Societário "
        "(33,33% Sócio 1 / 33,33% Sócio 2 / 33,33% Caixa PJ), proteger a liquidez e entregar planos em 5 seções."
    ),
    backstory=(
        "Você é o CEO do SimuladoApp. Mentalidade: Alex Hormozi (escala enxuta), Eric Ries (Lean) e David Sacks (SaaS unit economics). "
        "Modelo de Negócio: Gratuito 15 correções/mês, Assinatura R$ 4,99/mês, Pacotes P/M/G vitalícios e Split 33/33/33 inegociável. "
        "Métricas: TTFV < 5min, CAC Pago <= R$ 15,00, CPL <= R$ 0,75, Margem > 80% e Payback imediato no Pix."
    ),
    llm=llm,
    verbose=False,
    allow_delegation=True
)

# 2. Agente CTO & Arquiteto Tech
cto_agent = Agent(
    role="CTO & Arquiteto Tech do SimuladoApp",
    goal="Entregar Mini-PRDs Técnicos de produção em Django/MySQL, otimizar pipeline OpenCV (<1s latência, >98% precisão) e Celery/Redis.",
    backstory="Você é o CTO do SimuladoApp. Mentalidade John Carmack (performance máxima) e Martin Fowler (Clean Architecture). Blindagem de queries MySQL sem N+1 e segurança LGPD de dados escolares.",
    llm=llm,
    verbose=False
)

# 3. Agente CPO & Especialista Pedagógico
cpo_agent = Agent(
    role="CPO & Diretor Pedagógico do SimuladoApp",
    goal="Garantir UX docente sem atrito (< 3 cliques), alinhamento estrito à BNCC/SAEB e relatórios formativos de 1 página.",
    backstory="Você é o CPO do SimuladoApp. Mentalidade Salman Khan e Tony Fadell. Foco na rotina sobrecarregada do professor para garantir TTFV < 5 minutos.",
    llm=llm,
    verbose=False
)

# 4. Agente Head de Conteúdo & Social Media
conteudo_agent = Agent(
    role="Head de Conteúdo & Social Media do SimuladoApp",
    goal="Criar roteiros magnéticos de Reels/Shorts em 3 atos (Hook 3s, Desenvolvimento, CTA) focados no alívio: 'O SimuladoApp devolve seus finais de semana'.",
    backstory="Você é o Head de Conteúdo. Mentalidade GaryVee e Nicolas Cole. Copywriting autêntico, zero jargão corporativo e apelo emocional direto ao cansaço de correção de provas.",
    llm=llm,
    verbose=False
)

# 5. Agente Head de Growth & Tráfego Pago
growth_agent = Agent(
    role="Head de Growth & Tráfego Pago do SimuladoApp",
    goal="Desenhar campanhas Meta Ads com CPL <= R$ 0,75, CAC Pago <= R$ 15,00, ROAS >= 3.5x e alocação dinâmica nos picos bimestrais (abril, junho, set, nov).",
    backstory="Você é o Head de Growth. Mentalidade Sean Ellis e Russell Brunson. Domínio da Conversion API (CAPI), testes A/B de criativos e regras de corte estritas para CPL > R$ 1,50.",
    llm=llm,
    verbose=False
)

# 6. Agente CFO & Controller Financeiro
cfo_agent = Agent(
    role="CFO & Controller Financeiro do SimuladoApp",
    goal="Auditar o Split 33/33/33, conciliação quinzenal, monitorar taxas de gateway Pix e garantir reserva de segurança de 3 meses de custos fixos.",
    backstory="Você é o CFO do SimuladoApp. Mentalidade Warren Buffett e Ray Dalio. Guardião da liquidez e do DRE de SaaS.",
    llm=llm,
    verbose=False
)

# 7. Agente Head de CS & Suporte
cs_agent = Agent(
    role="Head de CS & Retenção do SimuladoApp",
    goal="Manter churn < 5%, régua D+0/D+1 humanizada no WhatsApp e operar o gatilho de upsell para Pacote M quando o saldo for <= 15%.",
    backstory="Você é o Head de CS. Mentalidade Tony Hsieh (Zappos). Suporte ágil para gabaritos e resolução rápida de dúvidas de câmera.",
    llm=llm,
    verbose=False
)

# 8. Agente Consultor Jurídico & Compliance
legal_agent = Agent(
    role="Consultor Jurídico, DPO e Compliance do SimuladoApp",
    goal="Blindagem LGPD escolar (dados de menores, SimuladoApp como Operador), Termos de Uso de SaaS, INPI e Acordo de Sócios 33/33/33.",
    backstory="Você é o DPO do SimuladoApp. Mentalidade Brad Smith e Ann Cavoukian (Privacy by Design). Contratos ágeis para edtech.",
    llm=llm,
    verbose=False
)

MAPA_AGENTES = {
    "ceo": (ceo_agent, "👑 CEO & Estrategista Chefe"),
    "cto": (cto_agent, "💻 CTO & Arquiteto Tech"),
    "cpo": (cpo_agent, "🎓 CPO & Especialista Pedagógico"),
    "conteudo": (conteudo_agent, "✍️ Head de Conteúdo & Social Media"),
    "growth": (growth_agent, "📈 Head de Growth & Tráfego"),
    "cfo": (cfo_agent, "💰 CFO & Controller Financeiro"),
    "cs": (cs_agent, "🎧 Head de CS & Suporte"),
    "legal": (legal_agent, "⚖️ Consultor Jurídico & Compliance"),
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
    Permite economia drástica de tokens ao falar direto com 1 ou poucos especialistas.
    """
    # Normalização de agentes_alvo
    if isinstance(agentes_alvo, str):
        agentes_alvo = [agentes_alvo]
        
    if agentes_alvo:
        agentes_normalizados = [normalizar_agente(a) for a in agentes_alvo if normalizar_agente(a) in MAPA_AGENTES]
    else:
        agentes_normalizados = []

    # CASO 1: Consulta individual direta (Ultra econômico em tokens - 1 único agente)
    if len(agentes_normalizados) == 1:
        chave = agentes_normalizados[0]
        agente_escolhido, titulo_agente = MAPA_AGENTES[chave]
        
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
    elif len(agentes_normalizados) > 1 and len(agentes_normalizados) < len(MAPA_AGENTES):
        agentes_objs = [MAPA_AGENTES[k][0] for k in agentes_normalizados]
        titulos = ", ".join([MAPA_AGENTES[k][1] for k in agentes_normalizados])
        
        tarefa_subgrupo = Task(
            description=(
                f"Demanda do fundador: '{demanda_usuario}'.\n\n"
                f"Especialistas convocados: {titulos}.\n"
                f"Cada especialista deve fornecer sua contribuição direta e o CEO/Líder deve consolidar um plano rápido."
            ),
            expected_output="Parecer integrado dos especialistas convocados.",
            agent=ceo_agent
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
            agent=ceo_agent
        )
        
        conselho = Crew(
            agents=[ceo_agent, cto_agent, cpo_agent, cfo_agent, cs_agent, legal_agent, conteudo_agent, growth_agent],
            tasks=[tarefa_ceo],
            process=Process.sequential,
            verbose=False
        )
        resultado = await conselho.kickoff_async()
        return str(resultado)