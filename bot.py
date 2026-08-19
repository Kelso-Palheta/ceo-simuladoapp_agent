import os
import logging
import tempfile
from dotenv import load_dotenv
from telegram import Update
from telegram.ext import ApplicationBuilder, CommandHandler, MessageHandler, filters, ContextTypes
from database import init_db, salvar_lembrete, listar_lembretes_pendentes, registrar_consulta
from agents import executar_consulta_estrategica
from pdf_generator import gerar_pdf
from transcriber import transcrever_audio

load_dotenv()

logging.basicConfig(level=logging.INFO)

AUTHORIZED_USER = os.getenv("AUTHORIZED_USER_ID")

async def start(update: Update, context: ContextTypes.DEFAULT_TYPE):
    user_id = str(update.effective_user.id)
    if AUTHORIZED_USER and user_id != AUTHORIZED_USER:
        await update.message.reply_text("Acesso não autorizado.")
        return

    await update.message.reply_text(
        "👋 Olá! Sou o seu CEO Virtual & Assistente Executivo do SimuladoApp.\n\n"
        "Comandos e recursos disponíveis:\n"
        "• 🎙️ *Envie mensagens de voz/áudio* falando sua demanda diretamente.\n"
        "• 💬 *Envie mensagens de texto* para despachar com a Mesa Diretora.\n"
        "• `/pdf <demanda>` para gerar um relatório executivo em PDF formatado.\n"
        "• `/lembrete <texto>` para registrar uma tarefa na memória pessoal.\n"
        "• `/tarefas` para listar seus lembretes pendentes.",
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
            "`/pdf Gere um relatório financeiro do mês`\n"
            "`/pdf Crie um plano de marketing para setembro`\n\n"
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

async def handle_voice(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Processa mensagens de voz e arquivos de áudio enviados pelo fundador no Telegram."""
    user_id = str(update.effective_user.id)
    if AUTHORIZED_USER and user_id != AUTHORIZED_USER:
        return

    await update.message.reply_text("🎙️ *Ouvindo e transcrevendo seu áudio via Whisper...*", parse_mode="Markdown")

    try:
        # Obtém o arquivo de voz ou áudio
        arquivo_audio = update.message.voice or update.message.audio
        file_obj = await arquivo_audio.get_file()
        
        # Salva em arquivo temporário
        with tempfile.NamedTemporaryFile(suffix=".oga", delete=False) as temp_file:
            temp_path = temp_file.name

        await file_obj.download_to_drive(temp_path)

        # Transcrição via Groq Whisper Large v3
        texto_transcrito = transcrever_audio(temp_path)
        
        if os.path.exists(temp_path):
            os.remove(temp_path)

        if not texto_transcrito:
            await update.message.reply_text("⚠️ Não consegui compreender o áudio. Por favor, tente falar novamente.")
            return

        await update.message.reply_text(
            f"🗣️ *Entendi:* \"_{texto_transcrito}_\"\n\n⚙️ *Consultando a Mesa Diretora... Aguarde.*",
            parse_mode="Markdown"
        )

        # Executa consulta aos agentes
        resposta = await executar_consulta_estrategica(texto_transcrito)
        resposta_str = str(resposta)
        registrar_consulta("Telegram (Voz)", texto_transcrito, resposta_str)
        
        await enviar_resposta_longa(update, resposta_str)

    except Exception as e:
        logging.error(f"Erro ao processar áudio: {e}")
        await update.message.reply_text(f"⚠️ Erro ao processar mensagem de voz: {str(e)}")

async def handle_message(update: Update, context: ContextTypes.DEFAULT_TYPE):
    user_id = str(update.effective_user.id)
    if AUTHORIZED_USER and user_id != AUTHORIZED_USER:
        return

    texto_usuario = update.message.text
    await update.message.reply_text("⚙️ *Consultando a Mesa Diretora... Aguarde um instante.*", parse_mode="Markdown")

    try:
        resposta = await executar_consulta_estrategica(texto_usuario)
        resposta_str = str(resposta)
        registrar_consulta("Telegram", texto_usuario, resposta_str)
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
    app.add_handler(CommandHandler("pdf", handle_pdf))
    app.add_handler(MessageHandler(filters.VOICE | filters.AUDIO, handle_voice))
    app.add_handler(MessageHandler(filters.TEXT & ~filters.COMMAND, handle_message))

    print("🚀 Bot Executivo do SimuladoApp rodando...")
    app.run_polling()

if __name__ == "__main__":
    main()
