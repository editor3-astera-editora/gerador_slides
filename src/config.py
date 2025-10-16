"""
Módulo de configuração do projeto.
Carrega e valida as configurações necessárias.
"""

import os
from dotenv import load_dotenv


def carregar_configuracao():
    """
    Carrega as configurações do arquivo .env.

    Returns:
        str: API key da OpenAI

    Raises:
        ValueError: Se OPENAI_API_KEY não for encontrada
    """
    load_dotenv()
    api_key = os.getenv("OPENAI_API_KEY")

    if not api_key:
        raise ValueError("OPENAI_API_KEY não encontrada no arquivo .env")

    return api_key
