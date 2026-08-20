import streamlit as st
import asyncio
import os
from database import (
    init_db,
    salvar_lembrete,
    listar_lembretes,
    alternar_status_lembrete,
    excluir_lembrete,
    registrar_consulta,
    listar_historico_consultas
)
from agents import executar_consulta_estrategica, MAPA_AGENTES
from pdf_generator import gerar_pdf
from notion_sync import criar_pagina_deliberacao
from transcriber import transcrever_audio_bytes
from document_reader import extrair_texto_documento

# Configuração da Página
st.set_page_config(
    page_title="SimuladoApp | Mesa Diretora Executiva",
    page_icon="🏛️",
    layout="wide",
    initial_sidebar_state="expanded"
)

# Inicializa Banco de Dados
init_db()

# Senha de proteção
DASHBOARD_PASSWORD = os.getenv("DASHBOARD_PASSWORD", "simulado2026")

# Estilização CSS Customizada (Dark Slate Executive Theme)
st.markdown("""
<style>
    .main-header {
        font-size: 2.2rem;
        font-weight: 700;
        color: #1E293B;
        margin-bottom: 0.2rem;
    }
    .sub-header {
        font-size: 1.05rem;
        color: #64748B;
        margin-bottom: 1.5rem;
    }
    .card-metric {
        background-color: #F8FAFC;
        border: 1px solid #E2E8F0;
        border-radius: 8px;
        padding: 16px;
        margin-bottom: 12px;
    }
    .stButton>button {
        border-radius: 6px;
        font-weight: 600;
    }
</style>
""", unsafe_allow_html=True)

import hashlib

# ----------------- CONTROLE DE ACESSO COM PERSISTÊNCIA -----------------
def gerar_token_auth(senha: str) -> str:
    return hashlib.sha256(f"simulado_exec_{senha}".encode()).hexdigest()[:16]

TOKEN_CORRETO = gerar_token_auth(DASHBOARD_PASSWORD)

if "autenticado" not in st.session_state:
    st.session_state["autenticado"] = False

# Auto-login se o token estiver presente nos query params da URL
if not st.session_state["autenticado"]:
    token_url = st.query_params.get("auth")
    if token_url == TOKEN_CORRETO:
        st.session_state["autenticado"] = True

if not st.session_state["autenticado"]:
    st.markdown("<div class='main-header'>🏛️ SimuladoApp — Acesso Executivo</div>", unsafe_allow_html=True)
    st.markdown("<div class='sub-header'>Painel de Governança e Inteligência do Conselho de Diretores.</div>", unsafe_allow_html=True)
    
    col_l1, col_l2, col_l3 = st.columns([1, 1.5, 1])
    with col_l2:
        with st.form("form_login"):
            senha_digitada = st.text_input("Chave de Acesso da Mesa Diretora:", type="password")
            btn_entrar = st.form_submit_button("Entrar no Painel Executivo", use_container_width=True)
            
            if btn_entrar:
                if senha_digitada == DASHBOARD_PASSWORD:
                    st.session_state["autenticado"] = True
                    st.query_params["auth"] = TOKEN_CORRETO
                    st.success("Acesso autorizado com sucesso!")
                    st.rerun()
                else:
                    st.error("Chave de acesso incorreta.")
    st.stop()

# ----------------- SIDEBAR DE NAVEGAÇÃO -----------------
with st.sidebar:
    st.title("🏛️ SimuladoApp")
    st.caption("Conselho Executivo de IA")
    
    aba_selecionada = st.radio(
        "Navegação:",
        [
            "💬 Mesa Redonda (Chat)",
            "📋 Quadro de Tarefas",
            "📜 Histórico de Decisões",
            "👥 Membros do Conselho"
        ]
    )
    
    st.divider()
    st.caption("⚡ **Split Societário:** 33,33% S1 / 33,33% S2 / 33,33% Caixa")
    st.caption("🎯 **North Star:** TTFV < 5min | Margem > 80%")
    
    if st.button("Sair da Sessão", use_container_width=True):
        st.session_state["autenticado"] = False
        st.query_params.clear()
        st.rerun()

# ----------------- ABA 1: MESA REDONDA -----------------
if aba_selecionada == "💬 Mesa Redonda (Chat)":
    st.markdown("<div class='main-header'>💬 Mesa Redonda com o Conselho Executivo</div>", unsafe_allow_html=True)
    st.markdown("<div class='sub-header'>Despache demandas estratégicas, alinhe teses 1-a-1 com o CEO ou peça revisões de documentos.</div>", unsafe_allow_html=True)
    
    col_input, col_preset = st.columns([2.5, 1])
    
    with col_preset:
        st.markdown("**🎯 Destinatário da Demanda:**")
        destinatario = st.selectbox(
            "Com quem deseja despachar?",
            [
                "🏛️ Mesa Completa (Todos os 8)",
                "👑 CEO (Estratégia & Decisões)",
                "💻 Tecnologia (CTO - Dev & Sistema)",
                "💰 Financeiro (CFO - Caixa & Split)",
                "🎧 Suporte (CS - Atendimento & Alunos)",
                "📈 Tráfego & Marketing (Growth - Ads)",
                "✍️ Conteúdo (Roteiros & Redes)",
                "🎓 Pedagógico & Produto (CPO - BNCC)",
                "⚖️ Jurídico & Compliance (Legal - LGPD)"
            ]
        )
        
        mapa_destinatario = {
            "🏛️ Mesa Completa (Todos os 8)": None,
            "👑 CEO (Estratégia & Decisões)": "ceo",
            "💻 Tecnologia (CTO - Dev & Sistema)": "cto",
            "💰 Financeiro (CFO - Caixa & Split)": "cfo",
            "🎧 Suporte (CS - Atendimento & Alunos)": "cs",
            "📈 Tráfego & Marketing (Growth - Ads)": "growth",
            "✍️ Conteúdo (Roteiros & Redes)": "conteudo",
            "🎓 Pedagógico & Produto (CPO - BNCC)": "cpo",
            "⚖️ Jurídico & Compliance (Legal - LGPD)": "legal"
        }
        agente_alvo = mapa_destinatario[destinatario]
        
        if agente_alvo == "ceo":
            st.info("🤝 **Modo Sparring 1-a-1:** Alinhamento direto com o CEO antes de despachar para os outros diretores.")
        elif agente_alvo:
            st.info(f"⚡ **Consulta Direta:** Parecer especializado de {destinatario.split('(')[0].strip()}")
        else:
            st.caption("Convocará todo o conselho para um plano executivo integrado.")

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
        
        # Abas de Entrada: Microfone, Áudio Gravado, Documento Anexado
        tab_mic, tab_up, tab_doc = st.tabs(["🎙️ Gravar Microfone", "📁 Enviar Áudio", "📄 Anexar Documento"])
        
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
            arquivo_subido = st.file_uploader("Envie arquivo de áudio gravado (.mp3, .m4a, .wav, .ogg, .oga):", type=["mp3", "m4a", "wav", "ogg", "oga"])
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

        with tab_doc:
            doc_anexado = st.file_uploader(
                "Anexe um documento para revisão, crítica ou refatoração (.pdf, .docx, .txt, .md, .csv, .json):",
                type=["pdf", "docx", "txt", "md", "csv", "json"]
            )
            if doc_anexado is not None:
                if st.session_state.get("ultimo_doc_nome") != doc_anexado.name:
                    with st.spinner(f"📄 Extraindo texto de {doc_anexado.name}..."):
                        bytes_doc = doc_anexado.read()
                        texto_doc = extrair_texto_documento(bytes_doc, doc_anexado.name)
                        st.session_state["texto_doc_anexado"] = texto_doc
                        st.session_state["ultimo_doc_nome"] = doc_anexado.name
                        st.success(f"✅ Arquivo '{doc_anexado.name}' carregado ({len(texto_doc)} caracteres)!")
                        with st.expander("Visualizar conteúdo extraído"):
                            st.text(texto_doc[:2000] + ("..." if len(texto_doc) > 2000 else ""))

        valor_inicial = st.session_state.get("texto_audio", demanda_padrao)
        demanda = st.text_area(
            "Descreva a demanda ou instruções para a reunião:",
            value=valor_inicial,
            height=110,
            placeholder="Ex: Revise o documento em anexo e aponte pontos cegos / crie um plano para..."
        )
        
        label_btn = f"🚀 Despachar com {destinatario.split('(')[0].strip()}"
        btn_executar = st.button(label_btn, type="primary", use_container_width=True)

    if btn_executar and (demanda.strip() or st.session_state.get("texto_doc_anexado")):
        # Prepara a demanda final incorporando o documento caso anexado
        doc_texto = st.session_state.get("texto_doc_anexado", "")
        doc_nome = st.session_state.get("ultimo_doc_nome", "documento")
        
        if doc_texto:
            demanda_completa = f"{demanda.strip()}\n\n--- DOCUMENTO ANEXADO PARA ANÁLISE ({doc_nome}) ---\n{doc_texto}"
        else:
            demanda_completa = demanda.strip()

        msg_spinner = f"⏳ Consultando {destinatario.split('(')[0].strip()}..."
        with st.spinner(msg_spinner):
            try:
                loop = asyncio.new_event_loop()
                asyncio.set_event_loop(loop)
                resultado = loop.run_until_complete(executar_consulta_estrategica(demanda_completa, agentes_alvo=agente_alvo))
                loop.close()
                
                resultado_str = str(resultado)
                canal_tag = f"Dashboard Web ({destinatario.split('(')[0].strip()})"
                registrar_consulta(canal_tag, demanda if demanda.strip() else f"Análise de {doc_nome}", resultado_str)
                st.session_state["ultimo_resultado"] = resultado_str
                st.session_state["ultima_demanda"] = demanda if demanda.strip() else f"Análise de {doc_nome}"
                st.success("✅ Resposta gerada com sucesso!")
            except Exception as e:
                st.error(f"⚠️ Erro ao processar com os agentes: {e}")

    # Exibe o último resultado gerado
    if "ultimo_resultado" in st.session_state:
        st.divider()
        res = st.session_state["ultimo_resultado"]
        dem = st.session_state["ultima_demanda"]
        
        st.subheader("📄 Síntese Executiva da Reunião")
        st.markdown(f"**Demanda:** *{dem}*")
        
        # Ações de Exportação
        col_exp1, col_exp2, col_exp3, col_exp4 = st.columns(4)
        
        with col_exp1:
            st.download_button(
                label="📥 Baixar em Markdown",
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
                    label="📄 Baixar em PDF",
                    data=bytes_pdf,
                    file_name="plano_executivo_simuladoapp.pdf",
                    mime="application/pdf",
                    use_container_width=True
                )
                if os.path.exists(caminho_pdf):
                    os.remove(caminho_pdf)
            except Exception as e_pdf:
                st.error(f"Erro ao gerar PDF: {e_pdf}")
                
        with col_exp3:
            if st.button("📋 Criar Card no Kanban", use_container_width=True):
                from database import criar_tarefa_kanban
                criar_tarefa_kanban(
                    texto=f"Executar plano: {dem[:60]}...",
                    descricao=f"Deliberação Executiva:\n\n{res[:1500]}...",
                    responsavel="👑 CEO & Estratégia",
                    prioridade="Alta",
                    fase="planejamento"
                )
                st.success("✅ Card criado com sucesso na coluna de Planejamento do Kanban!")
                
        with col_exp4:
            if st.button("📓 Enviar ao Notion", use_container_width=True):
                with st.spinner("Sincronizando com o Notion..."):
                    sucesso, msg_notion = criar_pagina_deliberacao(res, dem, canal="Dashboard Web")
                    if sucesso:
                        st.success(f"✅ {msg_notion}")
                    else:
                        st.error(f"⚠️ {msg_notion}")
                        
        st.markdown("---")
        st.markdown(res)

# ----------------- ABA 2: QUADRO DE TAREFAS (KANBAN EXECUTIVO) -----------------
elif aba_selecionada == "📋 Quadro de Tarefas":
    st.markdown("<div class='main-header'>📋 Kanban Executivo de Tarefas & Ações</div>", unsafe_allow_html=True)
    st.markdown("<div class='sub-header'>Acompanhe e gerencie as iniciativas do SimuladoApp em tempo real sem precisar abrir ferramentas externas.</div>", unsafe_allow_html=True)
    
    from database import (
        criar_tarefa_kanban,
        listar_tarefas_kanban,
        atualizar_fase_tarefa,
        atualizar_tarefa_completa,
        excluir_lembrete
    )
    
    todas_tarefas = listar_tarefas_kanban()
    
    # Métricas de Resumo
    m_backlog = len([t for t in todas_tarefas if t["fase"] == "backlog"])
    m_plan = len([t for t in todas_tarefas if t["fase"] == "planejamento"])
    m_exec = len([t for t in todas_tarefas if t["fase"] == "execucao"])
    m_conc = len([t for t in todas_tarefas if t["fase"] == "concluido"])
    
    col_m1, col_m2, col_m3, col_m4, col_m5 = st.columns(5)
    col_m1.metric("Total de Ações", len(todas_tarefas))
    col_m2.metric("📌 Backlog", m_backlog)
    col_m3.metric("⚙️ Planejamento", m_plan)
    col_m4.metric("🚀 Execução", m_exec)
    col_m5.metric("✅ Concluídas", m_conc)
    
    st.divider()

    # Criação Rápida de Tarefa
    with st.expander("➕ Criar Nova Tarefa / Ação Executiva", expanded=False):
        with st.form("form_nova_tarefa_kanban"):
            c_f1, c_f2 = st.columns([3, 1])
            with c_f1:
                t_titulo = st.text_input("Título da Tarefa / Ação:")
                t_desc = st.text_area("Descrição / Checklist / Detalhes:", height=70)
            with c_f2:
                t_resp = st.selectbox("Responsável:", [
                    "👤 Fundador",
                    "👑 CEO & Estratégia",
                    "💻 Tecnologia (CTO)",
                    "💰 Financeiro (CFO)",
                    "📈 Tráfego & Marketing (Growth)",
                    "✍️ Conteúdo & Redes",
                    "🎓 Pedagógico (CPO)",
                    "🎧 Suporte (CS)",
                    "⚖️ Jurídico (Legal)"
                ])
                t_prio = st.selectbox("Prioridade:", ["🔴 Alta", "🟡 Média", "🟢 Baixa"])
                t_fase_init = st.selectbox("Fase Inicial:", [
                    ("backlog", "📌 Backlog"),
                    ("planejamento", "⚙️ Planejamento"),
                    ("execucao", "🚀 Execução"),
                    ("concluido", "✅ Concluído")
                ], format_func=lambda x: x[1])[0]
                t_prazo = st.text_input("Prazo (ex: 28/08 ou Sexta):", placeholder="Opcional")
                
            btn_add_k = st.form_submit_button("🚀 Criar Card no Kanban", type="primary", use_container_width=True)
            if btn_add_k and t_titulo.strip():
                prio_limpa = t_prio.replace("🔴 ", "").replace("🟡 ", "").replace("🟢 ", "")
                criar_tarefa_kanban(
                    texto=t_titulo.strip(),
                    descricao=t_desc.strip(),
                    responsavel=t_resp,
                    prioridade=prio_limpa,
                    fase=t_fase_init,
                    data_prazo=t_prazo.strip()
                )
                st.success("Card criado com sucesso!")
                st.rerun()

    # Filtros do Quadro
    c_flt1, c_flt2, c_flt3 = st.columns([2, 2, 1.5])
    with c_flt1:
        filtro_resp = st.selectbox("Filtrar por Responsável:", ["Todos"] + sorted(list(set([t["responsavel"] for t in todas_tarefas]))))
    with c_flt2:
        filtro_prio = st.selectbox("Filtrar por Prioridade:", ["Todas", "Alta", "Média", "Baixa"])
    with c_flt3:
        modo_visao = st.radio("Visualização:", ["📊 Kanban", "📋 Lista"], horizontal=True)

    # Aplica Filtros
    tarefas_filtradas = todas_tarefas
    if filtro_resp != "Todos":
        tarefas_filtradas = [t for t in tarefas_filtradas if t["responsavel"] == filtro_resp]
    if filtro_prio != "Todas":
        tarefas_filtradas = [t for t in tarefas_filtradas if t["prioridade"] == filtro_prio]

    # Função auxiliar para renderizar um card
    def render_card(t):
        badge_prio = "🔴" if t["prioridade"] == "Alta" else ("🟡" if t["prioridade"] == "Média" else "🟢")
        with st.container(border=True):
            st.markdown(f"**{badge_prio} [{t['id']}] {t['texto']}**")
            st.caption(f"🎯 `{t['responsavel']}`" + (f" | ⏰ `{t['data_prazo']}`" if t['data_prazo'] else ""))
            
            if t["descricao"]:
                with st.expander("Detalhes"):
                    st.write(t["descricao"])
            
            # Botões de Movimentação entre Fases
            col_b1, col_b2, col_b3 = st.columns([1, 1, 0.8])
            
            fases_ordem = ["backlog", "planejamento", "execucao", "concluido"]
            idx_atual = fases_ordem.index(t["fase"]) if t["fase"] in fases_ordem else 0
            
            with col_b1:
                if idx_atual > 0:
                    if st.button("⬅️", key=f"rec_{t['id']}", help=f"Mover para {fases_ordem[idx_atual-1]}"):
                        atualizar_fase_tarefa(t["id"], fases_ordem[idx_atual-1])
                        st.rerun()
            with col_b2:
                if idx_atual < len(fases_ordem) - 1:
                    if st.button("➡️", key=f"adv_{t['id']}", help=f"Avançar para {fases_ordem[idx_atual+1]}"):
                        atualizar_fase_tarefa(t["id"], fases_ordem[idx_atual+1])
                        st.rerun()
            with col_b3:
                if st.button("🗑️", key=f"delk_{t['id']}", help="Excluir tarefa"):
                    excluir_lembrete(t["id"])
                    st.rerun()

    # MODO 1: QUADRO KANBAN
    if modo_visao == "📊 Kanban":
        col_k1, col_k2, col_k3, col_k4 = st.columns(4)
        
        with col_k1:
            st.markdown("### 📌 Backlog")
            t_backlog = [t for t in tarefas_filtradas if t["fase"] == "backlog"]
            if not t_backlog:
                st.caption("Nenhum item")
            for t in t_backlog:
                render_card(t)
                
        with col_k2:
            st.markdown("### ⚙️ Planejamento")
            t_plan = [t for t in tarefas_filtradas if t["fase"] == "planejamento"]
            if not t_plan:
                st.caption("Nenhum item")
            for t in t_plan:
                render_card(t)
                
        with col_k3:
            st.markdown("### 🚀 Em Execução")
            t_exec = [t for t in tarefas_filtradas if t["fase"] == "execucao"]
            if not t_exec:
                st.caption("Nenhum item")
            for t in t_exec:
                render_card(t)
                
        with col_k4:
            st.markdown("### ✅ Concluído")
            t_conc = [t for t in tarefas_filtradas if t["fase"] == "concluido"]
            if not t_conc:
                st.caption("Nenhum item")
            for t in t_conc:
                render_card(t)

    # MODO 2: LISTA DETALHADA
    else:
        st.markdown("### 📋 Lista Completa de Tarefas")
        if not tarefas_filtradas:
            st.info("Nenhuma tarefa cadastrada.")
        else:
            for t in tarefas_filtradas:
                c_l1, c_l2, c_l3, c_l4 = st.columns([3.5, 1.5, 1.5, 0.8])
                with c_l1:
                    st.markdown(f"**[{t['id']}] {t['texto']}**")
                    if t["descricao"]:
                        st.caption(t["descricao"])
                with c_l2:
                    st.write(f"🎯 `{t['responsavel']}`")
                with c_l3:
                    st.write(f"📊 `{t['fase'].upper()}` | Prioridade: `{t['prioridade']}`")
                with c_l4:
                    if st.button("🗑️", key=f"dell_{t['id']}"):
                        excluir_lembrete(t["id"])
                        st.rerun()
                st.divider()

# ----------------- ABA 3: HISTÓRICO DE DECISÕES -----------------
elif aba_selecionada == "📜 Histórico de Decisões":
    st.markdown("<div class='main-header'>📜 Histórico de Deliberações</div>", unsafe_allow_html=True)
    st.markdown("<div class='sub-header'>Linha do tempo de todas as decisões com download de PDF, Markdown e envio ao Notion a qualquer momento.</div>", unsafe_allow_html=True)
    
    historico = listar_historico_consultas(limite=50)
    
    if not historico:
        st.info("Nenhum histórico registrado até o momento.")
    else:
        for h_id, canal, demanda, resposta, data_reg in historico:
            with st.expander(f"🕒 [{data_reg}] [{canal}] {demanda[:75]}..."):
                st.markdown(f"**Canal de Origem:** `{canal}` | **Data:** `{data_reg}`")
                st.markdown(f"**Demanda Registrada:**\n> {demanda}")
                
                # Ações Rápidas de Download, Kanban e Notion para cada item do histórico
                col_h1, col_h2, col_h3, col_h4 = st.columns(4)
                with col_h1:
                    st.download_button(
                        label="📥 Baixar Markdown (.md)",
                        data=resposta,
                        file_name=f"deliberacao_{h_id}.md",
                        mime="text/markdown",
                        key=f"dl_md_{h_id}",
                        use_container_width=True
                    )
                with col_h2:
                    try:
                        pdf_path = gerar_pdf(resposta, demanda)
                        with open(pdf_path, "rb") as f_hpdf:
                            pdf_bytes = f_hpdf.read()
                        st.download_button(
                            label="📄 Baixar PDF Executivo",
                            data=pdf_bytes,
                            file_name=f"deliberacao_{h_id}.pdf",
                            mime="application/pdf",
                            key=f"dl_pdf_{h_id}",
                            use_container_width=True
                        )
                        if os.path.exists(pdf_path):
                            os.remove(pdf_path)
                    except Exception as err_pdf:
                        st.caption(f"PDF indisponível: {err_pdf}")
                        
                with col_h3:
                    if st.button("📋 Criar no Kanban", key=f"btn_kanban_{h_id}", use_container_width=True):
                        from database import criar_tarefa_kanban
                        criar_tarefa_kanban(
                            texto=f"Executar plano #{h_id}: {demanda[:50]}...",
                            descricao=f"Deliberação Executiva ({data_reg}):\n\n{resposta[:1500]}...",
                            responsavel="👑 CEO & Estratégia",
                            prioridade="Alta",
                            fase="planejamento"
                        )
                        st.success("✅ Card criado na coluna de Planejamento do Kanban!")

                with col_h4:
                    if st.button("📓 Enviar ao Notion", key=f"btn_notion_{h_id}", use_container_width=True):
                        with st.spinner("Sincronizando com o Notion..."):
                            ok, msg_n = criar_pagina_deliberacao(resposta, demanda, canal=canal)
                            if ok:
                                st.success(f"✅ {msg_n}")
                            else:
                                st.error(f"⚠️ {msg_n}")
                                
                st.divider()
                st.markdown("**Conteúdo do Parecer:**")
                st.markdown(resposta)

# ----------------- ABA 4: MEMBROS DO CONSELHO & CONFIGURAÇÃO (ESTILO GOOGLE GEMS) -----------------
elif aba_selecionada == "👥 Membros do Conselho":
    st.markdown("<div class='main-header'>👥 Personalização de Agentes Executivos</div>", unsafe_allow_html=True)
    st.markdown("<div class='sub-header'>Configure Nome, Descrição, Instruções e faça upload de arquivos Markdown para a Base de Conhecimento de cada diretor.</div>", unsafe_allow_html=True)
    
    from database import (
        obter_configuracoes_agentes,
        salvar_configuracao_agente,
        restaurar_padrao_agentes,
        listar_arquivos_agente,
        salvar_arquivo_agente,
        excluir_arquivo_agente,
        ler_arquivo_agente
    )
    
    configs_atuais = obter_configuracoes_agentes()
    
    col_sel, col_reset = st.columns([3, 1])
    with col_sel:
        agente_chave_sel = st.selectbox(
            "Selecione o Diretor / Gem para Editar:",
            list(configs_atuais.keys()),
            format_func=lambda k: f"{k.upper()} — {configs_atuais[k]['cargo']}"
        )
    with col_reset:
        st.write("")
        st.write("")
        if st.button("🔄 Sincronizar Bases", use_container_width=True):
            restaurar_padrao_agentes()
            st.success("Bases de conhecimento sincronizadas com sucesso!")
            st.rerun()

    dados_agente = configs_atuais[agente_chave_sel]
    arquivos_conhecimento = listar_arquivos_agente(agente_chave_sel)
    
    st.divider()

    # 1, 2 & 3: FORMULÁRIO DE NOME, DESCRIÇÃO E INSTRUÇÕES (ESTILO GOOGLE GEMS)
    with st.form(key=f"form_gem_config_{agente_chave_sel}"):
        st.markdown("#### 🏷️ Nome do Agente")
        novo_cargo = st.text_input("Nome", value=dados_agente["cargo"], label_visibility="collapsed")
        
        st.markdown("#### 📝 Descrição")
        nova_meta = st.text_input(
            "Descrição",
            value=dados_agente["meta"],
            help="Descrição de alto nível do papel executivo do diretor.",
            label_visibility="collapsed"
        )
        
        st.markdown("#### 🧠 Instruções (Persona, Tom & Regras de Entrega)")
        novas_diretrizes = st.text_area(
            "Instruções",
            value=dados_agente["diretrizes"],
            height=260,
            help="Instruções de sistema, mentalidade de referência, regras do Split 33/33/33 e formatos de resposta.",
            label_visibility="collapsed"
        )
        
        btn_salvar_gem = st.form_submit_button(
            f"💾 Salvar Alterações de '{dados_agente['cargo']}'",
            type="primary",
            use_container_width=True
        )
        
        if btn_salvar_gem:
            salvar_configuracao_agente(agente_chave_sel, novo_cargo.strip(), nova_meta.strip(), novas_diretrizes.strip())
            st.success(f"✅ Configurações e Instruções de '{novo_cargo}' salvas e persistidas com sucesso!")
            st.rerun()

    st.divider()

    # 4. BASE DE CONHECIMENTO (CARDS DE ARQUIVOS .MD ANEXADOS)
    st.markdown("#### 📚 Base de Conhecimento (Arquivos Markdown Anexados)")
    st.caption("Arquivos `.md` físicos anexados à base de dados deste diretor. O agente lê esses documentos a cada consulta e eles nunca são perdidos.")

    if not arquivos_conhecimento:
        st.info("Nenhum arquivo `.md` anexado à base deste agente ainda. Faça o upload abaixo para adicionar documentos de negócio!")
    else:
        # Exibe em grid de cards (2 colunas) estilo Google Gems
        cols_cards = st.columns(2)
        for idx, arq in enumerate(arquivos_conhecimento):
            with cols_cards[idx % 2]:
                with st.container(border=True):
                    c_icone, c_info, c_acoes = st.columns([0.8, 3.2, 1.2])
                    with c_icone:
                        st.markdown("<h2 style='margin:0; text-align:center;'>📄</h2>", unsafe_allow_html=True)
                    with c_info:
                        st.markdown(f"**{arq['nome']}**")
                        st.caption(f"Tamanho: `{arq['tamanho']} bytes`")
                    with c_acoes:
                        btn_del = st.button("🗑️", key=f"del_arq_{agente_chave_sel}_{arq['nome']}", help="Remover arquivo da base")
                        if btn_del:
                            excluir_arquivo_agente(agente_chave_sel, arq['nome'])
                            st.warning(f"Arquivo '{arq['nome']}' removido da base.")
                            st.rerun()
                    
                    with st.expander(f"👁️ Ler '{arq['nome']}'"):
                        conteudo_preview = ler_arquivo_agente(agente_chave_sel, arq['nome'])
                        st.markdown(conteudo_preview)

    # 5. UPLOAD DE NOVOS ARQUIVOS PARA A BASE DE CONHECIMENTO DO AGENTE
    st.markdown("##### ➕ Anexar Novo Arquivo à Base deste Agente")
    arq_up = st.file_uploader(
        f"Faça upload de um arquivo .md para adicionar à base do {dados_agente['cargo']}:",
        type=["md", "txt"],
        key=f"up_md_{agente_chave_sel}"
    )
    if arq_up is not None:
        if st.button(f"📥 Salvar '{arq_up.name}' na Base de Conhecimento", key=f"btn_save_up_{agente_chave_sel}", type="primary"):
            bytes_up = arq_up.read()
            ok = salvar_arquivo_agente(agente_chave_sel, arq_up.name, bytes_up)
            if ok:
                st.success(f"✅ Arquivo '{arq_up.name}' incorporado com sucesso à base de conhecimento do {dados_agente['cargo']}!")
                st.rerun()
            else:
                st.error("Erro ao salvar arquivo na base.")
