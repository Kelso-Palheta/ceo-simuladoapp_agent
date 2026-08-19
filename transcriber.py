import os
import io
import logging
from dotenv import load_dotenv
from groq import Groq

load_dotenv()

GROQ_API_KEY = os.getenv("GROQ_API_KEY")

def get_groq_client():
    if not GROQ_API_KEY:
        raise ValueError("GROQ_API_KEY não configurada no arquivo .env")
    return Groq(api_key=GROQ_API_KEY)

def transcrever_audio(caminho_arquivo: str) -> str:
    """
    Transcreve um arquivo de áudio (.ogg, .mp3, .wav, .m4a) em texto em português
    usando o modelo Whisper Large v3 da Groq.
    """
    try:
        client = get_groq_client()
        with open(caminho_arquivo, "rb") as file:
            transcricao = client.audio.transcriptions.create(
                file=(os.path.basename(caminho_arquivo), file.read()),
                model="whisper-large-v3",
                language="pt",
                response_format="text"
            )
        return str(transcricao).strip()
    except Exception as e:
        logging.error(f"Erro na transcrição de áudio: {e}")
        raise e

def transcrever_audio_bytes(dados_audio: bytes, nome_arquivo: str = "audio.wav") -> str:
    """
    Transcreve bytes de áudio diretamente da memória (útil para o Streamlit).
    """
    try:
        client = get_groq_client()
        transcricao = client.audio.transcriptions.create(
            file=(nome_arquivo, dados_audio),
            model="whisper-large-v3",
            language="pt",
            response_format="text"
        )
        return str(transcricao).strip()
    except Exception as e:
        logging.error(f"Erro na transcrição de bytes de áudio: {e}")
        raise e
