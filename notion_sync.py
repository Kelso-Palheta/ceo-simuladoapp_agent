import os
import re
from datetime import datetime
from dotenv import load_dotenv

try:
    from notion_client import Client
    NOTION_CLIENT_AVAILABLE = True
except ImportError:
    Client = None
    NOTION_CLIENT_AVAILABLE = False

load_dotenv()

NOTION_TOKEN = os.getenv("NOTION_API_KEY") or os.getenv("NOTION_TOKEN")
NOTION_PARENT_ID = os.getenv("NOTION_PAGE_ID") or os.getenv("NOTION_DATABASE_ID")

def is_notion_configurado() -> bool:
    """Verifica se as credenciais do Notion estão disponíveis."""
    return bool(NOTION_TOKEN and NOTION_PARENT_ID)

def _converter_texto_para_blocos_notion(texto_markdown: str):
    """Converte o Markdown retornado pelos agentes em blocos estruturados da API do Notion."""
    blocos = []
    linhas = texto_markdown.split("\n")
    
    for linha in linhas:
        linha_strip = linha.strip()
        if not linha_strip:
            continue
            
        # Títulos H1/H2/H3
        if linha_strip.startswith("### "):
            blocos.append({
                "object": "block",
                "type": "heading_3",
                "heading_3": {
                    "rich_text": [{"type": "text", "text": {"content": linha_strip[4:]}}]
                }
            })
        elif linha_strip.startswith("## "):
            blocos.append({
                "object": "block",
                "type": "heading_2",
                "heading_2": {
                    "rich_text": [{"type": "text", "text": {"content": linha_strip[3:]}}]
                }
            })
        elif linha_strip.startswith("# "):
            blocos.append({
                "object": "block",
                "type": "heading_1",
                "heading_1": {
                    "rich_text": [{"type": "text", "text": {"content": linha_strip[2:]}}]
                }
            })
        # Itens de Checklist / To-do
        elif linha_strip.startswith("- [ ] ") or linha_strip.startswith("- [x] "):
            checked = linha_strip.startswith("- [x] ")
            blocos.append({
                "object": "block",
                "type": "to_do",
                "to_do": {
                    "rich_text": [{"type": "text", "text": {"content": linha_strip[6:]}}],
                    "checked": checked
                }
            })
        # Bullet points
        elif linha_strip.startswith("- ") or linha_strip.startswith("• "):
            blocos.append({
                "object": "block",
                "type": "bulleted_list_item",
                "bulleted_list_item": {
                    "rich_text": [{"type": "text", "text": {"content": linha_strip[2:]}}]
                }
            })
        # Parágrafo comum
        else:
            # Limita a 2000 caracteres por bloco (limite da API do Notion)
            conteudo = linha_strip[:1900]
            blocos.append({
                "object": "block",
                "type": "paragraph",
                "paragraph": {
                    "rich_text": [{"type": "text", "text": {"content": conteudo}}]
                }
            })
            
    return blocos

def exportar_para_notion(demanda: str, resposta: str) -> dict:
    """
    Cria uma nova página no Notion com o plano executivo gerado pela Mesa Diretora.
    
    Returns:
        dict: {'sucesso': bool, 'url': str | None, 'mensagem': str}
    """
    if not NOTION_CLIENT_AVAILABLE:
        return {
            "sucesso": False,
            "url": None,
            "mensagem": "Biblioteca notion-client não encontrada. Execute 'pip install notion-client'."
        }

    if not is_notion_configurado():
        return {
            "sucesso": False,
            "url": None,
            "mensagem": "Credenciais NOTION_API_KEY ou NOTION_PAGE_ID não encontradas no arquivo .env."
        }
        
    try:
        notion = Client(auth=NOTION_TOKEN)
        data_str = datetime.now().strftime("%d/%m/%Y %H:%M")
        titulo_pagina = f"🏛️ Plano Executivo — {demanda[:45]} ({data_str})"
        
        blocos_corpo = _converter_texto_para_blocos_notion(resposta)
        
        # Bloco de destaque inicial com a demanda
        bloco_callout = {
            "object": "block",
            "type": "callout",
            "callout": {
                "rich_text": [{
                    "type": "text",
                    "text": {"content": f"Demanda do Fundador:\n\"{demanda}\""}
                }],
                "icon": {"emoji": "💡"}
            }
        }
        
        todos_blocos = [bloco_callout] + blocos_corpo
        
        # Cria a página filha
        nova_pagina = notion.pages.create(
            parent={"page_id": NOTION_PARENT_ID},
            properties={
                "title": {
                    "title": [{"type": "text", "text": {"content": titulo_pagina}}]
                }
            },
            children=todos_blocos[:90] # API limita criação inicial a 100 blocos
        )
        
        url_criada = nova_pagina.get("url")
        return {
            "sucesso": True,
            "url": url_criada,
            "mensagem": f"Página criada no Notion com sucesso!"
        }
    except Exception as e:
        return {
            "sucesso": False,
            "url": None,
            "mensagem": f"Erro ao sincronizar com o Notion: {str(e)}"
        }
