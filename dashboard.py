import streamlit as st
import asyncio
import os
import io
from dotenv import load_dotenv
from database import (
    init_db,
    salvar_lembrete,
    listar_lembretes,
    alternar_status_lembrete,
    excluir_lembrete,
    registrar_consulta,
    listar_historico_consultas
)
from agents import executar_consulta_estrategica
from pdf_generator import gerar_pdf
from notion_sync import exportar_para_notion, is_notion_configurado
from transcriber import transcrever_audio_bytes

load_dotenv()
init_db()

st.set_page_config(
    page_title="SimuladoApp — Mesa Diretora",
    page_icon="🏛️",
    layout="wide",
    initial_sidebar_state="expanded"
)

# Estilização CSS customizada
st.markdown("""
<style>
    .main-header {
        font-size: 2.2rem;
        font-weight: 700;
        color: #F8FAFC;
        margin-bottom: 0.2rem;
    }
    .sub-header {
        font-size: 1.0rem;
        color: #94A3B8;
        margin-bottom: 1.5rem;
    }
    .director-badge {
        display: inline-block;
        padding: 4px 10px;
        border-radius: 6px;
        font-size: 0.85rem;
        font-weight: 600;
        margin-right: 6px;
    }
    .ceo-badge { background-color: #3B82F6; color: white; }
    .cfo-badge { background-color: #10B981; color: white; }
    .cto-badge { background-color: #8B5CF6; color: white; }
    .cpo-badge { background-color: #F59E0B; color: white; }
</style>
""", unsafe_allow_html=True)

# Autenticação Simples
SENHA_CONFIGURADA = os.getenv("DASHBOARD_PASSWORD", "simulado2026")

if "autenticado" not in st.session_state:
    st.session_state["autenticado"] = False

def tela_login():
    st.markdown("<div class='main-header'>🏛️ SimuladoApp — Acesso Executivo</div>", unsafe_allow_html=True)
    st.markdown("<div class='sub-header'>Autenticação restrita para o fundador e diretoria.</div>", unsafe_allow_html=True)
    
    col1, col2, col3 = st.columns([1, 1.5, 1])
    with col2:
        with st.form("login_form"):
            senha = st.text_input("Senha de Acesso", type="password", placeholder="Digite sua senha...")
            submit = st.form_submit_button("Entrar no Painel", use_container_width=True)
            if submit:
                if senha == SENHA_CONFIGURADA:
                    st.session_state["autenticado"] = True
                    st.rerun()
                else:
                    st.error("❌ Senha incorreta.")

if not st.session_state["autenticado"]:
    tela_login()
    st.stop()

# Barra Lateral
with st.sidebar:
    st.title("🏛️ Mesa Diretora")
    st.caption("Conselho Executivo de IA do SimuladoApp")
    
    aba_selecionada = st.radio(
        "Navegação:",
        ["💬 Mesa Redonda (Chat)", "📋 Quadro de Tarefas", "📜 Histórico de Decisões", "👥 Membros do Conselho"]
    )
    
    st.divider()
    st.markdown("**Status do Sistema:**")
    st.success("🟢 8 Agentes Ativos")
    st.info("⚡ LLM: Groq (Llama 3.3 70B)")
    
    if st.button("Sair da Sessão", use_container_width=True):
        st.session_state["autenticado"] = False
        st.rerun()

# ----------------- ABA 1: MESA REDONDA -----------------
if aba_selecionada == "💬 Mesa Redonda (Chat)":
    st.markdown("<div class='main-header'>💬 Mesa Redonda com o Conselho Executivo</div>", unsafe_allow_html=True)
    st.markdown("<div class='sub-header'>Despache uma demanda estratégica para ser analisada e sintetizada pela diretoria.</div>", unsafe_allow_html=True)
    
    col_input, col_preset = st.columns([2.5, 1])
    
    with col_preset:
        st.markdown("**🎯 Destinatário da Demanda:**")
        destinatario = st.selectbox(
            "Com quem deseja despachar?",
            [
                "🏛️ Mesa Completa (Todos os 8)",
                "👑 CEO (Estratégia & Split 33%)",
                "💻 CTO (Tecnologia & Mini-PRD)",
                "💰 CFO (Finanças & DRE)",
                "📈 Growth (Campanhas & Tráfego)",
                "✍️ Conteúdo (Reels & Copy)",
                "🎓 CPO (Pedagógico & UX)",
                "🎧 CS (Retenção & Suporte)",
                "⚖️ Legal (LGPD & Contratos)"
            ]
        )
        
        mapa_destinatario = {
            "🏛️ Mesa Completa (Todos os 8)": None,
            "👑 CEO (Estratégia & Split 33%)": "ceo",
            "💻 CTO (Tecnologia & Mini-PRD)": "cto",
            "💰 CFO (Finanças & DRE)": "cfo",
            "📈 Growth (Campanhas & Tráfego)": "growth",
            "✍️ Conteúdo (Reels & Copy)": "conteudo",
            "🎓 CPO (Pedagógico & UX)": "cpo",
            "🎧 CS (Retenção & Suporte)": "cs",
            "⚖️ Legal (LGPD & Contratos)": "legal"
        }
        agente_alvo = mapa_destinatario[destinatario]
        
        if agente_alvo:
            st.info(f"⚡ Modo Rápido & Econômico: Consulta direta com {destinatario.split('(')[0].strip()}")
        else:
            st.caption("Convocará todo o conselho para um plano integrado.")

        st.divider()
        st.markdown("**Sugestões Rápidas:**")
        preset = st.selectbox(
            "Selecione um briefing pronto:",
            [
                "Personalizado...",
                "Qual a prioridade estratégica e plano de ação para esta semana?",
                "Auditoria financeira do split 33/33/33 e metas de LTV/CAC",
                "Desenho de PRD técnico para otimização de scanner OpenCV",
                "Planejamento de 3 roteiros de Reels focados na dor do fim de semana",
                "Plano de contingência e termos de conformidade LGPD para dados escolares"
            ]
        )
    
    with col_input:
        demanda_padrao = "" if preset == "Personalizado..." else preset
        
        # Entrada de áudio por microfone ou upload
        tab_mic, tab_up = st.tabs(["🎙️ Gravar Microfone", "📁 Enviar Arquivo de Áudio"])
        
        with tab_mic:
            gravacao_audio = st.audio_input("Grave sua fala diretamente:")
            if gravacao_audio is not None:
                if "audio_processado" not in st.session_state or st.session_state.get("ultimo_audio_nome") != gravacao_audio.name:
                    with st.spinner("🎙️ Transcrevendo áudio via Whisper Large v3..."):
                        try:
                            bytes_audio = gravacao_audio.read()
                            texto_transcrito = transcrever_audio_bytes(bytes_audio, nome_arquivo=gravacao_audio.name or "audio.wav")
                            st.session_state["texto_audio"] = texto_transcrito
                            st.session_state["ultimo_audio_nome"] = gravacao_audio.name
                            st.success(f"🗣️ Transcrição: \"{texto_transcrito}\"")
                        except Exception as e:
                            st.error(f"Erro ao transcrever áudio: {e}")
        
        with tab_up:
            arquivo_subido = st.file_uploader("Ou envie um áudio gravado (.mp3, .m4a, .wav, .ogg, .oga):", type=["mp3", "m4a", "wav", "ogg", "oga"])
            if arquivo_subido is not None:
                if st.session_state.get("ultimo_up_nome") != arquivo_subido.name:
                    with st.spinner("🎙️ Transcrevendo áudio via Whisper..."):
                        try:
                            bytes_up = arquivo_subido.read()
                            texto_up = transcrever_audio_bytes(bytes_up, nome_arquivo=arquivo_subido.name)
                            st.session_state["texto_audio"] = texto_up
                            st.session_state["ultimo_up_nome"] = arquivo_subido.name
                            st.success(f"🗣️ Transcrição: \"{texto_up}\"")
                        except Exception as e:
                            st.error(f"Erro ao transcrever: {e}")

        valor_inicial = st.session_state.get("texto_audio", demanda_padrao)
        demanda = st.text_area(
            "Descreva a demanda para a Mesa Diretora:",
            value=valor_inicial,
            height=110,
            placeholder="Ex: Preciso de um plano para reduzir o churn da assinatura de R$ 4,99..."
        )
        label_btn = f"🚀 Enviar para {destinatario.split('(')[0].strip()}"
        btn_executar = st.button(label_btn, type="primary", use_container_width=True)

    if btn_executar and demanda.strip():
        msg_spinner = f"⏳ Consultando {destinatario.split('(')[0].strip()}..."
        with st.spinner(msg_spinner):
            try:
                loop = asyncio.new_event_loop()
                asyncio.set_event_loop(loop)
                resultado = loop.run_until_complete(executar_consulta_estrategica(demanda, agentes_alvo=agente_alvo))
                loop.close()
                
                resultado_str = str(resultado)
                canal_tag = f"Dashboard Web ({destinatario.split('(')[0].strip()})"
                registrar_consulta(canal_tag, demanda, resultado_str)
                st.session_state["ultimo_resultado"] = resultado_str
                st.session_state["ultima_demanda"] = demanda
                st.success("✅ Resposta gerada com sucesso!")
            except Exception as e:
                st.error(f"⚠️ Erro ao processar com os agentes: {e}")
                st.error(f"⚠️ Erro ao processar com os agentes: {e}")

    # Exibe o último resultado gerado
    if "ultimo_resultado" in st.session_state:
        st.divider()
        res = st.session_state["ultimo_resultado"]
        dem = st.session_state["ultima_demanda"]
        
        st.subheader("📄 Síntese Executiva da Reunião")
        st.markdown(f"**Demanda original:** *{dem}*")
        
        # Ações de Exportação
        col_exp1, col_exp2, col_exp3 = st.columns(3)
        
        with col_exp1:
            st.download_button(
                label="📥 Baixar como Markdown (.md)",
                data=res,
                file_name="plano_executivo_simuladoapp.md",
                mime="text/markdown",
                use_container_width=True
            )
            
        with col_exp2:
            try:
                caminho_pdf = gerar_pdf(res, dem)
                with open(caminho_pdf, "rb") as f_pdf:
                    bytes_pdf = f_pdf.read()
                st.download_button(
                    label="📄 Baixar Relatório em PDF",
                    data=bytes_pdf,
                    file_name="relatorio_executivo_simuladoapp.pdf",
                    mime="application/pdf",
                    use_container_width=True
                )
                if os.path.exists(caminho_pdf):
                    os.remove(caminho_pdf)
            except Exception as ex:
                st.warning(f"PDF indisponível no momento: {ex}")
                
        with col_exp3:
            if st.button("🚀 Sincronizar com Notion", use_container_width=True):
                with st.spinner("Enviando para o Notion..."):
                    resp_notion = exportar_para_notion(dem, res)
                    if resp_notion["sucesso"]:
                        st.success(f"Página criada no Notion! [Abrir Página]({resp_notion['url']})")
                    else:
                        st.warning(resp_notion["mensagem"])

        # Exibição do Conteúdo Formatado
        st.markdown(res)

# ----------------- ABA 2: QUADRO DE TAREFAS -----------------
elif aba_selecionada == "📋 Quadro de Tarefas":
    st.markdown("<div class='main-header'>📋 Quadro de Lembretes & Tarefas</div>", unsafe_allow_html=True)
    st.markdown("<div class='sub-header'>Gerencie seus lembretes estratégicos sincronizados com o Telegram.</div>", unsafe_allow_html=True)
    
    with st.expander("➕ Adicionar Novo Lembrete / Tarefa"):
        with st.form("form_tarefa"):
            novo_texto = st.text_input("Descrição da Tarefa:")
            btn_add = st.form_submit_button("Salvar Tarefa")
            if btn_add and novo_texto.strip():
                salvar_lembrete(novo_texto.strip())
                st.success("Tarefa salva com sucesso!")
                st.rerun()

    filtro = st.radio("Filtrar por:", ["Pendente", "Concluído", "Todos"], horizontal=True)
    mapa_filtro = {"Pendente": "pendente", "Concluído": "concluido", "Todos": "todos"}
    
    itens = listar_lembretes(mapa_filtro[filtro])
    
    if not itens:
        st.info("Nenhuma tarefa encontrada neste status.")
    else:
        for item_id, texto, status, data_criacao in itens:
            col_t1, col_t2, col_t3 = st.columns([4, 1.2, 0.8])
            with col_t1:
                if status == "concluido":
                    st.markdown(f"~~**[{item_id}]** {texto}~~ <small>({data_criacao})</small>", unsafe_allow_html=True)
                else:
                    st.markdown(f"📌 **[{item_id}]** {texto} <br><small style='color:gray;'>Registrado em: {data_criacao}</small>", unsafe_allow_html=True)
            with col_t2:
                novo_st = "pendente" if status == "concluido" else "concluido"
                btn_txt = "↩️ Reabrir" if status == "concluido" else "✅ Concluir"
                if st.button(btn_txt, key=f"status_{item_id}", use_container_width=True):
                    alternar_status_lembrete(item_id, novo_st)
                    st.rerun()
            with col_t3:
                if st.button("🗑️", key=f"del_{item_id}", use_container_width=True):
                    excluir_lembrete(item_id)
                    st.rerun()
            st.divider()

# ----------------- ABA 3: HISTÓRICO DE DECISÕES -----------------
elif aba_selecionada == "📜 Histórico de Decisões":
    st.markdown("<div class='main-header'>📜 Histórico de Deliberações</div>", unsafe_allow_html=True)
    st.markdown("<div class='sub-header'>Linha do tempo de todas as decisões e despachos emitidos pela Mesa Diretora.</div>", unsafe_allow_html=True)
    
    historico = listar_historico_consultas(limite=50)
    
    if not historico:
        st.info("Nenhum histórico registrado até o momento.")
    else:
        for h_id, canal, demanda, resposta, data_reg in historico:
            with st.expander(f"🕒 [{data_reg}] [{canal}] {demanda[:80]}..."):
                st.markdown(f"**Canal de Origem:** `{canal}` | **Data:** `{data_reg}`")
                st.markdown(f"**Demanda Completa:**\n> {demanda}")
                st.divider()
                st.markdown("**Parecer da Diretoria:**")
                st.markdown(resposta)

# ----------------- ABA 4: MEMBROS DO CONSELHO -----------------
elif aba_selecionada == "👥 Membros do Conselho":
    st.markdown("<div class='main-header'>👥 Composição do Conselho Executivo</div>", unsafe_allow_html=True)
    st.markdown("<div class='sub-header'>Conheça os 8 diretores especialistas autônomos dedicados ao SimuladoApp.</div>", unsafe_allow_html=True)
    
    membros = [
        ("👑 CEO & Estrategista Chefe", "Escala enxuta, métricas unitárias e governança do Split 33/33/33.", "Alex Hormozi, Eric Ries, Brian Chesky"),
        ("💻 CTO & Arquiteto Tech", "Arquitetura Python/Django, MySQL, Celery e Visão Computacional OpenCV.", "John Carmack, Martin Fowler, Kelsey Hightower"),
        ("🎓 CPO & Especialista Pedagógico", "UX/UI em sala de aula, alinhamento BNCC/SAEB e TTFV < 5min.", "Salman Khan, Tony Fadell, Julie Zhuo"),
        ("💰 CFO & Controller Financeiro", "Unit Economics, liquidez, conciliação quinzenal e proteção de caixa.", "Warren Buffett, Ray Dalio, David Sacks"),
        ("🎧 Head de CS & Suporte", "Encantamento, redução de churn < 5% e scripts humanizados de WhatsApp.", "Tony Hsieh, Nick Mehta"),
        ("⚖️ Consultor Jurídico & DPO", "LGPD escolar, compliance, proteção da marca no INPI e contratos SaaS.", "Brad Smith, Ann Cavoukian"),
        ("✍️ Head de Conteúdo & Copywriter", "Comunidade 'Devolve seus fins de semana' e roteiros de Reels/Shorts.", "GaryVee, Nicolas Cole, Ann Handley"),
        ("📈 Head de Growth & Performance", "Aquisição com CPL <= R$ 0,75, campanhas Meta Ads e sazonalidade escolar.", "Sean Ellis, Russell Brunson, David Ogilvy")
    ]
    
    cols = st.columns(2)
    for i, (cargo, missao, inspiracoes) in enumerate(membros):
        with cols[i % 2]:
            with st.container(border=True):
                st.subheader(cargo)
                st.markdown(f"**Missão:** {missao}")
                st.caption(f"🧠 **Mentalidade de Referência:** {inspiracoes}")
