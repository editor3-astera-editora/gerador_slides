"""
Módulo para exibição e salvamento de resultados da transcrição.
"""

import json
from pathlib import Path


def exibir_resultados(palavras_com_timestamps):
    """
    Exibe os resultados da transcrição no console.

    Args:
        palavras_com_timestamps (list): Lista de palavras com timestamps
    """
    print("\n" + "=" * 70)
    print("TRANSCRIÇÃO COM TIMESTAMPS")
    print("=" * 70 + "\n")

    for palavra_info in palavras_com_timestamps:
        print(f"Palavra: '{palavra_info['palavra']}', "
              f"Início: {palavra_info['inicio']:.2f}s, "
              f"Fim: {palavra_info['fim']:.2f}s")


def salvar_transcricao(palavras_com_timestamps, audio_file_path, output_dir=None):
    """
    Salva a transcrição em um arquivo JSON.

    Args:
        palavras_com_timestamps (list): Lista de palavras com timestamps
        audio_file_path (Path): Caminho do arquivo de áudio original
        output_dir (Path, optional): Diretório de output customizado. Padrão: "output/"

    Returns:
        Path: Caminho do arquivo JSON salvo
    """
    # Define diretório de output
    if output_dir is None:
        output_dir = Path("output")
    else:
        output_dir = Path(output_dir)

    # Cria a pasta se não existir
    output_dir.mkdir(parents=True, exist_ok=True)

    # Define o caminho do arquivo JSON
    output_path = output_dir / audio_file_path.with_suffix('.json').name

    resultado = {
        'arquivo_audio': audio_file_path.name,
        'total_palavras': len(palavras_com_timestamps),
        'palavras': palavras_com_timestamps
    }

    with open(output_path, 'w', encoding='utf-8') as f:
        json.dump(resultado, f, ensure_ascii=False, indent=2)

    print(f"\nTranscrição salva em: {output_path}")
    return output_path


def exibir_resumo(palavras_com_timestamps):
    """
    Exibe um resumo do processo de transcrição.

    Args:
        palavras_com_timestamps (list): Lista de palavras com timestamps
    """
    print(f"\nOK Processo concluido com sucesso!")
    print(f"OK Total de palavras transcritas: {len(palavras_com_timestamps)}")
