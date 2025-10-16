"""
Módulo para validação de conteúdo dos slides.
"""

import json
from openai import OpenAI


CONTENT_VALIDATION_PROMPT = """Você é um validador especialista de conteúdo educacional.

**Sua Tarefa:**
Validar se os slides gerados estão FIÉIS ao texto original da transcrição.

**Você receberá:**
1. Texto completo da transcrição original
2. Lista de slides gerados

**Validações a fazer:**

1. **Fidelidade ao conteúdo:**
   - Cada slide tem conteúdo que EXISTE no texto original?
   - Os bullets são extraídos LITERALMENTE do texto?
   - Há invenções ou generalizações?

2. **Correspondência título-conceito:**
   - O slide_title corresponde ao titulo_conceito?
   - Exemplo: Se titulo_conceito="poema", slide_title deve ser "Poema" ou "O Poema"

3. **Conteúdo correto por conceito:**
   - Slide de "Romance Realista" tem conteúdo sobre Romance Realista?
   - Slide de "Poema" tem conteúdo sobre Poema (não sobre outros conceitos)?

4. **Slides vazios:**
   - Há slides com slide_bullets vazios []?

5. **Completude:**
   - Faltam informações importantes do texto no slide?

**Retorne APENAS um JSON válido:**

{
  "conteudo_valido": true/false,
  "erros_conteudo": [
    {
      "slide_index": 2,
      "tipo_erro": "conteudo_errado|titulo_errado|vazio|incompleto|inventado",
      "descricao": "Descrição clara do erro",
      "titulo_conceito": "nome do conceito deste slide",
      "conteudo_esperado": "O que deveria estar no slide baseado no texto original"
    }
  ],
  "slides_corretos": [0, 1],
  "slides_com_erro_conteudo": [2, 3, 4]
}

**Regras:**
- Se conteudo_valido=true, erros_conteudo deve ser []
- Se conteudo_valido=false, liste TODOS os erros encontrados
- Para cada erro, forneça conteudo_esperado extraído DO TEXTO ORIGINAL
- Seja específico e detalhado nos erros
"""


CONTENT_CORRECTION_PROMPT = """Você é um corretor especialista de slides educacionais.

**Sua Tarefa:**
Corrigir os slides com erros de conteúdo usando APENAS o texto original da transcrição.

**Você receberá:**
1. Texto completo da transcrição original
2. Lista de slides originais (alguns com erros)
3. Lista de erros encontrados na validação

**Como corrigir:**

1. Para cada erro listado:
   - Identifique o slide_index do erro
   - Localize o conteúdo correto no texto original baseado no titulo_conceito
   - Extraia informações LITERALMENTE do texto original
   - Corrija APENAS o que está errado (título, bullets, ou ambos)

2. Regras de correção:
   - NÃO invente conteúdo
   - NÃO use conhecimento externo
   - USE apenas o que está no texto original
   - Mantenha timestamp_inicio e tipo originais do slide
   - Corrija slide_title para corresponder ao titulo_conceito
   - Extraia slide_bullets fielmente do texto

3. Tipos de erro e como corrigir:
   - **vazio**: Preencha slide_bullets com conteúdo do texto original sobre o conceito
   - **titulo_errado**: Corrija slide_title para refletir o titulo_conceito
   - **conteudo_errado**: Substitua slide_bullets pelo conteúdo correto do conceito
   - **incompleto**: Adicione mais informações do texto original aos slide_bullets
   - **inventado**: Remova conteúdo inventado e use apenas o texto original

**Retorne APENAS um JSON válido:**

{
  "slides_corrigidos": [
    {
      "slide_index": 2,
      "timestamp_inicio": 82.58,
      "tipo": "conceito",
      "titulo_conceito": "romance pré modernista",
      "slide_title": "Romance Pré-Modernista",
      "slide_bullets": [
        "Bullet 1 extraído LITERALMENTE do texto",
        "Bullet 2 extraído LITERALMENTE do texto"
      ]
    }
  ]
}

**IMPORTANTE:**
- Retorne SOMENTE os slides que precisam de correção (aqueles listados em erros)
- Não retorne slides já corretos
- Mantenha a estrutura completa de cada slide corrigido
- Cada bullet deve ser fiel ao texto original
- Não altere timestamp_inicio, tipo, ou titulo_conceito
"""


def validar_conteudo(client, texto_transcricao, slides):
    """
    Valida se o conteúdo dos slides está fiel ao texto original.

    Args:
        client (OpenAI): Cliente OpenAI configurado
        texto_transcricao (str): Texto completo da transcrição
        slides (list): Lista de slides gerados

    Returns:
        dict: Resultado da validação de conteúdo
    """
    print("\n[VALIDAÇÃO DE CONTEÚDO] Verificando fidelidade ao texto original...")

    dados_validacao = {
        "texto_original": texto_transcricao,
        "slides": slides
    }

    response = client.chat.completions.create(
        model="gpt-4o",
        messages=[
            {"role": "system", "content": CONTENT_VALIDATION_PROMPT},
            {"role": "user", "content": json.dumps(dados_validacao, ensure_ascii=False)}
        ],
        temperature=0.1,
        response_format={"type": "json_object"}
    )

    resultado = json.loads(response.choices[0].message.content)

    if resultado.get("conteudo_valido", False):
        print("OK Conteudo de todos os slides esta correto!")
    else:
        erros = resultado.get("erros_conteudo", [])
        print(f"AVISO Encontrados {len(erros)} erros de conteudo:")
        for erro in erros:
            print(f"  - Slide {erro['slide_index']}: {erro['tipo_erro']} - {erro['descricao']}")

    return resultado


def corrigir_conteudo_slides(client, texto_transcricao, slides, erros_conteudo):
    """
    Corrige slides com erros de conteúdo usando o texto original.

    Args:
        client (OpenAI): Cliente OpenAI configurado
        texto_transcricao (str): Texto completo da transcrição
        slides (list): Lista de slides originais
        erros_conteudo (list): Lista de erros encontrados na validação

    Returns:
        list: Slides com correções aplicadas
    """
    if not erros_conteudo:
        print("\nNenhuma correcao de conteudo necessaria.")
        return slides

    print(f"\n[CORRECAO DE CONTEUDO] Corrigindo {len(erros_conteudo)} slides com erros...")

    dados_correcao = {
        "texto_original": texto_transcricao,
        "slides_originais": slides,
        "erros": erros_conteudo
    }

    response = client.chat.completions.create(
        model="gpt-4o",
        messages=[
            {"role": "system", "content": CONTENT_CORRECTION_PROMPT},
            {"role": "user", "content": json.dumps(dados_correcao, ensure_ascii=False)}
        ],
        temperature=0.2,
        response_format={"type": "json_object"}
    )

    resultado = json.loads(response.choices[0].message.content)
    slides_corrigidos_dict = resultado.get("slides_corrigidos", [])

    # Aplica correções aos slides originais
    slides_finais = [slide.copy() for slide in slides]

    for correcao in slides_corrigidos_dict:
        idx = correcao.get("slide_index")
        if idx is not None and 0 <= idx < len(slides_finais):
            # CORRIGIDO: Atualiza apenas os campos de conteúdo, preservando timestamps e metadados
            slides_finais[idx]["slide_title"] = correcao.get("slide_title", slides_finais[idx]["slide_title"])
            slides_finais[idx]["slide_bullets"] = correcao.get("slide_bullets", slides_finais[idx]["slide_bullets"])
            # Marca que este slide foi corrigido - sync deve buscar no áudio completo, não no chunk
            slides_finais[idx]["corrigido_pela_validacao"] = True
            # Preserva: timestamp_inicio, tipo, titulo_conceito, chunk_palavra_inicio, chunk_palavra_fim
            print(f"  OK Slide {idx} corrigido: {correcao.get('slide_title', 'sem titulo')}")

    print(f"\nOK {len(slides_corrigidos_dict)} slides corrigidos com sucesso")

    return slides_finais
