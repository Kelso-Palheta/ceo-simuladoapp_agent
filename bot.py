import os
import logging
from dotenv import load_dotenv
from telegram import Update
from telegram.ext import ApplicationBuilder, CommandHandler, MessageHandler, filters, ContextTypes
from database import init_db, salvar_lembrete, listar_lembretes_pendentes, registrar_consulta
from agents import executar_consulta_estrategica
from pdf_generator import gerar_pdf

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
        "Comandos disponíveis:\n"
        "• Envie qualquer dúvida ou demanda de negócio para acionar o Conselho.\n"
        "• `/lembrete <texto>` para registrar uma tarefa na memória pessoal.\n"
        "• `/tarefas` para listar seus lembretes pendentes.\n"
        "• `/pdf <demanda>` para receber a resposta como documento PDF formatado."
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
        # Consulta a Mesa Diretora
        resposta = await executar_consulta_estrategica(demanda)
        resposta_str = str(resposta)
        registrar_consulta("Telegram (/pdf)", demanda, resposta_str)

        # Gera o PDF
        caminho_pdf = gerar_pdf(resposta_str, demanda)

        # Envia o PDF como documento
        with open(caminho_pdf, "rb") as pdf_file:
            await update.message.reply_document(
                document=pdf_file,
                filename=os.path.basename(caminho_pdf),
                caption=f"📋 Relatório gerado pela Mesa Diretora do SimuladoApp.\n\nDemanda: \"{demanda}\""
            )

        # Remove o arquivo temporário
        os.remove(caminho_pdf)

        # Também envia um resumo curto no chat
        resumo = resposta_str[:500] + "..." if len(resposta_str) > 500 else resposta_str
        await update.message.reply_text(f"📌 *Resumo rápido:*\n\n{resumo}", parse_mode="Markdown")

    except Exception as e:
        logging.error(f"Erro ao gerar PDF: {e}")
        await update.message.reply_text(f"⚠️ Ocorreu um erro ao gerar o documento: {str(e)}")

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
    app.add_handler(MessageHandler(filters.TEXT & ~filters.COMMAND, handle_message))

    print("🚀 Bot Executivo do SimuladoApp rodando...")
    app.run_polling()

if __name__ == "__main__":
    main()
