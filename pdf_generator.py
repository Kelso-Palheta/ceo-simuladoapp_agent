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
    """PDF customizado com header e footer executivos."""

    def __init__(self, titulo: str = "Relatório Executivo"):
        super().__init__()
        self.titulo_relatorio = titulo
        self.data_geracao = datetime.now().strftime("%d/%m/%Y às %H:%M")

        # Adiciona fonte Unicode (DejaVu) para suportar acentos e caracteres especiais
        font_dir = os.path.join(os.path.dirname(__file__), "fonts")
        if os.path.exists(os.path.join(font_dir, "DejaVuSans.ttf")):
            self.add_font("DejaVu", "", os.path.join(font_dir, "DejaVuSans.ttf"), uni=True)
            self.add_font("DejaVu", "B", os.path.join(font_dir, "DejaVuSans-Bold.ttf"), uni=True)
            self.add_font("DejaVu", "I", os.path.join(font_dir, "DejaVuSans-Oblique.ttf"), uni=True)
            self.font_family_name = "DejaVu"
        else:
            # Fallback para Helvetica (sem suporte completo a Unicode, mas funcional)
            self.font_family_name = "Helvetica"

    def header(self):
        # Barra superior colorida
        self.set_fill_color(15, 23, 42)  # Slate-900
        self.rect(0, 0, 210, 28, "F")

        # Linha de destaque dourada
        self.set_fill_color(234, 179, 8)  # Amarelo/Dourado
        self.rect(0, 28, 210, 1.5, "F")

        # Título do relatório
        self.set_font(self.font_family_name, "B", 16)
        self.set_text_color(255, 255, 255)
        self.set_y(6)
        self.cell(0, 10, self.titulo_relatorio, ln=True, align="C")

        # Subtítulo com data
        self.set_font(self.font_family_name, "", 8)
        self.set_text_color(148, 163, 184)  # Slate-400
        self.cell(0, 5, f"SimuladoApp | Mesa Diretora | {self.data_geracao}", ln=True, align="C")

        self.ln(10)

    def footer(self):
        self.set_y(-15)
        self.set_font(self.font_family_name, "I", 7)
        self.set_text_color(100, 116, 139)  # Slate-500
        self.cell(0, 10, f"CEO Virtual SimuladoApp — Documento gerado automaticamente — Pag. {self.page_no()}/{{nb}}", align="C")

    def adicionar_secao(self, titulo: str, conteudo: str):
        """Adiciona uma seção com título destacado e conteúdo formatado."""
        # Título da seção
        self.set_font(self.font_family_name, "B", 13)
        self.set_text_color(15, 23, 42)  # Slate-900

        # Barra lateral colorida antes do título
        x = self.get_x()
        y = self.get_y()
        self.set_fill_color(234, 179, 8)  # Dourado
        self.rect(x, y, 3, 8, "F")
        self.set_x(x + 6)
        self.cell(0, 8, titulo, ln=True)
        self.ln(2)

        # Conteúdo
        self.set_font(self.font_family_name, "", 10)
        self.set_text_color(30, 41, 59)  # Slate-800
        self.multi_cell(0, 6, conteudo)
        self.ln(4)

    def adicionar_bullet(self, texto: str):
        """Adiciona um item com bullet point."""
        self.set_font(self.font_family_name, "", 10)
        self.set_text_color(30, 41, 59)
        x = self.get_x()
        self.set_x(x + 6)
        self.cell(5, 6, chr(8226))  # Bullet character
        self.multi_cell(0, 6, texto)
        self.ln(1)


def _limpar_markdown(texto: str) -> str:
    """Remove formatação Markdown básica mantendo o texto legível."""
    # Remove ** (bold)
    texto = re.sub(r'\*\*(.*?)\*\*', r'\1', texto)
    # Remove * (italic)
    texto = re.sub(r'\*(.*?)\*', r'\1', texto)
    # Remove __ (bold)
    texto = re.sub(r'__(.*?)__', r'\1', texto)
    # Remove _ (italic)
    texto = re.sub(r'_(.*?)_', r'\1', texto)
    # Remove ```code blocks```
    texto = re.sub(r'```[\s\S]*?```', '', texto)
    # Remove `inline code`
    texto = re.sub(r'`(.*?)`', r'\1', texto)
    # Remove links [text](url) -> text
    texto = re.sub(r'\[(.*?)\]\(.*?\)', r'\1', texto)
    return texto.strip()


def _detectar_titulo(demanda: str) -> str:
    """Gera um título curto e descritivo baseado na demanda do usuário."""
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
        "reel": "Roteiro de Conteúdo",
        "suporte": "Plano de Suporte",
        "cs": "Plano de Customer Success",
        "churn": "Análise de Churn",
        "preço": "Análise de Precificação",
        "preco": "Análise de Precificação",
        "seman": "Plano Semanal Executivo",
        "mensal": "Plano Mensal Executivo",
        "estratég": "Plano Estratégico",
        "estrateg": "Plano Estratégico",
        "prioridade": "Relatório de Prioridades",
        "relatório": "Relatório Executivo",
        "relatorio": "Relatório Executivo",
    }

    for key, titulo in keywords.items():
        if key in demanda_lower:
            return titulo

    return "Relatório Executivo"


def gerar_pdf(conteudo_resposta: str, demanda_usuario: str = "") -> str:
    """
    Gera um PDF formatado a partir da resposta dos agentes.

    Args:
        conteudo_resposta: Texto da resposta dos agentes (pode conter Markdown).
        demanda_usuario: A pergunta/demanda original do usuário (para gerar título).

    Returns:
        Caminho absoluto do arquivo PDF gerado.
    """
    titulo = _detectar_titulo(demanda_usuario)
    conteudo_limpo = _limpar_markdown(conteudo_resposta)

    pdf = RelatorioPDF(titulo=titulo)
    pdf.alias_nb_pages()
    pdf.add_page()
    pdf.set_auto_page_break(auto=True, margin=20)

    # Adiciona a demanda original como contexto
    if demanda_usuario:
        pdf.set_font(pdf.font_family_name, "I", 9)
        pdf.set_text_color(100, 116, 139)  # Slate-500
        pdf.multi_cell(0, 5, f'Demanda: "{demanda_usuario}"')
        pdf.ln(4)

        # Linha separadora fina
        pdf.set_draw_color(226, 232, 240)  # Slate-200
        pdf.line(10, pdf.get_y(), 200, pdf.get_y())
        pdf.ln(6)

    # Divide o conteúdo em seções (detecta padrões de título como "1.", "##", "###", etc.)
    linhas = conteudo_limpo.split("\n")
    secao_atual_titulo = ""
    secao_atual_conteudo = []

    for linha in linhas:
        linha_strip = linha.strip()

        # Detecta títulos de seção (## Título, ### Título, 1. Título, etc.)
        is_titulo = False
        titulo_limpo = ""

        if linha_strip.startswith("## ") or linha_strip.startswith("### "):
            titulo_limpo = re.sub(r'^#{2,3}\s*', '', linha_strip)
            is_titulo = True
        elif re.match(r'^\d+\.\s+[A-Z]', linha_strip):
            titulo_limpo = linha_strip
            is_titulo = True

        if is_titulo and titulo_limpo:
            # Salva a seção anterior
            if secao_atual_titulo and secao_atual_conteudo:
                texto_secao = "\n".join(secao_atual_conteudo).strip()
                if texto_secao:
                    pdf.adicionar_secao(secao_atual_titulo, texto_secao)

            secao_atual_titulo = titulo_limpo
            secao_atual_conteudo = []
        elif linha_strip.startswith("- ") or linha_strip.startswith("• "):
            # Bullet points
            bullet_text = re.sub(r'^[-•]\s*', '', linha_strip)
            secao_atual_conteudo.append(f"  • {bullet_text}")
        elif linha_strip:
            secao_atual_conteudo.append(linha_strip)

    # Salva a última seção
    if secao_atual_titulo and secao_atual_conteudo:
        texto_secao = "\n".join(secao_atual_conteudo).strip()
        if texto_secao:
            pdf.adicionar_secao(secao_atual_titulo, texto_secao)
    elif secao_atual_conteudo:
        # Se não detectou nenhuma seção, coloca tudo como corpo de texto
        pdf.set_font(pdf.font_family_name, "", 10)
        pdf.set_text_color(30, 41, 59)
        texto_completo = "\n".join(secao_atual_conteudo).strip()
        pdf.multi_cell(0, 6, texto_completo)
    elif not secao_atual_titulo:
        # Fallback: coloca o conteúdo inteiro como texto corrido
        pdf.set_font(pdf.font_family_name, "", 10)
        pdf.set_text_color(30, 41, 59)
        pdf.multi_cell(0, 6, conteudo_limpo)

    # Gera nome do arquivo com timestamp
    timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
    nome_arquivo = f"relatorio_{timestamp}.pdf"
    caminho = os.path.join(tempfile.gettempdir(), nome_arquivo)

    pdf.output(caminho)
    return caminho
