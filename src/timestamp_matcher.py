"""
Módulo para sincronização determinística de timestamps.
Faz matching preciso entre conteúdo dos slides e timestamps das palavras.
"""

from difflib import SequenceMatcher
import re


def normalizar_texto(texto):
    """
    Normaliza texto para comparação: lowercase, remove pontuação, espaços extras.

    Args:
        texto (str): Texto a normalizar

    Returns:
        str: Texto normalizado
    """
    texto = texto.lower()
    texto = re.sub(r'[^\w\s]', '', texto)
    texto = re.sub(r'\s+', ' ', texto)
    return texto.strip()


def extrair_palavras_normalizadas(texto):
    """
    Extrai lista de palavras normalizadas de um texto.

    Args:
        texto (str): Texto completo

    Returns:
        list: Lista de palavras normalizadas
    """
    texto_norm = normalizar_texto(texto)
    return texto_norm.split()


def calcular_similaridade(texto1, texto2):
    """
    Calcula similaridade entre dois textos (0.0 a 1.0).

    Args:
        texto1 (str): Primeiro texto
        texto2 (str): Segundo texto

    Returns:
        float: Similaridade (0.0 = diferente, 1.0 = idêntico)
    """
    return SequenceMatcher(None, texto1, texto2).ratio()


def verificar_conceito_no_contexto(indice, titulo_conceito, palavras_com_timestamps, janela_contexto=50):
    """
    Verifica se o titulo_conceito aparece próximo ao índice encontrado.
    Verifica que as palavras do conceito aparecem em sequência (não separadas).

    Args:
        indice (int): Índice da palavra encontrada
        titulo_conceito (str): Conceito esperado (ex: "romance realista", "conto")
        palavras_com_timestamps (list): Array de palavras com timestamps
        janela_contexto (int): Número de palavras antes e depois para verificar

    Returns:
        bool: True se o conceito aparece no contexto, False caso contrário
    """
    if not titulo_conceito:
        return True  # Se não tem conceito específico, aceita qualquer contexto

    # Normaliza o titulo_conceito
    conceito_norm = normalizar_texto(titulo_conceito)
    palavras_conceito = conceito_norm.split()

    # Define janela de busca
    inicio_janela = max(0, indice - janela_contexto)
    fim_janela = min(len(palavras_com_timestamps), indice + janela_contexto)

    # Extrai texto do contexto
    contexto_palavras = [normalizar_texto(palavras_com_timestamps[i]["palavra"])
                         for i in range(inicio_janela, fim_janela)]
    contexto_texto = " ".join(contexto_palavras)

    # Verifica se o conceito completo aparece como sequência no contexto
    conceito_completo = " ".join(palavras_conceito)

    # Busca com tolerância: aceita até 1 palavra extra entre as palavras do conceito
    if conceito_completo in contexto_texto:
        return True

    # Tenta matching com palavras do conceito próximas (máximo 2 palavras de distância)
    for i in range(len(contexto_palavras)):
        match_count = 0
        j = i
        for palavra_conceito in palavras_conceito:
            # Procura a próxima palavra do conceito nas próximas 3 posições
            encontrou = False
            for k in range(j, min(j + 3, len(contexto_palavras))):
                if contexto_palavras[k] == palavra_conceito:
                    match_count += 1
                    j = k + 1
                    encontrou = True
                    break
            if not encontrou:
                break

        if match_count == len(palavras_conceito):
            return True

    return False


def encontrar_todas_ocorrencias(conteudo, palavras_com_timestamps, min_palavras=3, threshold=0.8):
    """
    Encontra TODAS as ocorrências do conteúdo no array de palavras.

    Args:
        conteudo (str): Texto do conteúdo do slide
        palavras_com_timestamps (list): Array de palavras com timestamps
        min_palavras (int): Mínimo de palavras para considerar um match
        threshold (float): Limiar de similaridade

    Returns:
        list: Lista de tuplas (indice, similaridade) ordenadas por similaridade
    """
    palavras_busca = extrair_palavras_normalizadas(conteudo)

    if len(palavras_busca) < min_palavras:
        min_palavras = len(palavras_busca)

    if min_palavras == 0:
        return []

    palavras_audio_norm = [normalizar_texto(p["palavra"]) for p in palavras_com_timestamps]

    ocorrencias = []

    for i in range(len(palavras_audio_norm) - min_palavras + 1):
        janela = palavras_audio_norm[i:i + min_palavras]
        janela_texto = " ".join(janela)
        busca_texto = " ".join(palavras_busca[:min_palavras])
        similaridade = calcular_similaridade(janela_texto, busca_texto)

        if similaridade >= threshold:
            ocorrencias.append((i, similaridade))

    # Ordena por similaridade (maior primeiro)
    ocorrencias.sort(key=lambda x: x[1], reverse=True)

    return ocorrencias


def encontrar_inicio_conteudo_no_array(conteudo, palavras_com_timestamps, min_palavras=3, threshold=0.8, titulo_conceito=None, timestamp_minimo=None):
    """
    Encontra o índice da primeira palavra do conteúdo no array de palavras.
    Usa matching fuzzy, validação de contexto e ordem temporal.

    Args:
        conteudo (str): Texto do conteúdo do slide (pode ser um bullet ou título)
        palavras_com_timestamps (list): Array de palavras com timestamps
        min_palavras (int): Mínimo de palavras para considerar um match
        threshold (float): Limiar de similaridade (0.0 a 1.0)
        titulo_conceito (str): Conceito esperado para validação de contexto
        timestamp_minimo (float): Timestamp mínimo aceitável (ordem cronológica)

    Returns:
        tuple: (indice_encontrado, similaridade) ou (None, 0.0) se não encontrar
    """
    # Encontra todas as ocorrências possíveis
    ocorrencias = encontrar_todas_ocorrencias(conteudo, palavras_com_timestamps, min_palavras, threshold)

    if not ocorrencias:
        return (None, 0.0)

    # FILTRO 1: Ordem temporal - remove ocorrências antes do timestamp_minimo
    if timestamp_minimo is not None:
        ocorrencias_validas = []
        for indice, similaridade in ocorrencias:
            timestamp_ocorrencia = palavras_com_timestamps[indice]["inicio"]
            if timestamp_ocorrencia >= timestamp_minimo:
                ocorrencias_validas.append((indice, similaridade))
        ocorrencias = ocorrencias_validas

        if not ocorrencias:
            return (None, 0.0)

    # FILTRO 2: Validação de contexto (se tem titulo_conceito)
    if titulo_conceito:
        for indice, similaridade in ocorrencias:
            if verificar_conceito_no_contexto(indice, titulo_conceito, palavras_com_timestamps):
                return (indice, similaridade)
        # Se nenhuma ocorrência passou na validação de contexto, retorna None
        return (None, 0.0)

    # Se não tem titulo_conceito, retorna a melhor similaridade (já filtrada por timestamp)
    return ocorrencias[0]


def sincronizar_slide_com_audio(slide, palavras_com_timestamps, timestamp_minimo=None):
    """
    Sincroniza um slide com o áudio, encontrando o timestamp correto.
    Restringe a busca ao contexto do chunk original para evitar matches incorretos.
    Tenta match com: 1) primeiro bullet, 2) título do slide.

    Args:
        slide (dict): Slide com conteúdo gerado
        palavras_com_timestamps (list): Array completo de palavras com timestamps
        timestamp_minimo (float): Timestamp mínimo aceitável (ordem cronológica)

    Returns:
        dict: Slide com timestamp_inicio corrigido e metadados de sincronização
    """
    titulo = slide.get("slide_title", "")
    bullets = slide.get("slide_bullets", [])
    titulo_conceito = slide.get("titulo_conceito", "")
    tipo_slide = slide.get("tipo", "")

    # Verifica se o slide foi corrigido pela validação
    foi_corrigido = slide.get("corrigido_pela_validacao", False)

    if foi_corrigido:
        # Se foi corrigido, os limites do chunk original estão errados
        # Busca no áudio completo
        chunk_inicio = 0
        chunk_fim = len(palavras_com_timestamps) - 1
        palavras_do_chunk = palavras_com_timestamps
    else:
        # Extrai os limites do chunk original
        chunk_inicio = slide.get("chunk_palavra_inicio", 0)
        chunk_fim = slide.get("chunk_palavra_fim", len(palavras_com_timestamps) - 1)
        # Restringe a busca ao sub-array do chunk original
        palavras_do_chunk = palavras_com_timestamps[chunk_inicio : chunk_fim + 1]

    # Para slides tipo EXEMPLO, não valida titulo_conceito no contexto
    # pois o exemplo pode estar distante da definição do conceito
    conceito_para_validacao = None if tipo_slide == "exemplo" else titulo_conceito

    melhor_match = None

    # ESTRATÉGIA 1: Match com primeiro bullet no contexto do chunk
    if bullets:
        primeiro_bullet = bullets[0]
        idx_relativo, sim = encontrar_inicio_conteudo_no_array(
            primeiro_bullet,
            palavras_do_chunk,  # Busca apenas no chunk
            min_palavras=2,  # Reduzido de 3 para 2
            threshold=0.65,  # Reduzido de 0.75 para 0.65
            titulo_conceito=conceito_para_validacao,
            timestamp_minimo=timestamp_minimo
        )
        if idx_relativo is not None:
            # Converte índice relativo para absoluto
            idx_absoluto = chunk_inicio + idx_relativo
            melhor_match = (idx_absoluto, sim, "primeiro_bullet")

    # ESTRATÉGIA 2: Se não encontrou pelo bullet, tenta pelo título
    if melhor_match is None and titulo:
        idx_relativo, sim = encontrar_inicio_conteudo_no_array(
            titulo,
            palavras_do_chunk,  # Busca apenas no chunk
            min_palavras=2,
            threshold=0.7,
            titulo_conceito=conceito_para_validacao,
            timestamp_minimo=timestamp_minimo
        )
        if idx_relativo is not None:
            idx_absoluto = chunk_inicio + idx_relativo
            melhor_match = (idx_absoluto, sim, "titulo")

    # ESTRATÉGIA 3: Tenta com segundo bullet
    if melhor_match is None and len(bullets) > 1:
        segundo_bullet = bullets[1]
        idx_relativo, sim = encontrar_inicio_conteudo_no_array(
            segundo_bullet,
            palavras_do_chunk,  # Busca apenas no chunk
            min_palavras=2,  # Reduzido de 3 para 2
            threshold=0.65,  # Reduzido de 0.75 para 0.65
            titulo_conceito=conceito_para_validacao,
            timestamp_minimo=timestamp_minimo
        )
        if idx_relativo is not None:
            idx_absoluto = chunk_inicio + idx_relativo
            melhor_match = (idx_absoluto, sim, "segundo_bullet")

    # ESTRATÉGIA 4 (NOVA): Fallback - usa timestamp_inicio do chunk original
    if melhor_match is None:
        # Se não encontrou match, usa o timestamp do início do chunk
        timestamp_fallback = palavras_com_timestamps[chunk_inicio]["inicio"]

        slide_com_fallback = slide.copy()
        slide_com_fallback["timestamp_inicio"] = timestamp_fallback
        slide_com_fallback["sync_metadata"] = {
            "indice_palavra": chunk_inicio,
            "palavra_referencia": palavras_com_timestamps[chunk_inicio]["palavra"],
            "similaridade": 0.0,
            "metodo_sync": "fallback_chunk_inicio",
            "timestamp_original": slide.get("timestamp_inicio")
        }

        return slide_com_fallback

    # Se encontrou match, atualiza timestamp
    idx_absoluto, similaridade, metodo = melhor_match
    timestamp_correto = palavras_com_timestamps[idx_absoluto]["inicio"]

    slide_sincronizado = slide.copy()
    slide_sincronizado["timestamp_inicio"] = timestamp_correto
    slide_sincronizado["sync_metadata"] = {
        "indice_palavra": idx_absoluto,
        "palavra_referencia": palavras_com_timestamps[idx_absoluto]["palavra"],
        "similaridade": round(similaridade, 3),
        "metodo_sync": metodo,
        "timestamp_original": slide.get("timestamp_inicio")
    }

    return slide_sincronizado


def sincronizar_todos_slides(slides, palavras_com_timestamps):
    """
    Sincroniza todos os slides com o áudio usando ordem temporal.
    Os slides devem aparecer em ordem cronológica no áudio.

    Args:
        slides (list): Lista de slides gerados
        palavras_com_timestamps (list): Array de palavras com timestamps

    Returns:
        tuple: (slides_sincronizados, estatisticas)
    """
    print("\n[SINCRONIZACAO DETERMINISTICA] Matching preciso de timestamps...")

    slides_sincronizados = []
    stats = {
        "total": len(slides),
        "sincronizados": 0,
        "nao_sincronizados": 0,
        "correcoes": []
    }

    timestamp_anterior = 0.0  # Inicia em 0 para o primeiro slide

    for i, slide in enumerate(slides):
        # Sincroniza com restrição temporal: timestamp >= timestamp_anterior
        slide_sync = sincronizar_slide_com_audio(slide, palavras_com_timestamps, timestamp_minimo=timestamp_anterior)
        slides_sincronizados.append(slide_sync)

        sync_meta = slide_sync.get("sync_metadata", {})

        if sync_meta.get("sincronizado", True):
            stats["sincronizados"] += 1

            ts_original = sync_meta.get("timestamp_original")
            ts_novo = slide_sync["timestamp_inicio"]

            # Atualiza timestamp_anterior para o próximo slide
            timestamp_anterior = ts_novo

            if ts_original is not None and abs(ts_original - ts_novo) > 0.5:
                correcao = {
                    "slide_index": i,
                    "titulo": slide_sync.get("slide_title", ""),
                    "timestamp_original": ts_original,
                    "timestamp_corrigido": ts_novo,
                    "diferenca": round(ts_novo - ts_original, 2),
                    "metodo": sync_meta.get("metodo_sync"),
                    "similaridade": sync_meta.get("similaridade")
                }
                stats["correcoes"].append(correcao)
                print(f"  OK Slide {i}: {ts_original:.2f}s -> {ts_novo:.2f}s (Delta={correcao['diferenca']:+.2f}s) - {sync_meta.get('metodo_sync')}")
            else:
                print(f"  OK Slide {i}: {ts_novo:.2f}s (OK)")
        else:
            stats["nao_sincronizados"] += 1
            print(f"  AVISO Slide {i}: Nao sincronizado - {sync_meta.get('motivo')}")
            # Não atualiza timestamp_anterior se não conseguiu sincronizar

    print(f"\nOK Sincronizacao concluida:")
    print(f"  - {stats['sincronizados']}/{stats['total']} slides sincronizados")
    print(f"  - {len(stats['correcoes'])} timestamps corrigidos")
    if stats["nao_sincronizados"] > 0:
        print(f"  - {stats['nao_sincronizados']} slides nao sincronizados (requerem revisao manual)")

    return slides_sincronizados, stats


def limpar_metadados_sincronizacao(slides):
    """
    Remove metadados de sincronização dos slides (para produção).

    Args:
        slides (list): Lista de slides com metadados

    Returns:
        list: Slides sem metadados de sincronização
    """
    slides_limpos = []
    for slide in slides:
        slide_limpo = slide.copy()
        # Remove metadados de sincronização
        if "sync_metadata" in slide_limpo:
            del slide_limpo["sync_metadata"]
        # Remove limites do chunk (usados apenas internamente)
        if "chunk_palavra_inicio" in slide_limpo:
            del slide_limpo["chunk_palavra_inicio"]
        if "chunk_palavra_fim" in slide_limpo:
            del slide_limpo["chunk_palavra_fim"]
        slides_limpos.append(slide_limpo)
    return slides_limpos
