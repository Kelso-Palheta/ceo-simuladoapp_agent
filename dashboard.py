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
        col_exp1, col_exp2, col_exp3 = st.columns(3)
        
        with col_exp1:
            st.download_button(
                label="📥 Baixar Markdown (.md)",
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
                    file_name="plano_executivo_simuladoapp.pdf",
                    mime="application/pdf",
                    use_container_width=True
                )
                if os.path.exists(caminho_pdf):
                    os.remove(caminho_pdf)
            except Exception as e_pdf:
                st.error(f"Erro ao gerar PDF: {e_pdf}")
                
        with col_exp3:
            if st.button("📓 Sincronizar com Notion", use_container_width=True):
                with st.spinner("Sincronizando com o Notion..."):
                    sucesso, msg_notion = criar_pagina_deliberacao(res, dem, canal="Dashboard Web")
                    if sucesso:
                        st.success(f"✅ {msg_notion}")
                    else:
                        st.error(f"⚠️ {msg_notion}")
                        
        st.markdown("---")
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
    st.markdown("<div class='sub-header'>Linha do tempo de todas as decisões com download de PDF, Markdown e envio ao Notion a qualquer momento.</div>", unsafe_allow_html=True)
    
    historico = listar_historico_consultas(limite=50)
    
    if not historico:
        st.info("Nenhum histórico registrado até o momento.")
    else:
        for h_id, canal, demanda, resposta, data_reg in historico:
            with st.expander(f"🕒 [{data_reg}] [{canal}] {demanda[:75]}..."):
                st.markdown(f"**Canal de Origem:** `{canal}` | **Data:** `{data_reg}`")
                st.markdown(f"**Demanda Registrada:**\n> {demanda}")
                
                # Ações Rápidas de Download e Notion para cada item do histórico
                col_h1, col_h2, col_h3 = st.columns(3)
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

    # 1. NOME & DESCRIÇÃO
    st.markdown("#### 🏷️ Nome do Agente")
    novo_cargo = st.text_input("Nome", value=dados_agente["cargo"], key=f"nome_{agente_chave_sel}", label_visibility="collapsed")
    
    st.markdown("#### 📝 Descrição")
    nova_meta = st.text_input(
        "Descrição",
        value=dados_agente["meta"],
        key=f"desc_{agente_chave_sel}",
        help="Descrição de alto nível do papel executivo do diretor.",
        label_visibility="collapsed"
    )
    
    # 2. INSTRUÇÕES (PERSONA & COMPORTAMENTO)
    st.markdown("#### 🧠 Instruções (Persona, Tom & Regras de Entrega)")
    novas_diretrizes = st.text_area(
        "Instruções",
        value=dados_agente["diretrizes"],
        height=260,
        key=f"inst_{agente_chave_sel}",
        help="Instruções de sistema, mentalidade de referência, regras do Split 33/33/33 e formatos de resposta.",
        label_visibility="collapsed"
    )
    
    # Botão de salvar alterações das instruções
    if st.button("💾 Salvar Alterações de Nome, Descrição e Instruções", type="primary", use_container_width=True):
        salvar_configuracao_agente(agente_chave_sel, novo_cargo.strip(), nova_meta.strip(), novas_diretrizes.strip())
        st.success(f"✅ Configurações do {novo_cargo} atualizadas com sucesso!")
        st.rerun()

    st.divider()

    # 3. BASE DE CONHECIMENTO (CARDS DE ARQUIVOS .MD ANEXADOS)
    st.markdown("#### 📚 Base de Conhecimento (Arquivos Markdown Anexados)")
    st.caption("Arquivos `.md` que embasam o conhecimento técnico, estratégico e operacional deste diretor. O agente lê esses documentos a cada consulta.")

    if not arquivos_conhecimento:
        st.info("Nenhum arquivo `.md` anexado à base deste agente ainda. Faça o upload abaixo para aumentar a inteligência dele!")
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

    # 4. UPLOAD DE NOVOS ARQUIVOS PARA A BASE DE CONHECIMENTO DO AGENTE
    st.markdown("##### ➕ Anexar Novo Arquivo à Base deste Agente")
    arq_up = st.file_uploader(
        f"Faça upload de um arquivo .md para adicionar à base do {dados_agente['cargo']}:",
        type=["md", "txt"],
        key=f"up_md_{agente_chave_sel}"
    )
    if arq_up is not None:
        if st.button(f"📥 Salvar '{arq_up.name}' na Base do Agente", key=f"btn_save_up_{agente_chave_sel}"):
            bytes_up = arq_up.read()
            ok = salvar_arquivo_agente(agente_chave_sel, arq_up.name, bytes_up)
            if ok:
                st.success(f"✅ Arquivo '{arq_up.name}' incorporado com sucesso à inteligência do agente!")
                st.rerun()
            else:
                st.error("Erro ao salvar arquivo na base.")
