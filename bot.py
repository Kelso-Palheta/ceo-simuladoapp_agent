import os
import logging
import tempfile
import re
from dotenv import load_dotenv
from telegram import Update
from telegram.ext import ApplicationBuilder, CommandHandler, MessageHandler, filters, ContextTypes
from database import (
    init_db,
    salvar_lembrete,
    listar_lembretes_pendentes,
    registrar_consulta,
    listar_historico_consultas
)
from agents import executar_consulta_estrategica, MAPA_AGENTES, normalizar_agente
from pdf_generator import gerar_pdf
from transcriber import transcrever_audio
from document_reader import extrair_texto_documento

load_dotenv()

logging.basicConfig(level=logging.INFO)

AUTHORIZED_USER = os.getenv("AUTHORIZED_USER_ID")

def extrair_agente_mencionado(texto: str):
    """Detecta se o texto começa com uma menção a um agente específico (ex: @cto, @cfo, cto:, etc.)"""
    match = re.match(r'^[@/]?([a-zA-Z]+)[:\s]+(.*)$', texto.strip(), re.DOTALL)
    if match:
        tag = match.group(1).lower()
        resto = match.group(2).strip()
        tag_normalizada = normalizar_agente(tag)
        if tag_normalizada in MAPA_AGENTES:
            return tag_normalizada, resto
    return None, texto

async def start(update: Update, context: ContextTypes.DEFAULT_TYPE):
    user_id = str(update.effective_user.id)
    if AUTHORIZED_USER and user_id != AUTHORIZED_USER:
        await update.message.reply_text("Acesso não autorizado.")
        return

    await update.message.reply_text(
        "👋 Olá! Sou o seu CEO Virtual & Assistente Executivo do SimuladoApp.\n\n"
        "🏛️ *Mesa Geral (Todos os 8 Diretores):*\n"
        "• Envie qualquer áudio, texto ou documento (PDF/DOCX) para análise.\n"
        "• `/pdf <demanda>` para gerar Relatório Executivo em PDF.\n"
        "• `/historico` para consultar as últimas deliberações.\n\n"
        "🎯 *Consultas Diretas (Econômicas e Rápidas):*\n"
        "• `/ceo <ideia>` ou `@ceo` — Sparring Estratégico 1-a-1 & Alinhamento\n"
        "• `/tecnologia <demanda>` ou `@tecnologia` (ou `/cto`) — Tecnologia, Dev & Mini-PRD\n"
        "• `/financeiro <demanda>` ou `@financeiro` (ou `/cfo`) — Finanças, DRE & Split 33%\n"
        "• `/suporte <demanda>` ou `@suporte` (ou `/cs`) — Atendimento, Retenção & Alunos\n"
        "• `/trafego <demanda>` ou `@trafego` (ou `/marketing`, `/growth`) — Tráfego Pago & Meta Ads\n"
        "• `/conteudo <demanda>` ou `@conteudo` — Roteiros de Reels, Redes & Copy\n"
        "• `/pedagogico <demanda>` ou `@pedagogico` (ou `/cpo`) — Provas, BNCC, SAEB & UX\n"
        "• `/juridico <demanda>` ou `@juridico` (ou `/legal`) — LGPD, Contratos & Compliance\n\n"
        "📋 *Gestão de Tarefas:*\n"
        "• `/lembrete <texto>` para registrar tarefa.\n"
        "• `/tarefas` para listar tarefas pendentes.",
        parse_mode="Markdown"
    )

async def handle_lembrete(update: Update, context: ContextTypes.DEFAULT_TYPE):
    texto = " ".join(context.args)
    if not texto:
        await update.message.reply_text("Uso correto: `/lembrete Comprar folhas A4`")
        return
    salvar_lembrete(texto)
    await update.message.reply_text(f"✅ Lembrete salvo com sucesso:\n_{texto}_", parse_mode="Markdown")

async def handle_tarefas(update: Update, context: ContextTypes.DEFAULT_TYPE):
    itens = listar_lembretes_pendentes()
    if not itens:
        await update.message.reply_text("Nenhum lembrete pendente no momento!")
        return
    
    msg = "📋 *Seus Lembretes Pendentes:*\n\n"
    for item_id, texto in itens:
        msg += f"• [{item_id}] {texto}\n"
    await update.message.reply_text(msg, parse_mode="Markdown")

async def handle_historico(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Lista as últimas 5 consultas registradas."""
    user_id = str(update.effective_user.id)
    if AUTHORIZED_USER and user_id != AUTHORIZED_USER:
        return

    itens = listar_historico_consultas(limite=5)
    if not itens:
        await update.message.reply_text("Nenhuma consulta registrada no histórico ainda.")
        return

    msg = "📜 *Últimas 5 Deliberações Executivas:*\n\n"
    for h_id, canal, demanda, resposta, data_reg in itens:
        resumo = resposta[:120].replace("\n", " ") + "..."
        msg += f"🕒 *[{data_reg}]* ({canal})\n📌 *Demanda:* {demanda[:70]}\n💡 *Parecer:* _{resumo}_\n\n"
    
    msg += "💡 *Dica:* Para acessar todos os relatórios completos e exportar PDFs antigos, acesse o Dashboard Web na aba *Histórico de Decisões*."
    await update.message.reply_text(msg, parse_mode="Markdown")

async def enviar_resposta_longa(update: Update, texto: str):
    """Divide a resposta em partes de no máximo 4000 caracteres para respeitar o limite do Telegram (4096)."""
    tamanho_max = 4000
    for i in range(0, len(texto), tamanho_max):
        chunk = texto[i:i + tamanho_max]
        await update.message.reply_text(chunk)

async def handle_pdf(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Comando /pdf - Gera a resposta da Mesa Diretora como um documento PDF formatado."""
    user_id = str(update.effective_user.id)
    if AUTHORIZED_USER and user_id != AUTHORIZED_USER:
        return

    demanda = " ".join(context.args)
    if not demanda:
        await update.message.reply_text(
            "📄 *Uso do comando /pdf:*\n\n"
            "`/pdf Qual a prioridade estratégica da semana?`\n"
            "`/pdf Gere um relatório financeiro do mês`\n\n"
            "A Mesa Diretora vai analisar e entregar um PDF executivo formatado.",
            parse_mode="Markdown"
        )
        return

    await update.message.reply_text("📄 *Gerando documento executivo... Aguarde um instante.*", parse_mode="Markdown")

    try:
        resposta = await executar_consulta_estrategica(demanda)
        resposta_str = str(resposta)
        registrar_consulta("Telegram (/pdf)", demanda, resposta_str)

        caminho_pdf = gerar_pdf(resposta_str, demanda)

        with open(caminho_pdf, "rb") as pdf_file:
            await update.message.reply_document(
                document=pdf_file,
                filename=os.path.basename(caminho_pdf),
                caption=f"📋 Relatório gerado pela Mesa Diretora do SimuladoApp.\n\nDemanda: \"{demanda}\""
            )

        if os.path.exists(caminho_pdf):
            os.remove(caminho_pdf)

        resumo = resposta_str[:500] + "..." if len(resposta_str) > 500 else resposta_str
        await update.message.reply_text(f"📌 *Resumo rápido:*\n\n{resumo}", parse_mode="Markdown")

    except Exception as e:
        logging.error(f"Erro ao gerar PDF: {e}")
        await update.message.reply_text(f"⚠️ Ocorreu um erro ao gerar o documento: {str(e)}")

async def handle_direto_especialista(update: Update, context: ContextTypes.DEFAULT_TYPE, agente_nome: str):
    """Handler genérico para comandos /ceo, /cto, /cfo, /growth, etc."""
    user_id = str(update.effective_user.id)
    if AUTHORIZED_USER and user_id != AUTHORIZED_USER:
        return

    demanda = " ".join(context.args)
    if not demanda:
        titulo = MAPA_AGENTES[agente_nome][1]
        await update.message.reply_text(f"Uso: `/{agente_nome} <sua dúvida ou demanda para {titulo}>`", parse_mode="Markdown")
        return

    titulo = MAPA_AGENTES[agente_nome][1]
    await update.message.reply_text(f"⚙️ *Consultando diretamente {titulo}...*", parse_mode="Markdown")

    try:
        resposta = await executar_consulta_estrategica(demanda, agentes_alvo=agente_nome)
        resposta_str = str(resposta)
        registrar_consulta(f"Telegram (/{agente_nome})", demanda, resposta_str)
        await enviar_resposta_longa(update, resposta_str)
    except Exception as e:
        await update.message.reply_text(f"⚠️ Erro ao consultar {titulo}: {str(e)}")

async def handle_voice(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Processa mensagens de voz e arquivos de áudio enviados pelo fundador no Telegram."""
    user_id = str(update.effective_user.id)
    if AUTHORIZED_USER and user_id != AUTHORIZED_USER:
        return

    await update.message.reply_text("🎙️ *Ouvindo e transcrevendo seu áudio via Whisper...*", parse_mode="Markdown")

    try:
        arquivo_audio = update.message.voice or update.message.audio
        file_obj = await arquivo_audio.get_file()
        
        with tempfile.NamedTemporaryFile(suffix=".oga", delete=False) as temp_file:
            temp_path = temp_file.name

        await file_obj.download_to_drive(temp_path)
        texto_transcrito = transcrever_audio(temp_path)
        
        if os.path.exists(temp_path):
            os.remove(temp_path)

        if not texto_transcrito:
            await update.message.reply_text("⚠️ Não consegui compreender o áudio. Por favor, tente falar novamente.")
            return

        agente_detectado, demanda_real = extrair_agente_mencionado(texto_transcrito)
        
        if agente_detectado:
            titulo = MAPA_AGENTES[agente_detectado][1]
            await update.message.reply_text(
                f"🗣️ *Entendi:* \"_{texto_transcrito}_\"\n\n🎯 *Direcionando exclusivamente para {titulo}...*",
                parse_mode="Markdown"
            )
            resposta = await executar_consulta_estrategica(demanda_real, agentes_alvo=agente_detectado)
            canal = f"Telegram (Voz @{agente_detectado})"
        else:
            await update.message.reply_text(
                f"🗣️ *Entendi:* \"_{texto_transcrito}_\"\n\n⚙️ *Consultando a Mesa Diretora Completa...*",
                parse_mode="Markdown"
            )
            resposta = await executar_consulta_estrategica(texto_transcrito)
            canal = "Telegram (Voz)"

        resposta_str = str(resposta)
        registrar_consulta(canal, texto_transcrito, resposta_str)
        await enviar_resposta_longa(update, resposta_str)

    except Exception as e:
        logging.error(f"Erro ao processar áudio: {e}")
        await update.message.reply_text(f"⚠️ Erro ao processar mensagem de voz: {str(e)}")

async def handle_document(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Processa documentos enviados no Telegram (.pdf, .docx, .txt, .md)."""
    user_id = str(update.effective_user.id)
    if AUTHORIZED_USER and user_id != AUTHORIZED_USER:
        return

    doc = update.message.document
    caption = update.message.caption or "Revise e analise este documento estrategicamente."
    
    await update.message.reply_text(f"📄 *Recebi o arquivo '{doc.file_name}'. Extraindo conteúdo para análise...*", parse_mode="Markdown")

    try:
        file_obj = await doc.get_file()
        with tempfile.NamedTemporaryFile(suffix=os.path.splitext(doc.file_name)[1], delete=False) as temp_file:
            temp_path = temp_file.name

        await file_obj.download_to_drive(temp_path)
        with open(temp_path, "rb") as f:
            bytes_doc = f.read()

        texto_doc = extrair_texto_documento(bytes_doc, doc.file_name)
        if os.path.exists(temp_path):
            os.remove(temp_path)

        agente_detectado, demanda_real = extrair_agente_mencionado(caption)
        demanda_completa = f"{demanda_real}\n\n--- DOCUMENTO ANEXADO ({doc.file_name}) ---\n{texto_doc}"

        if agente_detectado:
            titulo = MAPA_AGENTES[agente_detectado][1]
            await update.message.reply_text(f"🎯 *Direcionando documento para análise de {titulo}...*", parse_mode="Markdown")
            resposta = await executar_consulta_estrategica(demanda_completa, agentes_alvo=agente_detectado)
            canal = f"Telegram (Doc @{agente_detectado})"
        else:
            await update.message.reply_text("⚙️ *Consultando a Mesa Diretora sobre o documento...*", parse_mode="Markdown")
            resposta = await executar_consulta_estrategica(demanda_completa)
            canal = "Telegram (Doc)"

        resposta_str = str(resposta)
        registrar_consulta(canal, f"{caption} [{doc.file_name}]", resposta_str)
        await enviar_resposta_longa(update, resposta_str)

    except Exception as e:
        logging.error(f"Erro ao processar documento: {e}")
        await update.message.reply_text(f"⚠️ Erro ao processar documento: {str(e)}")

async def handle_message(update: Update, context: ContextTypes.DEFAULT_TYPE):
    user_id = str(update.effective_user.id)
    if AUTHORIZED_USER and user_id != AUTHORIZED_USER:
        return

    texto_usuario = update.message.text
    agente_detectado, demanda_real = extrair_agente_mencionado(texto_usuario)

    try:
        if agente_detectado:
            titulo = MAPA_AGENTES[agente_detectado][1]
            await update.message.reply_text(f"⚙️ *Consultando diretamente {titulo}...*", parse_mode="Markdown")
            resposta = await executar_consulta_estrategica(demanda_real, agentes_alvo=agente_detectado)
            canal = f"Telegram (@{agente_detectado})"
        else:
            await update.message.reply_text("⚙️ *Consultando a Mesa Diretora Completa...*", parse_mode="Markdown")
            resposta = await executar_consulta_estrategica(texto_usuario)
            canal = "Telegram"

        resposta_str = str(resposta)
        registrar_consulta(canal, texto_usuario, resposta_str)
        await enviar_resposta_longa(update, resposta_str)
    except Exception as e:
        await update.message.reply_text(f"⚠️ Ocorreu um erro na orquestração: {str(e)}")

def main():
    init_db()
    token = os.getenv("TELEGRAM_BOT_TOKEN")
    app = ApplicationBuilder().token(token).build()

    app.add_handler(CommandHandler("start", start))
    app.add_handler(CommandHandler("lembrete", handle_lembrete))
    app.add_handler(CommandHandler("tarefas", handle_tarefas))
    app.add_handler(CommandHandler("historico", handle_historico))
    app.add_handler(CommandHandler("pdf", handle_pdf))

    # Comandos individuais para economizar tokens (Português + Siglas)
    COMANDOS_ALIAS = {
        "ceo": "ceo",
        "tecnologia": "cto",
        "tech": "cto",
        "dev": "cto",
        "cto": "cto",
        "financeiro": "cfo",
        "financas": "cfo",
        "cfo": "cfo",
        "suporte": "cs",
        "atendimento": "cs",
        "cs": "cs",
        "trafego": "growth",
        "marketing": "growth",
        "growth": "growth",
        "conteudo": "conteudo",
        "copy": "conteudo",
        "pedagogico": "cpo",
        "produto": "cpo",
        "cpo": "cpo",
        "juridico": "legal",
        "legal": "legal",
    }

    for cmd, chave_agente in COMANDOS_ALIAS.items():
        app.add_handler(CommandHandler(cmd, lambda u, c, k=chave_agente: handle_direto_especialista(u, c, k)))

    app.add_handler(MessageHandler(filters.VOICE | filters.AUDIO, handle_voice))
    app.add_handler(MessageHandler(filters.Document.ALL, handle_document))
    app.add_handler(MessageHandler(filters.TEXT & ~filters.COMMAND, handle_message))

    print("🚀 Bot Executivo do SimuladoApp rodando...")
    app.run_polling(drop_pending_updates=True, allowed_updates=Update.ALL_TYPES, close_loop=False)

if __name__ == "__main__":
    main()
