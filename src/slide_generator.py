"""
Módulo para geração de slides a partir de chunks de transcrição.
"""

import json
from pathlib import Path
from openai import OpenAI
from src.prompts import SLIDE_INTRO_PROMPT, SLIDE_CONCEITO_PROMPT, SLIDE_EXEMPLO_PROMPT


def gerar_slide_para_chunk(client, chunk):
    """
    Gera um slide (título + bullets) para um chunk de texto.
    Usa prompts específicos baseados no tipo do chunk.

    Args:
        client (OpenAI): Cliente OpenAI configurado
        chunk (dict): Chunk com texto e metadados

    Returns:
        dict: Slide gerado com título e bullets, ou None se despedida
    """
    tipo = chunk["tipo"]
    texto = chunk["texto"]

    # Despedida não gera slide
    if tipo == "despedida":
        return None

    # Seleciona o prompt apropriado baseado no tipo
    prompt_map = {
        "introducao": SLIDE_INTRO_PROMPT,
        "conceito": SLIDE_CONCEITO_PROMPT,
        "exemplo": SLIDE_EXEMPLO_PROMPT
    }

    prompt = prompt_map.get(tipo)
    if not prompt:
        print(f"\n  Aviso: Tipo desconhecido '{tipo}', ignorando...")
        return None

    # Envia para GPT
    response = client.chat.completions.create(
        model="gpt-4o",
        messages=[
            {"role": "system", "content": prompt},
            {"role": "user", "content": f"Segmento de transcrição:\n\n{texto}"}
        ],
        temperature=0.4,
        response_format={"type": "json_object"}
    )

    # Parse da resposta
    slide_content = json.loads(response.choices[0].message.content)

    # Monta o slide completo com metadados + limites do chunk original
    slide = {
        "timestamp_inicio": chunk["timestamp_inicio"],
        "tipo": tipo,
        "titulo_conceito": chunk.get("titulo_conceito"),
        "slide_title": slide_content["slide_title"],  # Mantido para referência (não é exibido no Layout 1)
        "slide_bullets": slide_content["slide_bullets"],
        "texto_original_chunk": texto,  # Adicionado: texto original para enriquecimento
        "chunk_palavra_inicio": chunk["palavra_inicio"],
        "chunk_palavra_fim": chunk["palavra_fim"]
    }

    return slide


def gerar_slides(client, chunks_com_texto):
    """
    Gera slides para todos os chunks.

    Args:
        client (OpenAI): Cliente OpenAI configurado
        chunks_com_texto (list): Lista de chunks com texto

    Returns:
        list: Lista de slides gerados
    """
    print("\nGerando slides a partir dos chunks...")

    slides = []
    total_chunks = len(chunks_com_texto)

    for i, chunk in enumerate(chunks_com_texto, 1):
        tipo = chunk['tipo']
        titulo = chunk.get('titulo_conceito', 'N/A')

        if tipo == "despedida":
            print(f"  Processando chunk {i}/{total_chunks}: {tipo} (ignorado)")
            continue

        print(f"  Processando chunk {i}/{total_chunks}: {tipo} - {titulo}", end="")

        slide = gerar_slide_para_chunk(client, chunk)

        if slide:
            slides.append(slide)
            print(f" OK")
        else:
            print(f" (erro)")

    print(f"\nOK {len(slides)} slides gerados")

    return slides


def salvar_slides(slides, json_transcricao_path, output_dir=None):
    """
    Salva os slides em um arquivo JSON.

    Args:
        slides (list): Lista de slides gerados
        json_transcricao_path (Path): Caminho do JSON de transcrição original
        output_dir (Path, optional): Diretório de output customizado. Padrão: "output/"

    Returns:
        Path: Caminho do arquivo de slides salvo
    """
    # Define diretório de output
    if output_dir is None:
        output_dir = Path("output")
    else:
        output_dir = Path(output_dir)

    # Cria pasta se não existir
    output_dir.mkdir(parents=True, exist_ok=True)

    # Define o nome do arquivo de slides
    nome_base = json_transcricao_path.stem  # Remove .json
    slides_filename = f"{nome_base}_slides.json"
    slides_path = output_dir / slides_filename

    # Estrutura do JSON de saída
    resultado = {
        "arquivo_original": json_transcricao_path.name,
        "total_slides": len(slides),
        "slides": slides
    }

    # Salva o arquivo
    with open(slides_path, 'w', encoding='utf-8') as f:
        json.dump(resultado, f, ensure_ascii=False, indent=2)

    print(f"\nOK Slides salvos em: {slides_path}")

    return slides_path


def exibir_preview_slides(slides):
    """
    Exibe um preview dos slides gerados no console.

    Args:
        slides (list): Lista de slides gerados
    """
    print("\n" + "=" * 70)
    print("PREVIEW DOS SLIDES GERADOS")
    print("=" * 70)

    for i, slide in enumerate(slides, 1):
        tipo_label = {
            "introducao": "INTRODUÇÃO",
            "conceito": "CONCEITO",
            "exemplo": "EXEMPLO"
        }.get(slide['tipo'], slide['tipo'].upper())

        print(f"\n[Slide {i}] - {tipo_label} - Timestamp: {slide['timestamp_inicio']:.2f}s")
        print(f"Título: {slide['slide_title']}")
        print("Bullets:")
        for bullet in slide['slide_bullets']:
            print(f"  • {bullet}")

    print("\n" + "=" * 70)
