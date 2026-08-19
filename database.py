import sqlite3
from datetime import datetime

DB_NAME = "simulado_memory.db"

def init_db():
    conn = sqlite3.connect(DB_NAME)
    cursor = conn.cursor()
    cursor.execute("""
        CREATE TABLE IF NOT EXISTS lembretes (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            texto TEXT NOT NULL,
            data_criacao TEXT NOT NULL,
            status TEXT DEFAULT 'pendente'
        )
    """)
    cursor.execute("""
        CREATE TABLE IF NOT EXISTS notas (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            categoria TEXT NOT NULL,
            conteudo TEXT NOT NULL,
            data_registro TEXT NOT NULL
        )
    """)
    conn.commit()
    conn.close()

def salvar_lembrete(texto: str):
    conn = sqlite3.connect(DB_NAME)
    cursor = conn.cursor()
    cursor.execute("INSERT INTO lembretes (texto, data_criacao) VALUES (?, ?)", 
                   (texto, datetime.now().isoformat()))
    conn.commit()
    conn.close()

def listar_lembretes_pendentes():
    conn = sqlite3.connect(DB_NAME)
    cursor = conn.cursor()
    cursor.execute("SELECT id, texto FROM lembretes WHERE status = 'pendente'")
    itens = cursor.fetchall()
    conn.close()
    return itens
