import io
import os
from pypdf import PdfReader
from docx import Document

def extrair_texto_documento(conteudo_bytes: bytes, nome_arquivo: str, max_chars: int = 15000) -> str:
    """
    Extrai o conteúdo textual de arquivos PDF, DOCX, TXT, MD, CSV ou JSON.
    Limita o texto a max_chars para garantir conformidade com limites de tokens.
    """
    ext = os.path.splitext(nome_arquivo.lower())[1]
    texto_extraido = ""

    try:
        if ext == ".pdf":
            reader = PdfReader(io.BytesIO(conteudo_bytes))
            paginas_texto = []
            for i, pagina in enumerate(reader.pages):
                txt = pagina.extract_text() or ""
                if txt.strip():
                    paginas_texto.append(f"--- Página {i+1} ---\n{txt}")
            texto_extraido = "\n\n".join(paginas_texto)

        elif ext in [".docx", ".doc"]:
            doc = Document(io.BytesIO(conteudo_bytes))
            paragrafos = [p.text for p in doc.paragraphs if p.text.strip()]
            texto_extraido = "\n".join(paragrafos)

        elif ext in [".txt", ".md", ".json", ".csv", ".py", ".html", ".js"]:
            texto_extraido = conteudo_bytes.decode("utf-8", errors="replace")

        else:
            texto_extraido = conteudo_bytes.decode("utf-8", errors="replace")

    except Exception as e:
        return f"[Erro ao ler arquivo {nome_arquivo}: {str(e)}]"

    texto_extraido = texto_extraido.strip()
    if len(texto_extraido) > max_chars:
        texto_extraido = texto_extraido[:max_chars] + f"\n\n... [Conteúdo truncado após {max_chars} caracteres para segurança de contexto]"

    return texto_extraido
