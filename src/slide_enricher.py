"""
Módulo para enriquecimento e refinamento de conteúdo dos slides.
Melhora a clareza, redação e estrutura dos bullets usando o texto original.
"""

import json
from openai import OpenAI
from src.prompts import SLIDE_ENRICH_AND_REFINE_PROMPT


def enriquecer_conteudo_slide(client, slide):
    """
    Enriquece e refina o conteúdo de um único slide.
    Melhora a redação, clareza e estrutura usando o texto original do chunk.

    Args:
        client (OpenAI): Cliente OpenAI configurado
        slide (dict): Slide com texto_original_chunk, slide_title e slide_bullets

    Returns:
        dict: Slide com conteúdo refinado e enriquecido
    """
    texto_original = slide.get("texto_original_chunk", "")
    bullets_iniciais = slide.get("slide_bullets", [])
    titulo_inicial = slide.get("slide_title", "")

    # Se não houver conteúdo para enriquecer, retorna o slide original
    if not texto_original or not bullets_iniciais:
        return slide

    # Prepara dados para o prompt de enriquecimento
    dados_para_refinar = {
        "texto_original_chunk": texto_original,
        "slide_title_inicial": titulo_inicial,
        "slide_bullets_iniciais": bullets_iniciais
    }

    # Envia para GPT-4o
    response = client.chat.completions.create(
        model="gpt-4o",
        messages=[
            {"role": "system", "content": SLIDE_ENRICH_AND_REFINE_PROMPT},
            {"role": "user", "content": json.dumps(dados_para_refinar, ensure_ascii=False)}
        ],
        temperature=0.3,
        response_format={"type": "json_object"}
    )

    # Parse da resposta
    resultado = json.loads(response.choices[0].message.content)

    # Cria slide refinado com conteúdo enriquecido
    slide_refinado = slide.copy()
    slide_refinado["slide_title"] = resultado.get("slide_title", titulo_inicial)
    slide_refinado["slide_bullets"] = resultado.get("slide_bullets", bullets_iniciais)
    slide_refinado["frase_introdutoria"] = resultado.get("frase_introdutoria", "")

    return slide_refinado


def enriquecer_todos_slides(client, slides):
    """
    Enriquece o conteúdo de todos os slides.

    Args:
        client (OpenAI): Cliente OpenAI configurado
        slides (list): Lista de slides gerados

    Returns:
        list: Lista de slides com conteúdo enriquecido
    """
    print("\n[ENRIQUECIMENTO DE CONTEÚDO] Refinando slides...")

    slides_enriquecidos = []
    total_slides = len(slides)

    for i, slide in enumerate(slides, 1):
        tipo = slide.get("tipo", "")
        titulo = slide.get("slide_title", "")[:50]

        print(f"  Refinando slide {i}/{total_slides}: {tipo} - {titulo}...", end="")

        slide_enriquecido = enriquecer_conteudo_slide(client, slide)
        slides_enriquecidos.append(slide_enriquecido)

        # Verifica se houve mudanças significativas
        teve_mudanca = (
            slide_enriquecido["slide_title"] != slide["slide_title"] or
            slide_enriquecido.get("frase_introdutoria", "") != ""
        )

        if teve_mudanca:
            print(" OK (refinado)")
        else:
            print(" OK")

    print(f"\nOK {len(slides_enriquecidos)} slides refinados")

    return slides_enriquecidos


def limpar_metadados_enriquecimento(slides):
    """
    Remove o texto_original_chunk dos slides (usado apenas para enriquecimento).
    Mantém a frase_introdutoria para uso no PowerPoint.

    Args:
        slides (list): Lista de slides enriquecidos

    Returns:
        list: Slides sem metadados de enriquecimento
    """
    slides_limpos = []
    for slide in slides:
        slide_limpo = slide.copy()
        # Remove texto original (não necessário no output final)
        if "texto_original_chunk" in slide_limpo:
            del slide_limpo["texto_original_chunk"]
        slides_limpos.append(slide_limpo)
    return slides_limpos
