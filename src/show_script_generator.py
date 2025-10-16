"""
Módulo para gerar o script de apresentação (guião).
Cria eventos SHOW_SLIDE com timestamps sincronizados.
"""

import json
from pathlib import Path


def gerar_show_script(slides_json_path, output_path=None):
    """
    Gera um script de apresentação a partir do arquivo de slides.

    O script contém eventos SHOW_SLIDE com timestamps para sincronização
    de vídeo. Cada slide tem:
    - timestamp: tempo em segundos para mostrar o slide
    - action: tipo de ação (sempre 'SHOW_SLIDE')
    - slide_index: índice do slide (começando em 0)

    Args:
        slides_json_path (Path): Caminho para o arquivo *_slides.json
        output_path (Path): Caminho para salvar o show_script.json (opcional)

    Returns:
        list: Lista de eventos do script de apresentação
    """
    slides_json_path = Path(slides_json_path)

    if not slides_json_path.exists():
        raise FileNotFoundError(f"Arquivo de slides não encontrado: {slides_json_path}")

    print(f"Gerando script de apresentação a partir de {slides_json_path.name}...")

    # Carregar slides
    with open(slides_json_path, 'r', encoding='utf-8') as f:
        dados = json.load(f)

    slides = dados.get("slides", [])

    if not slides:
        raise ValueError("Nenhum slide encontrado no arquivo JSON")

    # Gerar eventos SHOW_SLIDE
    show_script = []

    for i, slide in enumerate(slides):
        timestamp = slide.get("timestamp_inicio", 0.0)
        tipo = slide.get("tipo", "")
        titulo = slide.get("slide_title", "Sem Título")

        evento = {
            "timestamp": timestamp,
            "action": "SHOW_SLIDE",
            "slide_index": i,
            "metadata": {
                "tipo": tipo,
                "titulo": titulo[:50]  # Primeiros 50 caracteres para referência
            }
        }

        show_script.append(evento)

        print(f"  Evento {i+1}: SHOW_SLIDE aos {timestamp:.2f}s - {titulo[:40]}...")

    print(f"\nOK {len(show_script)} eventos gerados")

    # Salvar script se caminho fornecido
    if output_path:
        output_path = Path(output_path)
        output_path.parent.mkdir(parents=True, exist_ok=True)

        with open(output_path, 'w', encoding='utf-8') as f:
            json.dump(show_script, f, ensure_ascii=False, indent=2)

        print(f"OK Script de apresentação salvo em: {output_path}")

    return show_script


def calcular_duracoes_slides(show_script, duracao_total_audio):
    """
    Calcula a duração de cada slide baseado nos timestamps.

    Args:
        show_script (list): Lista de eventos do script
        duracao_total_audio (float): Duração total do áudio em segundos

    Returns:
        list: Lista de tuplas (slide_index, timestamp_inicio, duracao)
    """
    duracoes = []

    for i, evento in enumerate(show_script):
        timestamp_inicio = evento["timestamp"]
        slide_index = evento["slide_index"]

        # Calcula duração até o próximo slide (ou até o fim do áudio)
        if i + 1 < len(show_script):
            timestamp_fim = show_script[i + 1]["timestamp"]
        else:
            timestamp_fim = duracao_total_audio

        duracao = timestamp_fim - timestamp_inicio

        duracoes.append((slide_index, timestamp_inicio, duracao))

    return duracoes


def validar_show_script(show_script):
    """
    Valida e corrige o script de apresentação automaticamente.

    Verifica:
    - Timestamps em ordem crescente (corrige automaticamente)
    - Remove eventos com timestamp 0.0 inválidos
    - Índices de slides sequenciais
    - Estrutura correta dos eventos

    Args:
        show_script (list): Lista de eventos do script

    Returns:
        tuple: (valido: bool, erros: list)
    """
    erros = []

    # Verifica se há eventos
    if not show_script:
        erros.append("Script de apresentação está vazio")
        return False, erros

    # CORREÇÃO 1: Remover eventos com timestamp 0.0 inválidos (exceto o primeiro)
    eventos_validos = []
    for i, evento in enumerate(show_script):
        timestamp = evento.get("timestamp", 0.0)
        # Mantém primeiro evento mesmo com 0.0, remove outros com 0.0
        if i == 0 or timestamp > 0.0:
            eventos_validos.append(evento)
        else:
            print(f"  Aviso: Removendo evento {i} com timestamp inválido (0.0)")

    show_script[:] = eventos_validos

    # CORREÇÃO 2: Ordenar eventos por timestamp
    eventos_desordenados = []
    for i in range(1, len(show_script)):
        if show_script[i]["timestamp"] < show_script[i-1]["timestamp"]:
            eventos_desordenados.append(i)

    if eventos_desordenados:
        print(f"  Aviso: Corrigindo {len(eventos_desordenados)} evento(s) fora de ordem")
        show_script.sort(key=lambda x: x["timestamp"])
        # Recalcular slide_index após ordenação
        for i, evento in enumerate(show_script):
            evento["slide_index"] = i

    # Verifica ordem dos timestamps (após correção)
    timestamps_anteriores = -1
    for i, evento in enumerate(show_script):
        timestamp = evento.get("timestamp")

        if timestamp is None:
            erros.append(f"Evento {i} não tem timestamp")
            continue

        if timestamp < timestamps_anteriores:
            erros.append(f"Evento {i}: timestamp {timestamp} ainda está fora de ordem")

        timestamps_anteriores = timestamp

    # Verifica estrutura dos eventos
    for i, evento in enumerate(show_script):
        if "action" not in evento:
            erros.append(f"Evento {i} não tem campo 'action'")

        if "slide_index" not in evento:
            erros.append(f"Evento {i} não tem campo 'slide_index'")

        if evento.get("action") != "SHOW_SLIDE":
            erros.append(f"Evento {i}: action desconhecida '{evento.get('action')}'")

    valido = len(erros) == 0

    return valido, erros


def exibir_preview_show_script(show_script, duracao_audio=None):
    """
    Exibe um preview do script de apresentação no console.

    Args:
        show_script (list): Lista de eventos do script
        duracao_audio (float): Duração total do áudio (opcional)
    """
    print("\n" + "=" * 70)
    print("PREVIEW DO SCRIPT DE APRESENTAÇÃO")
    print("=" * 70)

    if duracao_audio:
        duracoes = calcular_duracoes_slides(show_script, duracao_audio)
    else:
        duracoes = None

    for i, evento in enumerate(show_script):
        timestamp = evento["timestamp"]
        slide_index = evento["slide_index"]
        titulo = evento.get("metadata", {}).get("titulo", "N/A")

        print(f"\n[Evento {i+1}] SHOW_SLIDE")
        print(f"  Timestamp: {timestamp:.2f}s")
        print(f"  Slide: #{slide_index}")
        print(f"  Título: {titulo}")

        if duracoes:
            _, _, duracao = duracoes[i]
            print(f"  Duração: {duracao:.2f}s")

    print("\n" + "=" * 70)
    print(f"Total de eventos: {len(show_script)}")
    if duracao_audio:
        print(f"Duração total do áudio: {duracao_audio:.2f}s")
    print("=" * 70)
