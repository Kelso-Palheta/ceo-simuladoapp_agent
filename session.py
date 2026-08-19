import asyncio
import os
import sys
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
from agents import executar_consulta_estrategica
from pdf_generator import gerar_pdf

load_dotenv()
init_db()

console = Console()

def exibir_banner():
    banner_text = (
        "[bold cyan]SimuladoApp[/bold cyan] — [bold yellow]Mesa Diretora Executiva[/bold yellow]\n"
        "[dim]Terminal de Decisão Estratégica Interativo (CLI/TUI)[/dim]"
    )
    console.print(Panel(banner_text, border_style="cyan", expand=False))
    console.print(
        "[dim]Comandos rápidos: [bold]/lembrete <texto>[/bold], [bold]/tarefas[/bold], [bold]/pdf[/bold], [bold]/sair[/bold] ou digite sua demanda.[/dim]\n"
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

async def processar_demanda(demanda: str, gerar_arquivo_pdf: bool = False):
    with console.status("[bold green]⏳ Convocando os 8 Diretores da Mesa Executiva...[/bold green]", spinner="dots"):
        try:
            resposta = await executar_consulta_estrategica(demanda)
            resposta_str = str(resposta)
            registrar_consulta("Terminal (CLI)", demanda, resposta_str)
        except Exception as e:
            console.print(f"[bold red]⚠️ Erro na consulta:[/bold red] {e}")
            return

    console.print()
    console.print(Panel(Markdown(resposta_str), title="[bold yellow]📄 Deliberação da Mesa Diretora[/bold yellow]", border_style="yellow"))
    
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
                    await processar_demanda(demanda, gerar_arquivo_pdf=True)
                else:
                    console.print("[red]Uso: /pdf <sua demanda estratégica>[/red]\n")
                    
            else:
                await processar_demanda(entrada, gerar_arquivo_pdf=False)
                
        except KeyboardInterrupt:
            console.print("\n[bold yellow]Sessão interrompida. Até logo![/bold yellow]")
            break
        except Exception as e:
            console.print(f"[red]Erro inesperado:[/red] {e}")

if __name__ == "__main__":
    asyncio.run(loop_principal())
