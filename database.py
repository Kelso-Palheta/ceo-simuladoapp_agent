import sqlite3
from datetime import datetime
import os

def get_db_path() -> str:
    """Retorna o caminho correto do banco de dados para sincronizar Telegram e Dashboard."""
    if os.getenv("DB_PATH"):
        return os.getenv("DB_PATH")
    if os.path.exists("/app/data"):
        return "/app/data/simulado_memory.db"
    if os.path.exists("data"):
        return "data/simulado_memory.db"
    return "simulado_memory.db"

def get_connection():
    """Retorna uma conexão configurada com WAL mode e timeout seguro para concorrência."""
    db_path = get_db_path()
    dir_name = os.path.dirname(db_path)
    if dir_name and not os.path.exists(dir_name):
        os.makedirs(dir_name, exist_ok=True)
        
    conn = sqlite3.connect(db_path, timeout=15)
    conn.execute("PRAGMA journal_mode=WAL;")
    conn.execute("PRAGMA busy_timeout = 5000;")
    return conn

def obter_diretorio_agente(chave: str) -> str:
    """Retorna o caminho da pasta de conhecimento dedicada para o agente."""
    dir_path = os.path.join("conhecimento", chave)
    if not os.path.exists(dir_path):
        os.makedirs(dir_path, exist_ok=True)
    return dir_path

def listar_arquivos_agente(chave: str) -> list[dict]:
    """Lista todos os arquivos .md anexados na base de conhecimento do agente."""
    dir_agente = obter_diretorio_agente(chave)
    arquivos = []
    
    if os.path.exists(dir_agente):
        for nome in sorted(os.listdir(dir_agente)):
            if nome.endswith(".md") and not nome.startswith("."):
                caminho = os.path.join(dir_agente, nome)
                try:
                    tamanho = os.path.getsize(caminho)
                    arquivos.append({
                        "nome": nome,
                        "caminho": caminho,
                        "tamanho": tamanho
                    })
                except Exception:
                    pass
    return arquivos

def ler_arquivo_agente(chave: str, nome_arquivo: str) -> str:
    """Lê o conteúdo textual de um arquivo .md específico da base do agente."""
    caminho = os.path.join(obter_diretorio_agente(chave), nome_arquivo)
    if os.path.exists(caminho):
        try:
            with open(caminho, "r", encoding="utf-8") as f:
                return f.read()
        except Exception as e:
            return f"Erro ao ler arquivo: {e}"
    return ""

def salvar_arquivo_agente(chave: str, nome_arquivo: str, conteudo_bytes_ou_str: bytes | str) -> bool:
    """Salva um novo arquivo .md na base de conhecimento do agente."""
    if not nome_arquivo.endswith(".md"):
        nome_arquivo += ".md"
    nome_limpo = "".join([c for c in nome_arquivo if c.isalnum() or c in "._- "]).strip()
    caminho = os.path.join(obter_diretorio_agente(chave), nome_limpo)
    try:
        if isinstance(conteudo_bytes_ou_str, bytes):
            with open(caminho, "wb") as f:
                f.write(conteudo_bytes_ou_str)
        else:
            with open(caminho, "w", encoding="utf-8") as f:
                f.write(conteudo_bytes_ou_str)
        return True
    except Exception:
        return False

def excluir_arquivo_agente(chave: str, nome_arquivo: str) -> bool:
    """Exclui um arquivo .md da base de conhecimento do agente."""
    caminho = os.path.join(obter_diretorio_agente(chave), nome_arquivo)
    if os.path.exists(caminho):
        try:
            os.remove(caminho)
            return True
        except Exception:
            return False
    return False

def carregar_conhecimento_total_agente(chave: str) -> str:
    """Lê documentos adicionais anexados pelo usuário na pasta do agente sem duplicar arquivos de persona."""
    arquivos = listar_arquivos_agente(chave)
    blocos = []
    # Nomes de arquivos que são personas do sistema e não devem ser duplicados no contexto
    arquivos_ignorar = [
        "persona_instrucoes.md",
        f"{chave}_diretrizes.md",
        "ceo_diretrizes.md",
        "cto_arquitetura.md",
        "cfo_financeiro.md",
        "growth_metricas.md",
        "conteudo_personas.md",
        "cpo_pedagogico.md",
        "cs_suporte.md",
        "legal_compliance.md"
    ]
    for arq in arquivos:
        if arq["nome"] not in arquivos_ignorar:
            conteudo = ler_arquivo_agente(chave, arq["nome"])
            if conteudo.strip():
                # Limita a 2.500 caracteres por arquivo adicional para não estourar tokens
                trecho = conteudo.strip()[:2500]
                blocos.append(f"--- DOCUMENTO ANEXADO [{arq['nome']}] ---\n{trecho}")
    return "\n\n".join(blocos)

MAPA_ARQUIVOS_CONHECIMENTO = {
    "ceo": ("conhecimento/ceo_diretrizes.md", "CEO & Estratégia", "Orquestrar o Conselho Executivo do SimuladoApp, assegurar o Split Societário (33,33% Sócio 1 / 33,33% Sócio 2 / 33,33% Caixa PJ), proteger a liquidez e entregar planos em 5 seções."),
    "cto": ("conhecimento/cto_arquitetura.md", "Tecnologia (CTO)", "Entregar Mini-PRDs Técnicos de produção em Django/MySQL, otimizar pipeline OpenCV (<1s latência, >98% precisão) e Celery/Redis."),
    "cpo": ("conhecimento/cpo_pedagogico.md", "Pedagógico & Produto (CPO)", "Garantir UX docente sem atrito (< 3 cliques), alinhamento estrito à BNCC/SAEB e relatórios formativos de 1 página."),
    "growth": ("conhecimento/growth_metricas.md", "Tráfego & Marketing (Growth)", "Desenhar campanhas Meta Ads com CPL <= R$ 0,75, CAC Pago <= R$ 15,00, ROAS >= 3.5x e alocação dinâmica nos picos bimestrais (abril, junho, set, nov)."),
    "conteudo": ("conhecimento/conteudo_personas.md", "Conteúdo & Redes", "Criar roteiros magnéticos de Reels/Shorts em 3 atos (Hook 3s, Desenvolvimento, CTA) focados no alívio: 'O SimuladoApp devolve seus finais de semana'."),
    "cfo": ("conhecimento/cfo_financeiro.md", "Financeiro (CFO)", "Auditar o Split 33/33/33, conciliação quinzenal, monitorar taxas de gateway Pix e garantir reserva de segurança de 3 meses de custos fixos."),
    "cs": ("conhecimento/cs_suporte.md", "Suporte (CS)", "Manter churn < 5%, régua D+0/D+1 humanizada no WhatsApp e operar o gatilho de upsell para Pacote M quando o saldo for <= 15%."),
    "legal": ("conhecimento/legal_compliance.md", "Jurídico & Compliance (Legal)", "Blindagem LGPD escolar (dados de menores, SimuladoApp como Operador), Termos de Uso de SaaS, INPI e Acordo de Sócios 33/33/33.")
}

def carregar_conhecimento_arquivo(chave: str) -> str:
    """Lê os arquivos de conhecimento da pasta do agente ou arquivo legado."""
    conhecimento_pasta = carregar_conhecimento_total_agente(chave)
    if conhecimento_pasta.strip():
        return conhecimento_pasta
        
    if chave in MAPA_ARQUIVOS_CONHECIMENTO:
        rel_path, _, _ = MAPA_ARQUIVOS_CONHECIMENTO[chave]
        caminhos_tentar = [
            rel_path,
            os.path.join(os.path.dirname(__file__), rel_path),
            os.path.join("/app", rel_path)
        ]
        for cam in caminhos_tentar:
            if os.path.exists(cam):
                try:
                    with open(cam, "r", encoding="utf-8") as f:
                        conteudo = f.read().strip()
                        if conteudo:
                            return conteudo
                except Exception:
                    pass
    return ""

def obter_config_padrao_completa() -> dict:
    """Monta a configuração padrão com todo o conteúdo rico e detalhado da base de conhecimento."""
    config = {}
    for chave, (rel_path, cargo, meta) in MAPA_ARQUIVOS_CONHECIMENTO.items():
        diretrizes = carregar_conhecimento_arquivo(chave)
        if not diretrizes:
            diretrizes = f"Você é o {cargo} do SimuladoApp. Foco em excelência e metas estratégicas."
        config[chave] = {
            "cargo": cargo,
            "meta": meta,
            "diretrizes": diretrizes
        }
    return config

# Diretrizes padrão completas
CONFIG_PADRAO_AGENTES = obter_config_padrao_completa()

def init_db():
    conn = get_connection()
    cursor = conn.cursor()
    
    # Tabela de tarefas e Kanban Executivo
    cursor.execute("""
        CREATE TABLE IF NOT EXISTS lembretes (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            texto TEXT NOT NULL,
            descricao TEXT DEFAULT '',
            responsavel TEXT DEFAULT 'Fundador',
            prioridade TEXT DEFAULT 'Média',
            fase TEXT DEFAULT 'backlog',
            status TEXT DEFAULT 'pendente',
            data_criacao TEXT NOT NULL,
            data_prazo TEXT DEFAULT ''
        )
    """)

    # Migra colunas novas caso a tabela tenha sido criada em versão antiga
    cursor.execute("PRAGMA table_info(lembretes)")
    colunas_existentes = [col[1] for col in cursor.fetchall()]
    
    colunas_para_adicionar = {
        "descricao": "TEXT DEFAULT ''",
        "responsavel": "TEXT DEFAULT 'Fundador'",
        "prioridade": "TEXT DEFAULT 'Média'",
        "fase": "TEXT DEFAULT 'backlog'",
        "data_prazo": "TEXT DEFAULT ''"
    }
    
    for col, tipo in colunas_para_adicionar.items():
        if col not in colunas_existentes:
            try:
                cursor.execute(f"ALTER TABLE lembretes ADD COLUMN {col} {tipo}")
            except Exception:
                pass
    
    # Histórico de consultas estratégicas (Telegram, Web, CLI)
    cursor.execute("""
        CREATE TABLE IF NOT EXISTS consultas_historico (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            canal TEXT NOT NULL,
            demanda TEXT NOT NULL,
            resposta TEXT NOT NULL,
            data_registro TEXT NOT NULL
        )
    """)

    # Tabela de Configuração e Diretrizes Customizadas dos Agentes
    cursor.execute("""
        CREATE TABLE IF NOT EXISTS configuracao_agentes (
            chave TEXT PRIMARY KEY,
            cargo TEXT NOT NULL,
            meta TEXT NOT NULL,
            diretrizes TEXT NOT NULL,
            data_atualizacao TEXT NOT NULL
        )
    """)
    
    # Sincroniza com as diretrizes padrão apenas se o agente ainda não estiver cadastrado no banco
    configs_completas = obter_config_padrao_completa()
    cursor.execute("SELECT chave FROM configuracao_agentes")
    existentes = set([row[0] for row in cursor.fetchall()])
    
    for chave, dados in configs_completas.items():
        if chave not in existentes:
            cursor.execute("""
                INSERT INTO configuracao_agentes (chave, cargo, meta, diretrizes, data_atualizacao)
                VALUES (?, ?, ?, ?, ?)
            """, (chave, dados["cargo"], dados["meta"], dados["diretrizes"], datetime.now().strftime("%d/%m/%Y %H:%M")))
    
    conn.commit()
    conn.close()

def obter_configuracoes_agentes() -> dict:
    """Retorna as diretrizes ativas de todos os agentes configuradas no banco de dados."""
    init_db()
    conn = get_connection()
    cursor = conn.cursor()
    cursor.execute("SELECT chave, cargo, meta, diretrizes, data_atualizacao FROM configuracao_agentes")
    linhas = cursor.fetchall()
    conn.close()
    
    config = {}
    for chave, cargo, meta, diretrizes, data_atualizacao in linhas:
        config[chave] = {
            "cargo": cargo,
            "meta": meta,
            "diretrizes": diretrizes,
            "data_atualizacao": data_atualizacao
        }
    return config

def salvar_configuracao_agente(chave: str, cargo: str, meta: str, diretrizes: str):
    """Atualiza as diretrizes personalizadas de um agente no banco de dados e em arquivo de disco."""
    conn = get_connection()
    cursor = conn.cursor()
    data_hora = datetime.now().strftime("%d/%m/%Y %H:%M")
    cursor.execute("""
        INSERT INTO configuracao_agentes (chave, cargo, meta, diretrizes, data_atualizacao)
        VALUES (?, ?, ?, ?, ?)
        ON CONFLICT(chave) DO UPDATE SET
            cargo = excluded.cargo,
            meta = excluded.meta,
            diretrizes = excluded.diretrizes,
            data_atualizacao = excluded.data_atualizacao
    """, (chave, cargo.strip(), meta.strip(), diretrizes.strip(), data_hora))
    conn.commit()
    conn.close()
    
    # Salva também uma cópia no diretório de conhecimento do agente para persistência em disco
    dir_agente = obter_diretorio_agente(chave)
    arq_persona = os.path.join(dir_agente, "persona_instrucoes.md")
    try:
        with open(arq_persona, "w", encoding="utf-8") as f:
            f.write(f"# {cargo.upper()}\n\n**Meta:** {meta}\n\n## INSTRUÇÕES\n\n{diretrizes}")
    except Exception:
        pass

def restaurar_padrao_agentes():
    """Restaura as diretrizes padrão de todos os agentes a partir dos arquivos .md de conhecimento."""
    padrao = obter_config_padrao_completa()
    for chave, dados in padrao.items():
        salvar_configuracao_agente(chave, dados["cargo"], dados["meta"], dados["diretrizes"])

def criar_tarefa_kanban(
    texto: str,
    descricao: str = "",
    responsavel: str = "Fundador",
    prioridade: str = "Média",
    fase: str = "backlog",
    data_prazo: str = ""
) -> int:
    """Cria um novo card de tarefa no Kanban Executivo."""
    conn = get_connection()
    cursor = conn.cursor()
    status = "concluido" if fase == "concluido" else "pendente"
    cursor.execute("""
        INSERT INTO lembretes (texto, descricao, responsavel, prioridade, fase, status, data_criacao, data_prazo)
        VALUES (?, ?, ?, ?, ?, ?, ?, ?)
    """, (
        texto.strip(),
        descricao.strip(),
        responsavel,
        prioridade,
        fase,
        status,
        datetime.now().strftime("%d/%m/%Y %H:%M"),
        data_prazo.strip()
    ))
    novo_id = cursor.lastrowid
    conn.commit()
    conn.close()
    return novo_id

def salvar_lembrete(texto: str):
    """Função legada de lembrete simples (cria no backlog)."""
    criar_tarefa_kanban(texto=texto, fase="backlog")

def listar_tarefas_kanban() -> list[dict]:
    """Retorna todas as tarefas formatadas como dicionário com todos os metadados do Kanban."""
    init_db()
    conn = get_connection()
    cursor = conn.cursor()
    cursor.execute("""
        SELECT id, texto, descricao, responsavel, prioridade, fase, status, data_criacao, data_prazo
        FROM lembretes
        ORDER BY id DESC
    """)
    linhas = cursor.fetchall()
    conn.close()
    
    tarefas = []
    for row in linhas:
        fase = row[5] if row[5] in ["backlog", "planejamento", "execucao", "concluido"] else ("concluido" if row[6] == "concluido" else "backlog")
        tarefas.append({
            "id": row[0],
            "texto": row[1],
            "descricao": row[2] or "",
            "responsavel": row[3] or "Fundador",
            "prioridade": row[4] or "Média",
            "fase": fase,
            "status": row[6] or "pendente",
            "data_criacao": row[7],
            "data_prazo": row[8] or ""
        })
    return tarefas

def atualizar_fase_tarefa(item_id: int, nova_fase: str):
    """Atualiza a fase da tarefa no Kanban (backlog -> planejamento -> execucao -> concluido)."""
    conn = get_connection()
    cursor = conn.cursor()
    status = "concluido" if nova_fase == "concluido" else "pendente"
    cursor.execute("""
        UPDATE lembretes 
        SET fase = ?, status = ? 
        WHERE id = ?
    """, (nova_fase, status, item_id))
    conn.commit()
    conn.close()

def atualizar_tarefa_completa(
    item_id: int,
    texto: str,
    descricao: str,
    responsavel: str,
    prioridade: str,
    fase: str,
    data_prazo: str = ""
):
    """Atualiza todos os dados de uma tarefa no Kanban."""
    conn = get_connection()
    cursor = conn.cursor()
    status = "concluido" if fase == "concluido" else "pendente"
    cursor.execute("""
        UPDATE lembretes 
        SET texto = ?, descricao = ?, responsavel = ?, prioridade = ?, fase = ?, status = ?, data_prazo = ?
        WHERE id = ?
    """, (texto.strip(), descricao.strip(), responsavel, prioridade, fase, status, data_prazo.strip(), item_id))
    conn.commit()
    conn.close()

def listar_lembretes(status: str = "pendente"):
    conn = get_connection()
    cursor = conn.cursor()
    if status == "todos":
        cursor.execute("SELECT id, texto, status, data_criacao FROM lembretes ORDER BY id DESC")
    else:
        cursor.execute("SELECT id, texto, status, data_criacao FROM lembretes WHERE status = ? ORDER BY id DESC", (status,))
    itens = cursor.fetchall()
    conn.close()
    return itens

def listar_lembretes_pendentes():
    conn = get_connection()
    cursor = conn.cursor()
    cursor.execute("SELECT id, texto FROM lembretes WHERE status != 'concluido' AND fase != 'concluido' ORDER BY id DESC")
    itens = cursor.fetchall()
    conn.close()
    return itens

def alternar_status_lembrete(item_id: int, novo_status: str = "concluido"):
    nova_fase = "concluido" if novo_status == "concluido" else "backlog"
    atualizar_fase_tarefa(item_id, nova_fase)

def excluir_lembrete(item_id: int):
    conn = get_connection()
    cursor = conn.cursor()
    cursor.execute("DELETE FROM lembretes WHERE id = ?", (item_id,))
    conn.commit()
    conn.close()

def registrar_consulta(canal: str, demanda: str, resposta: str):
    conn = get_connection()
    cursor = conn.cursor()
    cursor.execute("""
        INSERT INTO consultas_historico (canal, demanda, resposta, data_registro)
        VALUES (?, ?, ?, ?)
    """, (canal, demanda, resposta, datetime.now().strftime("%d/%m/%Y %H:%M:%S")))
    conn.commit()
    conn.close()

def listar_historico_consultas(limite: int = 50):
    conn = get_connection()
    cursor = conn.cursor()
    cursor.execute("""
        SELECT id, canal, demanda, resposta, data_registro 
        FROM consultas_historico 
        ORDER BY id DESC 
        LIMIT ?
    """, (limite,))
    itens = cursor.fetchall()
    conn.close()
    return itens
