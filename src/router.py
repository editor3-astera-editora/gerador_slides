"""
Módulo para detectar tipo de conteúdo (matemática ou não) e rotear processamento.
"""

import json
from openai import OpenAI


CONTENT_TYPE_DETECTION_PROMPT = """Você é um especialista em análise de conteúdo educacional.

**Sua Tarefa:**
Analisar uma transcrição de áudio educacional e determinar se o conteúdo é MATEMÁTICO ou NÃO-MATEMÁTICO.

**Conteúdo MATEMÁTICO inclui:**
- Explicações de fórmulas, equações ou expressões matemáticas
- Conceitos de álgebra, geometria, cálculo, estatística, etc.
- Resolução de problemas numéricos
- Demonstrações matemáticas
- Qualquer menção a variáveis, operações matemáticas, funções

**Conteúdo NÃO-MATEMÁTICO inclui:**
- Literatura, gramática, redação
- História, geografia, ciências sociais
- Biologia, química descritiva (sem fórmulas complexas)
- Artes, filosofia

**Indicadores-chave de conteúdo matemático:**
- Palavras como: "função", "equação", "fórmula", "variável", "calcular", "resolver"
- Menções a letras como variáveis: "x", "y", "a", "b"
- Descrições de operações: "vezes", "dividido", "ao quadrado", "raiz de"
- Símbolos matemáticos falados: "delta", "sigma", "pi"

**Formato de Saída (JSON):**
{
  "tipo_conteudo": "matematica" ou "geral",
  "confianca": 0.0 a 1.0,
  "justificativa": "Breve explicação da decisão"
}

**IMPORTANTE:**
- Se houver QUALQUER dúvida, prefira classificar como "geral"
- Confiança acima de 0.7 indica alta certeza de conteúdo matemático
- Retorne APENAS o objeto JSON, sem texto adicional
"""


def detectar_tipo_conteudo(client: OpenAI, texto_transcricao: str) -> dict:
    """
    Detecta se o conteúdo é matemático ou geral usando GPT-4o.

    Args:
        client (OpenAI): Cliente OpenAI configurado
        texto_transcricao (str): Texto da transcrição completa

    Returns:
        dict: {
            "tipo_conteudo": "matematica" | "geral",
            "confianca": float,
            "justificativa": str
        }
    """
    print("\n[ROUTER] Detectando tipo de conteúdo...")

    try:
        # Usa apenas os primeiros 2000 caracteres para análise (suficiente)
        amostra = texto_transcricao[:2000]

        response = client.chat.completions.create(
            model="gpt-4o",
            messages=[
                {"role": "system", "content": CONTENT_TYPE_DETECTION_PROMPT},
                {"role": "user", "content": amostra}
            ],
            temperature=0.1,
            response_format={"type": "json_object"}
        )

        resultado = json.loads(response.choices[0].message.content)

        tipo = resultado.get("tipo_conteudo", "geral")
        confianca = resultado.get("confianca", 0.0)
        justificativa = resultado.get("justificativa", "")

        print(f"✓ Tipo detectado: {tipo.upper()}")
        print(f"  Confiança: {confianca:.2f}")
        print(f"  Justificativa: {justificativa}")

        return {
            "tipo_conteudo": tipo,
            "confianca": confianca,
            "justificativa": justificativa
        }

    except Exception as e:
        print(f"⚠ ERRO ao detectar tipo de conteúdo: {e}")
        print("⚠ Usando modo GERAL por padrão...")
        return {
            "tipo_conteudo": "geral",
            "confianca": 0.0,
            "justificativa": "Erro na detecção, usando modo padrão"
        }


def deve_processar_matematica(deteccao: dict) -> bool:
    """
    Decide se deve ativar o processamento matemático baseado na detecção.

    Args:
        deteccao (dict): Resultado de detectar_tipo_conteudo()

    Returns:
        bool: True se deve processar como conteúdo matemático
    """
    tipo = deteccao.get("tipo_conteudo", "geral")
    confianca = deteccao.get("confianca", 0.0)

    # Ativa processamento matemático se:
    # 1. Tipo detectado é "matematica" E
    # 2. Confiança >= 0.7
    return tipo == "matematica" and confianca >= 0.7
