"""
Módulo para detecção e conversão de fórmulas matemáticas para LaTeX.
"""

import json
from openai import OpenAI
from src.prompts import MATH_CONVERSION_PROMPT


def converter_formulas_para_latex(client: OpenAI, texto_transcricao: str) -> str:
    """
    Usa GPT-4o para encontrar expressões matemáticas no texto e convertê-las para LaTeX.

    Args:
        client (OpenAI): Cliente OpenAI configurado
        texto_transcricao (str): Texto da transcrição completa

    Returns:
        str: Texto com fórmulas convertidas para LaTeX
    """
    print("\n[MATH PARSER] Detectando e convertendo fórmulas para LaTeX...")

    try:
        response = client.chat.completions.create(
            model="gpt-4o",
            messages=[
                {"role": "system", "content": MATH_CONVERSION_PROMPT},
                {"role": "user", "content": texto_transcricao}
            ],
            temperature=0.0,
            response_format={"type": "json_object"}
        )

        resultado = json.loads(response.choices[0].message.content)
        texto_convertido = resultado.get("texto_com_latex", texto_transcricao)

        # Conta quantas fórmulas foram encontradas
        num_formulas = texto_convertido.count('$')
        if num_formulas > 0:
            print(f"✓ {num_formulas // 2} fórmula(s) matemática(s) convertida(s) para LaTeX")
        else:
            print("✓ Nenhuma fórmula matemática detectada")

        return texto_convertido

    except Exception as e:
        print(f"⚠ ERRO ao converter fórmulas: {e}")
        print("⚠ Continuando com texto original...")
        return texto_transcricao
