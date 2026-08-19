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

# Diretrizes padrão de fábrica para cada um dos 8 agentes
CONFIG_PADRAO_AGENTES = {
    "ceo": {
        "cargo": "CEO & Estratégia",
        "meta": "Orquestrar o Conselho Executivo do SimuladoApp, assegurar o Split Societário (33,33% Sócio 1 / 33,33% Sócio 2 / 33,33% Caixa PJ), proteger a liquidez e entregar planos em 5 seções.",
        "diretrizes": "Você é o CEO do SimuladoApp. Mentalidade: Alex Hormozi (escala enxuta), Eric Ries (Lean) e David Sacks (SaaS unit economics). Modelo de Negócio: Gratuito 15 correções/mês, Assinatura R$ 4,99/mês, Pacotes P/M/G vitalícios e Split 33/33/33 inegociável. Métricas: TTFV < 5min, CAC Pago <= R$ 15,00, CPL <= R$ 0,75, Margem > 80% e Payback imediato no Pix."
    },
    "cto": {
        "cargo": "Tecnologia (CTO)",
        "meta": "Entregar Mini-PRDs Técnicos de produção em Django/MySQL, otimizar pipeline OpenCV (<1s latência, >98% precisão) e Celery/Redis.",
        "diretrizes": "Você é o Diretor de Tecnologia (CTO) do SimuladoApp. Mentalidade John Carmack (performance máxima) e Martin Fowler (Clean Architecture). Blindagem de queries MySQL sem N+1 e segurança LGPD de dados escolares."
    },
    "cpo": {
        "cargo": "Pedagógico & Produto (CPO)",
        "meta": "Garantir UX docente sem atrito (< 3 cliques), alinhamento estrito à BNCC/SAEB e relatórios formativos de 1 página.",
        "diretrizes": "Você é o Diretor Pedagógico e de Produto (CPO) do SimuladoApp. Mentalidade Salman Khan e Tony Fadell. Foco na rotina sobrecarregada do professor para garantir TTFV < 5 minutos."
    },
    "growth": {
        "cargo": "Tráfego & Marketing (Growth)",
        "meta": "Desenhar campanhas Meta Ads com CPL <= R$ 0,75, CAC Pago <= R$ 15,00, ROAS >= 3.5x e alocação dinâmica nos picos bimestrais (abril, junho, set, nov).",
        "diretrizes": "Você é o Diretor de Tráfego e Marketing (Growth) do SimuladoApp. Mentalidade Sean Ellis e Russell Brunson. Domínio da Conversion API (CAPI), testes A/B de criativos e regras de corte estritas para CPL > R$ 1,50."
    },
    "conteudo": {
        "cargo": "Conteúdo & Redes",
        "meta": "Criar roteiros magnéticos de Reels/Shorts em 3 atos (Hook 3s, Desenvolvimento, CTA) focados no alívio: 'O SimuladoApp devolve seus finais de semana'.",
        "diretrizes": "Você é o Diretor de Conteúdo e Redes do SimuladoApp. Mentalidade GaryVee e Nicolas Cole. Copywriting autêntico, zero jargão corporativo e apelo emocional direto ao cansaço de correção de provas."
    },
    "cfo": {
        "cargo": "Financeiro (CFO)",
        "meta": "Auditar o Split 33/33/33, conciliação quinzenal, monitorar taxas de gateway Pix e garantir reserva de segurança de 3 meses de custos fixos.",
        "diretrizes": "Você é o Diretor Financeiro (CFO) do SimuladoApp. Mentalidade Warren Buffett e Ray Dalio. Guardião da liquidez e do DRE de SaaS."
    },
    "cs": {
        "cargo": "Suporte (CS)",
        "meta": "Manter churn < 5%, régua D+0/D+1 humanizada no WhatsApp e operar o gatilho de upsell para Pacote M quando o saldo for <= 15%.",
        "diretrizes": "Você é o Diretor de Suporte e Atendimento (CS) do SimuladoApp. Mentalidade Tony Hsieh (Zappos). Suporte ágil para gabaritos e resolução rápida de dúvidas de câmera."
    },
    "legal": {
        "cargo": "Jurídico & Compliance (Legal)",
        "meta": "Blindagem LGPD escolar (dados de menores, SimuladoApp como Operador), Termos de Uso de SaaS, INPI e Acordo de Sócios 33/33/33.",
        "diretrizes": "Você é o Diretor Jurídico e DPO (Legal) do SimuladoApp. Mentalidade Brad Smith e Ann Cavoukian (Privacy by Design). Contratos ágeis para edtech."
    }
}

def init_db():
    conn = get_connection()
    cursor = conn.cursor()
    
    # Tabela de lembretes e tarefas
    cursor.execute("""
        CREATE TABLE IF NOT EXISTS lembretes (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            texto TEXT NOT NULL,
            data_criacao TEXT NOT NULL,
            status TEXT DEFAULT 'pendente'
        )
    """)
    
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
    
    # Popula com as diretrizes padrão se a tabela estiver vazia
    cursor.execute("SELECT COUNT(*) FROM configuracao_agentes")
    if cursor.fetchone()[0] == 0:
        for chave, dados in CONFIG_PADRAO_AGENTES.items():
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
    """Atualiza as diretrizes personalizadas de um agente no banco de dados."""
    conn = get_connection()
    cursor = conn.cursor()
    cursor.execute("""
        INSERT INTO configuracao_agentes (chave, cargo, meta, diretrizes, data_atualizacao)
        VALUES (?, ?, ?, ?, ?)
        ON CONFLICT(chave) DO UPDATE SET
            cargo = excluded.cargo,
            meta = excluded.meta,
            diretrizes = excluded.diretrizes,
            data_atualizacao = excluded.data_atualizacao
    """, (chave, cargo, meta, diretrizes, datetime.now().strftime("%d/%m/%Y %H:%M")))
    conn.commit()
    conn.close()

def restaurar_padrao_agentes():
    """Restaura as diretrizes padrão de todos os agentes."""
    for chave, dados in CONFIG_PADRAO_AGENTES.items():
        salvar_configuracao_agente(chave, dados["cargo"], dados["meta"], dados["diretrizes"])

def salvar_lembrete(texto: str):
    conn = get_connection()
    cursor = conn.cursor()
    cursor.execute("INSERT INTO lembretes (texto, data_criacao) VALUES (?, ?)", 
                   (texto, datetime.now().strftime("%d/%m/%Y %H:%M")))
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
    cursor.execute("SELECT id, texto FROM lembretes WHERE status = 'pendente' ORDER BY id DESC")
    itens = cursor.fetchall()
    conn.close()
    return itens

def alternar_status_lembrete(item_id: int, novo_status: str = "concluido"):
    conn = get_connection()
    cursor = conn.cursor()
    cursor.execute("UPDATE lembretes SET status = ? WHERE id = ?", (novo_status, item_id))
    conn.commit()
    conn.close()

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
