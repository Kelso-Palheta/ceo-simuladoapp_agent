import asyncio
import os
import sys
import re
from dotenv import load_dotenv
from rich.console import Console
from rich.panel import Panel
from rich.markdown import Markdown
from rich.table import Table
from rich.prompt import Prompt
from database import (
    init_db,
    salvar_lembrete,
    listar_lembretes_pendentes,
    registrar_consulta
)
from agents import executar_consulta_estrategica, MAPA_AGENTES, normalizar_agente
from pdf_generator import gerar_pdf

load_dotenv()
init_db()

console = Console()

def extrair_agente_mencionado(texto: str):
    match = re.match(r'^[@/]?([a-zA-Z]+)[:\s]+(.*)$', texto.strip(), re.DOTALL)
    if match:
        tag = match.group(1).lower()
        resto = match.group(2).strip()
        tag_normalizada = normalizar_agente(tag)
        if tag_normalizada in MAPA_AGENTES:
            return tag_normalizada, resto
    return None, texto

def exibir_banner():
    banner_text = (
        "[bold cyan]SimuladoApp[/bold cyan] — [bold yellow]Mesa Diretora Executiva[/bold yellow]\n"
        "[dim]Terminal de Decisão Estratégica Interativo (CLI/TUI)[/dim]"
    )
    console.print(Panel(banner_text, border_style="cyan", expand=False))
    console.print(
        "[dim]Mesa Geral: digite sua demanda | Direto: [bold]@cto[/bold], [bold]@cfo[/bold], [bold]@growth[/bold], [bold]@conteudo[/bold], [bold]@cpo[/bold], [bold]@cs[/bold], [bold]@legal[/bold] | [bold]/tarefas[/bold], [bold]/pdf[/bold], [bold]/sair[/bold][/dim]\n"
    )

def exibir_tarefas():
    itens = listar_lembretes_pendentes()
    if not itens:
        console.print("[green]✅ Nenhuma tarefa pendente no momento![/green]\n")
        return
    
    table = Table(title="📋 Lembretes & Tarefas Pendentes", border_style="yellow")
    table.add_column("ID", style="cyan", justify="center")
    table.add_column("Descrição", style="white")
    
    for item_id, texto in itens:
        table.add_row(str(item_id), texto)
        
    console.print(table)
    console.print()

async def processar_demanda(demanda: str, agente_alvo: str | None = None, gerar_arquivo_pdf: bool = False):
    if agente_alvo:
        titulo = MAPA_AGENTES[agente_alvo][1]
        msg_status = f"[bold green]⏳ Consultando diretamente {titulo}...[/bold green]"
    else:
        titulo = "Mesa Diretora Completa"
        msg_status = "[bold green]⏳ Convocando os 8 Diretores da Mesa Executiva...[/bold green]"

    with console.status(msg_status, spinner="dots"):
        try:
            resposta = await executar_consulta_estrategica(demanda, agentes_alvo=agente_alvo)
            resposta_str = str(resposta)
            canal = f"Terminal (CLI @{agente_alvo})" if agente_alvo else "Terminal (CLI)"
            registrar_consulta(canal, demanda, resposta_str)
        except Exception as e:
            console.print(f"[bold red]⚠️ Erro na consulta:[/bold red] {e}")
            return

    console.print()
    console.print(Panel(Markdown(resposta_str), title=f"[bold yellow]📄 Parecer — {titulo}[/bold yellow]", border_style="yellow"))
    
    if gerar_arquivo_pdf:
        try:
            caminho_pdf = gerar_pdf(resposta_str, demanda)
            console.print(f"\n[bold green]📄 PDF executivo gerado com sucesso em:[/bold green] [cyan]{caminho_pdf}[/cyan]")
        except Exception as ex:
            console.print(f"\n[bold red]⚠️ Falha ao exportar PDF:[/bold red] {ex}")

async def loop_principal():
    exibir_banner()
    
    while True:
        try:
            entrada = Prompt.ask("[bold cyan]Fundador[/bold cyan]").strip()
            
            if not entrada:
                continue
                
            if entrada.lower() in ["/sair", "sair", "exit", "quit"]:
                console.print("[bold yellow]Encerrando sessão executiva. Até logo![/bold yellow]")
                break
                
            elif entrada.startswith("/lembrete"):
                partes = entrada.split(" ", 1)
                if len(partes) > 1 and partes[1].strip():
                    texto = partes[1].strip()
                    salvar_lembrete(texto)
                    console.print(f"[bold green]✅ Lembrete salvo:[/bold green] {texto}\n")
                else:
                    console.print("[red]Uso: /lembrete <sua tarefa aqui>[/red]\n")
                    
            elif entrada.startswith("/tarefas"):
                exibir_tarefas()
                
            elif entrada.startswith("/pdf"):
                partes = entrada.split(" ", 1)
                if len(partes) > 1 and partes[1].strip():
                    demanda = partes[1].strip()
                    agente_det, dem_real = extrair_agente_mencionado(demanda)
                    await processar_demanda(dem_real, agente_alvo=agente_det, gerar_arquivo_pdf=True)
                else:
                    console.print("[red]Uso: /pdf <sua demanda estratégica>[/red]\n")
                    
            else:
                agente_det, dem_real = extrair_agente_mencionado(entrada)
                await processar_demanda(dem_real, agente_alvo=agente_det, gerar_arquivo_pdf=False)
                
        except KeyboardInterrupt:
            console.print("\n[bold yellow]Sessão interrompida. Até logo![/bold yellow]")
            break
        except Exception as e:
            console.print(f"[red]Erro inesperado:[/red] {e}")

if __name__ == "__main__":
    asyncio.run(loop_principal())
