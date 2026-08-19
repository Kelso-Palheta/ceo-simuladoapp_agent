"""
Módulo de geração de PDFs executivos para o CEO Virtual do SimuladoApp.
Converte a resposta dos agentes em documentos PDF formatados e profissionais.
"""

import os
import re
import tempfile
from datetime import datetime
from fpdf import FPDF


class RelatorioPDF(FPDF):
    """PDF customizado com header e footer executivos usando fontes nativas do fpdf2."""

    def __init__(self, titulo: str = "Relatório Executivo"):
        super().__init__()
        self.titulo_relatorio = titulo
        self.data_geracao = datetime.now().strftime("%d/%m/%Y às %H:%M")
        self.font_family_name = "Helvetica"

    def header(self):
        # Barra superior escura
        self.set_fill_color(15, 23, 42)  # Slate-900
        self.rect(0, 0, 210, 28, "F")

        # Linha de destaque dourada
        self.set_fill_color(234, 179, 8)  # Amarelo/Dourado
        self.rect(0, 28, 210, 1.5, "F")

        # Título do relatório
        self.set_font(self.font_family_name, "B", 15)
        self.set_text_color(255, 255, 255)
        self.set_y(6)
        self.cell(0, 10, self.titulo_relatorio, align="C", new_x="LMARGIN", new_y="NEXT")

        # Subtítulo com data
        self.set_font(self.font_family_name, "", 8)
        self.set_text_color(148, 163, 184)  # Slate-400
        self.cell(0, 5, f"SimuladoApp | Mesa Diretora | {self.data_geracao}", align="C", new_x="LMARGIN", new_y="NEXT")

        self.ln(10)

    def footer(self):
        self.set_y(-15)
        self.set_font(self.font_family_name, "I", 7)
        self.set_text_color(100, 116, 139)  # Slate-500
        self.cell(0, 10, f"CEO Virtual SimuladoApp - Documento gerado automaticamente - Pag. {self.page_no()}/{{nb}}", align="C")

    def adicionar_secao(self, titulo: str, conteudo: str):
        """Adiciona uma seção com título destacado e conteúdo formatado."""
        self.set_font(self.font_family_name, "B", 12)
        self.set_text_color(15, 23, 42)  # Slate-900

        # Barra lateral dourada antes do título
        x = self.get_x()
        y = self.get_y()
        self.set_fill_color(234, 179, 8)
        self.rect(x, y, 3, 7, "F")
        self.set_x(x + 6)
        self.cell(0, 7, titulo, new_x="LMARGIN", new_y="NEXT")
        self.ln(2)

        # Conteúdo
        self.set_font(self.font_family_name, "", 10)
        self.set_text_color(30, 41, 59)  # Slate-800
        self.multi_cell(0, 5, conteudo)
        self.ln(4)


def _sanitizar_texto(texto: str) -> str:
    """Remove formatação Markdown e caracteres incompatíveis com latin-1."""
    # Remove marcações markdown
    texto = re.sub(r'\*\*(.*?)\*\*', r'\1', texto)
    texto = re.sub(r'\*(.*?)\*', r'\1', texto)
    texto = re.sub(r'__(.*?)__', r'\1', texto)
    texto = re.sub(r'_(.*?)_', r'\1', texto)
    texto = re.sub(r'```[\s\S]*?```', '', texto)
    texto = re.sub(r'`(.*?)`', r'\1', texto)
    texto = re.sub(r'\[(.*?)\]\(.*?\)', r'\1', texto)
    
    # Substitui emojis e caracteres especiais por equivalentes amigáveis
    substituicoes = {
        "—": "-", "–": "-", "“": '"', "”": '"', "‘": "'", "’": "'",
        "•": "-", "✔": "[x]", "✅": "[OK]", "❌": "[X]", "⚠️": "[!]",
        "👑": "", "💻": "", "🎓": "", "💰": "", "🎧": "", "⚖️": "", "✍️": "", "📈": "",
        "🚀": "", "📋": "", "📄": "", "📌": "", "💡": "", "🏛️": ""
    }
    for k, v in substituicoes.items():
        texto = texto.replace(k, v)
        
    # Garante compatibilidade de encoding com latin-1
    return texto.encode("latin-1", errors="replace").decode("latin-1").strip()


def _detectar_titulo(demanda: str) -> str:
    demanda_lower = demanda.lower()
    keywords = {
        "financ": "Relatório Financeiro",
        "marketing": "Plano de Marketing",
        "growth": "Estratégia de Growth",
        "técnic": "Relatório Técnico",
        "tecnic": "Relatório Técnico",
        "arquitetura": "Relatório de Arquitetura",
        "jurídic": "Parecer Jurídico",
        "juridic": "Parecer Jurídico",
        "legal": "Parecer Jurídico",
        "lgpd": "Parecer LGPD",
        "compliance": "Parecer de Compliance",
        "pedagóg": "Relatório Pedagógico",
        "pedagogic": "Relatório Pedagógico",
        "ux": "Relatório de UX/Produto",
        "produto": "Relatório de Produto",
        "conteúdo": "Plano de Conteúdo",
        "conteudo": "Plano de Conteúdo",
        "social": "Plano de Social Media",
        "suporte": "Plano de Suporte",
        "cs": "Plano de Customer Success",
        "churn": "Análise de Churn",
        "preço": "Análise de Precificação",
        "preco": "Análise de Precificação",
        "seman": "Plano Semanal Executivo",
        "estratég": "Plano Estratégico",
        "estrateg": "Plano Estratégico",
    }
    for key, tit in keywords.items():
        if key in demanda_lower:
            return tit
    return "Relatório Executivo"


def gerar_pdf(conteudo_resposta: str, demanda_usuario: str = "") -> str:
    titulo = _sanitizar_texto(_detectar_titulo(demanda_usuario))
    conteudo_limpo = _sanitizar_texto(conteudo_resposta)

    pdf = RelatorioPDF(titulo=titulo)
    pdf.alias_nb_pages()
    pdf.add_page()
    pdf.set_auto_page_break(auto=True, margin=15)

    if demanda_usuario:
        demanda_limpa = _sanitizar_texto(demanda_usuario)
        pdf.set_font("Helvetica", "I", 9)
        pdf.set_text_color(100, 116, 139)
        pdf.multi_cell(0, 5, f'Demanda: "{demanda_limpa}"')
        pdf.ln(3)
        pdf.set_draw_color(226, 232, 240)
        pdf.line(10, pdf.get_y(), 200, pdf.get_y())
        pdf.ln(5)

    linhas = conteudo_limpo.split("\n")
    secao_titulo = ""
    secao_corpo = []

    for linha in linhas:
        l_strip = linha.strip()
        is_tit = False
        t_clean = ""

        if l_strip.startswith("## ") or l_strip.startswith("### "):
            t_clean = re.sub(r'^#{2,3}\s*', '', l_strip)
            is_tit = True
        elif re.match(r'^\d+\.\s+[A-Z]', l_strip):
            t_clean = l_strip
            is_tit = True

        if is_tit and t_clean:
            if secao_titulo and secao_corpo:
                txt = "\n".join(secao_corpo).strip()
                if txt:
                    pdf.adicionar_secao(secao_titulo, txt)
            secao_titulo = t_clean
            secao_corpo = []
        elif l_strip.startswith("- ") or l_strip.startswith("• "):
            b_txt = re.sub(r'^[-•]\s*', '', l_strip)
            secao_corpo.append(f"  - {b_txt}")
        elif l_strip:
            secao_corpo.append(l_strip)

    if secao_titulo and secao_corpo:
        txt = "\n".join(secao_corpo).strip()
        if txt:
            pdf.adicionar_secao(secao_titulo, txt)
    elif secao_corpo:
        pdf.set_font("Helvetica", "", 10)
        pdf.set_text_color(30, 41, 59)
        pdf.multi_cell(0, 5, "\n".join(secao_corpo).strip())
    elif not secao_titulo:
        pdf.set_font("Helvetica", "", 10)
        pdf.set_text_color(30, 41, 59)
        pdf.multi_cell(0, 5, conteudo_limpo)

    timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
    nome_arquivo = f"relatorio_{timestamp}.pdf"
    caminho = os.path.join(tempfile.gettempdir(), nome_arquivo)

    pdf.output(caminho)
    return caminho
