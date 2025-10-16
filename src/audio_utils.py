"""
Módulo para manipulação de arquivos de áudio.
"""

from pathlib import Path


def obter_primeiro_audio(pasta_audios):
    """
    Obtém o primeiro arquivo de áudio encontrado na pasta especificada.

    Args:
        pasta_audios (Path): Path para a pasta de áudios

    Returns:
        Path: Caminho do arquivo de áudio encontrado

    Raises:
        FileNotFoundError: Se nenhum arquivo de áudio for encontrado
    """
    extensoes_audio = ['.mp3', '.wav', '.m4a', '.mp4', '.mpeg', '.mpga', '.webm']

    for arquivo in pasta_audios.iterdir():
        if arquivo.suffix.lower() in extensoes_audio:
            return arquivo

    raise FileNotFoundError(f"Nenhum arquivo de áudio encontrado na pasta {pasta_audios}")


def validar_pasta_audios(pasta_audios):
    """
    Valida se a pasta de áudios existe.

    Args:
        pasta_audios (Path): Path para a pasta de áudios

    Raises:
        FileNotFoundError: Se a pasta não existir
    """
    if not pasta_audios.exists():
        raise FileNotFoundError("A pasta 'audios/' não existe.")
