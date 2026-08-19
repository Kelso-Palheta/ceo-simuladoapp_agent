import sqlite3
from datetime import datetime
import os

DB_NAME = os.getenv("DB_PATH", "simulado_memory.db")

def get_connection():
    """Retorna uma conexão configurada com WAL mode e timeout seguro para concorrência."""
    conn = sqlite3.connect(DB_NAME, timeout=15)
    conn.execute("PRAGMA journal_mode=WAL;")
    conn.execute("PRAGMA busy_timeout = 5000;")
    return conn

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
    
    # Tabela de notas e diretrizes
    cursor.execute("""
        CREATE TABLE IF NOT EXISTS notas (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            categoria TEXT NOT NULL,
            conteudo TEXT NOT NULL,
            data_registro TEXT NOT NULL
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
    
    conn.commit()
    conn.close()

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

def listar_historico_consultas(limite: int = 30):
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
