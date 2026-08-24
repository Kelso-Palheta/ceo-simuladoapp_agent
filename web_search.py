import urllib.request
import urllib.parse
import re
from html import unescape
from crewai.tools import tool

def _buscar_duckduckgo_lite(query: str, max_resultados: int = 5) -> str:
    """Executa busca web leve sem dependência de chaves externas pagas."""
    url = "https://html.duckduckgo.com/html/?q=" + urllib.parse.quote(query)
    req = urllib.request.Request(
        url,
        headers={"User-Agent": "Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36"}
    )
    try:
        with urllib.request.urlopen(req, timeout=12) as resp:
            html = resp.read().decode("utf-8", errors="ignore")
        
        matches = re.findall(r"<a class=\"result__snippet\"[^>]*>(.*?)</a>", html, re.DOTALL)
        links = re.findall(r"<a class=\"result__url\"[^>]*href=\"(.*?)\"[^>]*>(.*?)</a>", html, re.DOTALL)
        
        results = []
        for i, snippet in enumerate(matches[:max_resultados]):
            clean_snip = re.sub(r"<.*?>", "", snippet).strip()
            clean_snip = unescape(clean_snip)
            raw_link = links[i][0].strip() if i < len(links) else ""
            
            # Decodifica link real se for redirect do DuckDuckGo
            if "uddg=" in raw_link:
                try:
                    real_link = urllib.parse.unquote(raw_link.split("uddg=")[1].split("&")[0])
                except Exception:
                    real_link = raw_link
            else:
                real_link = raw_link
                
            results.append(f"• **Resumo:** {clean_snip}\n  **Fonte:** {real_link}")
            
        if not results:
            return "Nenhum resultado direto encontrado na web para esta busca."
        return "\n\n".join(results)
    except Exception as e:
        return f"Erro ao consultar a web: {str(e)}"

@tool("Pesquisar na Web em Tempo Real")
def pesquisar_na_web(termo_busca: str) -> str:
    """
    Pesquisa na internet em tempo real para obter informações atualizadas sobre:
    concorrentes, preços de mercado, ferramentas de educação, tendências de tráfego pago,
    notícias recentes e artigos relevantes.
    """
    return _buscar_duckduckgo_lite(termo_busca, max_resultados=5)
