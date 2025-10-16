"""
Módulo para transcrição de áudio usando a API Whisper.
"""

from openai import OpenAI


def criar_cliente(api_key):
    """
    Cria e retorna um cliente OpenAI configurado.

    Args:
        api_key (str): Chave da API OpenAI

    Returns:
        OpenAI: Cliente configurado
    """
    return OpenAI(api_key=api_key)


def transcrever_audio(client, audio_file_path):
    """
    Transcreve o arquivo de áudio usando a API Whisper.

    Args:
        client (OpenAI): Cliente OpenAI configurado
        audio_file_path (Path): Caminho para o arquivo de áudio

    Returns:
        Objeto de transcrição com timestamps
    """
    print(f"Arquivo selecionado: {audio_file_path.name}")
    print("Enviando arquivo para a API da OpenAI...")

    with open(audio_file_path, "rb") as audio_file:
        transcript = client.audio.transcriptions.create(
            model="whisper-1",
            file=audio_file,
            response_format="verbose_json",
            timestamp_granularities=["word"]
        )

    print("Transcrição recebida.")
    return transcript


def processar_transcricao(transcript):
    """
    Processa a transcrição e extrai as palavras com timestamps.

    Args:
        transcript: Objeto de transcrição da API

    Returns:
        list: Lista de dicionários com informações de cada palavra
    """
    palavras_com_timestamps = []

    if hasattr(transcript, 'words') and transcript.words:
        # Formato direto com palavras
        for word_info in transcript.words:
            palavras_com_timestamps.append({
                'palavra': word_info.word,
                'inicio': round(word_info.start, 2),
                'fim': round(word_info.end, 2)
            })
    elif hasattr(transcript, 'segments') and transcript.segments:
        # Formato com segmentos
        for segment in transcript.segments:
            if 'words' in segment:
                for word_info in segment['words']:
                    palavras_com_timestamps.append({
                        'palavra': word_info['word'],
                        'inicio': round(word_info['start'], 2),
                        'fim': round(word_info['end'], 2)
                    })

    return palavras_com_timestamps
