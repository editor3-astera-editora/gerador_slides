"""
Módulo para segmentação semântica de transcrições usando LLM.
"""

import json
from openai import OpenAI
from src.prompts import CHUNKING_PROMPT
from difflib import SequenceMatcher


def carregar_transcricao_json(json_path):
    """
    Carrega a transcrição do arquivo JSON.

    Args:
        json_path (Path): Caminho para o arquivo JSON de transcrição

    Returns:
        dict: Dicionário com dados da transcrição
    """
    with open(json_path, 'r', encoding='utf-8') as f:
        return json.load(f)


def segmentar_transcricao(client, palavras_com_timestamps):
    """
    Segmenta a transcrição em chunks semânticos usando GPT.
    GPT retorna marcadores textuais, não índices numéricos.

    Args:
        client (OpenAI): Cliente OpenAI configurado
        palavras_com_timestamps (list): Lista de palavras com timestamps

    Returns:
        list: Lista de chunks com marcador_inicio e marcador_fim
    """
    print("\nAnalisando estrutura do conteúdo com IA...")

    # Reconstrói o texto completo para análise
    texto_completo = " ".join([p["palavra"] for p in palavras_com_timestamps])

    # Envia apenas o texto (não os índices - GPT identifica apenas marcadores)
    prompt_dados = f"""TEXTO COMPLETO DA TRANSCRIÇÃO:

{texto_completo}

---

TAREFA: Identifique os blocos conceituais e retorne os marcadores de início/fim de cada um."""

    # Envia para GPT
    response = client.chat.completions.create(
        model="gpt-4o",
        messages=[
            {"role": "system", "content": CHUNKING_PROMPT},
            {"role": "user", "content": prompt_dados}
        ],
        temperature=0.2,
        response_format={"type": "json_object"}
    )

    # Parse da resposta
    resultado = json.loads(response.choices[0].message.content)
    chunks = resultado.get("chunks", [])

    print(f"OK Identificados {len(chunks)} blocos conceituais")

    return chunks


def normalizar_para_busca(texto):
    """
    Normaliza texto para busca (mantém case, remove apenas espaços extras).

    Args:
        texto (str): Texto a normalizar

    Returns:
        str: Texto normalizado
    """
    return " ".join(texto.split())


def encontrar_marcador_no_audio(marcador, palavras_com_timestamps, inicio_busca=0):
    """
    Encontra um marcador textual no array de palavras usando fuzzy matching.

    Args:
        marcador (str): Texto do marcador a buscar
        palavras_com_timestamps (list): Array de palavras com timestamps
        inicio_busca (int): Índice a partir do qual buscar

    Returns:
        int: Índice da primeira palavra do marcador, ou None se não encontrar
    """
    marcador_norm = normalizar_para_busca(marcador)
    palavras_marcador = marcador_norm.split()
    num_palavras = len(palavras_marcador)

    if num_palavras == 0:
        return None

    melhor_match = None
    melhor_similaridade = 0.0

    # Busca janela deslizante
    for i in range(inicio_busca, len(palavras_com_timestamps) - num_palavras + 1):
        # Extrai janela de palavras
        janela = [palavras_com_timestamps[j]["palavra"] for j in range(i, i + num_palavras)]
        janela_texto = " ".join(janela)

        # Calcula similaridade
        similaridade = SequenceMatcher(None, marcador_norm.lower(), janela_texto.lower()).ratio()

        # Aceita match se similaridade >= 0.8
        if similaridade >= 0.8 and similaridade > melhor_similaridade:
            melhor_match = i
            melhor_similaridade = similaridade

            # Se match perfeito, retorna imediatamente
            if similaridade >= 0.95:
                return i

    if melhor_match is not None and melhor_similaridade >= 0.8:
        return melhor_match

    return None


def encontrar_indices_chunk(chunk_dict, palavras_com_timestamps, inicio_busca=0):
    """
    Encontra os índices palavra_inicio e palavra_fim de um chunk usando marcadores textuais.

    Args:
        chunk_dict (dict): Chunk com marcador_inicio e marcador_fim
        palavras_com_timestamps (list): Array de palavras com timestamps
        inicio_busca (int): Índice a partir do qual buscar

    Returns:
        tuple: (palavra_inicio, palavra_fim, sucesso)
    """
    marcador_inicio = chunk_dict.get("marcador_inicio", "")
    marcador_fim = chunk_dict.get("marcador_fim", "")

    # Busca marcador de início
    idx_inicio = encontrar_marcador_no_audio(marcador_inicio, palavras_com_timestamps, inicio_busca)

    if idx_inicio is None:
        print(f"  ERRO: Não encontrou marcador_inicio: '{marcador_inicio}'")
        return (None, None, False)

    # Busca marcador de fim (a partir do início encontrado)
    idx_fim_marcador = encontrar_marcador_no_audio(marcador_fim, palavras_com_timestamps, idx_inicio)

    if idx_fim_marcador is None:
        print(f"  ERRO: Não encontrou marcador_fim: '{marcador_fim}'")
        return (None, None, False)

    # Calcula palavra_fim: última palavra do marcador de fim
    num_palavras_fim = len(marcador_fim.split())
    palavra_fim = idx_fim_marcador + num_palavras_fim - 1

    return (idx_inicio, palavra_fim, True)


def extrair_texto_chunk(palavras_com_timestamps, palavra_inicio, palavra_fim):
    """
    Extrai o texto de um chunk baseado nos índices de palavras.

    Args:
        palavras_com_timestamps (list): Lista completa de palavras
        palavra_inicio (int): Índice da primeira palavra
        palavra_fim (int): Índice da última palavra

    Returns:
        str: Texto do chunk
    """
    if palavra_inicio is None or palavra_fim is None:
        return ""
    palavras_chunk = palavras_com_timestamps[palavra_inicio:palavra_fim + 1]
    return " ".join([p["palavra"] for p in palavras_chunk])


def preparar_chunks_com_texto(palavras_com_timestamps, chunks):
    """
    Adiciona o texto extraído a cada chunk usando busca determinística por marcadores.

    Args:
        palavras_com_timestamps (list): Lista completa de palavras
        chunks (list): Lista de chunks da segmentação (com marcador_inicio/fim)

    Returns:
        list: Chunks enriquecidos com texto e índices
    """
    chunks_com_texto = []
    inicio_busca = 0  # Mantém posição sequencial

    for i, chunk in enumerate(chunks):
        # Encontra índices usando marcadores textuais
        palavra_inicio, palavra_fim, sucesso = encontrar_indices_chunk(
            chunk,
            palavras_com_timestamps,
            inicio_busca
        )

        if not sucesso:
            print(f"  AVISO: Chunk {i+1} ({chunk.get('tipo')}) - Pulando devido a erro na busca")
            continue

        # Extrai texto usando índices encontrados
        texto = extrair_texto_chunk(palavras_com_timestamps, palavra_inicio, palavra_fim)

        # Calcula timestamp_inicio
        timestamp_inicio = palavras_com_timestamps[palavra_inicio]["inicio"]

        # Adiciona chunk com todos os dados
        chunks_com_texto.append({
            "tipo": chunk.get("tipo"),
            "titulo_conceito": chunk.get("titulo_conceito"),
            "palavra_inicio": palavra_inicio,
            "palavra_fim": palavra_fim,
            "timestamp_inicio": timestamp_inicio,
            "texto": texto
        })

        # Atualiza posição de busca para próximo chunk
        inicio_busca = palavra_fim + 1

    return chunks_com_texto
