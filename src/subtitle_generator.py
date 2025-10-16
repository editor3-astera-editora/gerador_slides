"""
Módulo para gerar legendas sincronizadas a partir da transcrição Whisper.
"""

import json
from pathlib import Path


def gerar_legendas_srt(transcricao_json_path, output_path=None, max_palavras_por_legenda=10):
    """
    Gera arquivo de legendas SRT a partir da transcrição Whisper.

    Args:
        transcricao_json_path (Path): Caminho para o JSON de transcrição
        output_path (Path): Caminho para salvar o arquivo .srt (opcional)
        max_palavras_por_legenda (int): Máximo de palavras por legenda

    Returns:
        str: Conteúdo do arquivo SRT
    """
    transcricao_json_path = Path(transcricao_json_path)

    if not transcricao_json_path.exists():
        raise FileNotFoundError(f"Arquivo de transcrição não encontrado: {transcricao_json_path}")

    print(f"Gerando legendas a partir de {transcricao_json_path.name}...")

    # Carregar transcrição
    with open(transcricao_json_path, 'r', encoding='utf-8') as f:
        dados = json.load(f)

    palavras = dados.get("palavras", [])

    if not palavras:
        raise ValueError("Nenhuma palavra encontrada no arquivo de transcrição")

    # Agrupar palavras em legendas
    legendas = agrupar_palavras_em_legendas(palavras, max_palavras_por_legenda)

    print(f"OK {len(legendas)} legendas geradas")

    # Gerar conteúdo SRT
    conteudo_srt = gerar_conteudo_srt(legendas)

    # Salvar arquivo se caminho fornecido
    if output_path:
        output_path = Path(output_path)
        output_path.parent.mkdir(parents=True, exist_ok=True)

        with open(output_path, 'w', encoding='utf-8') as f:
            f.write(conteudo_srt)

        print(f"OK Legendas salvas em: {output_path}")

    return conteudo_srt


def agrupar_palavras_em_legendas(palavras, max_palavras=10, max_duracao=5.0):
    """
    Agrupa palavras em legendas com número limitado de palavras e duração.

    Args:
        palavras (list): Lista de palavras com timestamps
        max_palavras (int): Máximo de palavras por legenda
        max_duracao (float): Duração máxima de uma legenda em segundos

    Returns:
        list: Lista de legendas {texto, inicio, fim}
    """
    legendas = []
    grupo_atual = []
    timestamp_inicio_grupo = None

    for palavra in palavras:
        texto = palavra["palavra"]
        inicio = palavra["inicio"]
        fim = palavra["fim"]

        # Inicia novo grupo se necessário
        if not grupo_atual:
            timestamp_inicio_grupo = inicio

        grupo_atual.append(texto)
        timestamp_fim_grupo = fim

        # Verifica se deve finalizar o grupo
        duracao_grupo = timestamp_fim_grupo - timestamp_inicio_grupo
        deve_finalizar = (
            len(grupo_atual) >= max_palavras or
            duracao_grupo >= max_duracao
        )

        if deve_finalizar:
            # Cria legenda
            legenda = {
                "texto": " ".join(grupo_atual),
                "inicio": timestamp_inicio_grupo,
                "fim": timestamp_fim_grupo
            }
            legendas.append(legenda)

            # Reseta grupo
            grupo_atual = []
            timestamp_inicio_grupo = None

    # Adiciona último grupo se houver
    if grupo_atual:
        legenda = {
            "texto": " ".join(grupo_atual),
            "inicio": timestamp_inicio_grupo,
            "fim": timestamp_fim_grupo
        }
        legendas.append(legenda)

    return legendas


def gerar_conteudo_srt(legendas):
    """
    Gera o conteúdo de um arquivo SRT a partir das legendas.

    Formato SRT:
    1
    00:00:00,500 --> 00:00:02,000
    Texto da primeira legenda

    2
    00:00:02,500 --> 00:00:04,000
    Texto da segunda legenda

    Args:
        legendas (list): Lista de legendas {texto, inicio, fim}

    Returns:
        str: Conteúdo do arquivo SRT
    """
    linhas = []

    for i, legenda in enumerate(legendas, 1):
        # Número da legenda
        linhas.append(str(i))

        # Timestamps
        inicio_str = formatar_timestamp_srt(legenda["inicio"])
        fim_str = formatar_timestamp_srt(legenda["fim"])
        linhas.append(f"{inicio_str} --> {fim_str}")

        # Texto
        linhas.append(legenda["texto"])

        # Linha em branco (separador)
        linhas.append("")

    return "\n".join(linhas)


def formatar_timestamp_srt(segundos):
    """
    Formata timestamp em segundos para o formato SRT (HH:MM:SS,mmm).

    Args:
        segundos (float): Tempo em segundos

    Returns:
        str: Timestamp formatado (ex: "00:01:23,450")
    """
    horas = int(segundos // 3600)
    minutos = int((segundos % 3600) // 60)
    segs = int(segundos % 60)
    milissegundos = int((segundos - int(segundos)) * 1000)

    return f"{horas:02d}:{minutos:02d}:{segs:02d},{milissegundos:03d}"


def criar_legendas_para_moviepy(transcricao_json_path, max_palavras_por_legenda=10):
    """
    Cria lista de legendas para uso direto com moviepy.

    Args:
        transcricao_json_path (Path): Caminho para o JSON de transcrição
        max_palavras_por_legenda (int): Máximo de palavras por legenda

    Returns:
        list: Lista de tuplas (inicio, fim, texto)
    """
    transcricao_json_path = Path(transcricao_json_path)

    # Carregar transcrição
    with open(transcricao_json_path, 'r', encoding='utf-8') as f:
        dados = json.load(f)

    palavras = dados.get("palavras", [])

    if not palavras:
        raise ValueError("Nenhuma palavra encontrada no arquivo de transcrição")

    # Agrupar palavras em legendas
    legendas = agrupar_palavras_em_legendas(palavras, max_palavras_por_legenda)

    # Converter para formato moviepy: (inicio, fim, texto)
    legendas_moviepy = [
        (leg["inicio"], leg["fim"], leg["texto"])
        for leg in legendas
    ]

    return legendas_moviepy


def exibir_preview_legendas(legendas, max_preview=10):
    """
    Exibe preview das primeiras legendas no console.

    Args:
        legendas (list): Lista de legendas {texto, inicio, fim}
        max_preview (int): Máximo de legendas a exibir
    """
    print("\n" + "=" * 70)
    print("PREVIEW DAS LEGENDAS")
    print("=" * 70)

    for i, legenda in enumerate(legendas[:max_preview], 1):
        inicio = legenda["inicio"]
        fim = legenda["fim"]
        texto = legenda["texto"]

        print(f"\n[Legenda {i}]")
        print(f"  Tempo: {inicio:.2f}s → {fim:.2f}s")
        print(f"  Texto: {texto}")

    if len(legendas) > max_preview:
        print(f"\n... e mais {len(legendas) - max_preview} legendas")

    print("\n" + "=" * 70)
    print(f"Total de legendas: {len(legendas)}")
    print("=" * 70)
