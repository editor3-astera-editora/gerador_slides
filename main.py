"""
Script principal para transcrição de áudio e geração automática de slides.
Orquestra todos os módulos do sistema com sistema de fila de processamento.
"""

import shutil
from pathlib import Path

from src.config import carregar_configuracao
from src.transcription import criar_cliente, transcrever_audio, processar_transcricao
from src.output import exibir_resultados, salvar_transcricao, exibir_resumo
from src.router import detectar_tipo_conteudo, deve_processar_matematica
from src.math_parser import converter_formulas_para_latex
from src.chunking import segmentar_transcricao, preparar_chunks_com_texto
from src.slide_generator import gerar_slides, salvar_slides, exibir_preview_slides
from src.slide_enricher import enriquecer_todos_slides, limpar_metadados_enriquecimento
from src.validation import validar_conteudo, corrigir_conteudo_slides
from src.timestamp_matcher import sincronizar_todos_slides, limpar_metadados_sincronizacao
from src.pptx_generator import gerar_apresentacao_powerpoint
from src.pptx_to_images import exportar_slides_como_imagens


def obter_pastas_projetos(pasta_audios):
    """
    Escaneia a pasta audios/ e retorna lista de pastas de projetos.
    Ignora a pasta 'Prontos'.
    """
    pastas = []
    for item in sorted(pasta_audios.iterdir()):
        if item.is_dir() and item.name != "Prontos":
            pastas.append(item)
    return pastas


def obter_audios_projeto(pasta_projeto):
    """
    Retorna lista de arquivos de áudio (.mp3, .m4a) dentro de pasta_projeto/audios/
    """
    pasta_audios_projeto = pasta_projeto / "audios"

    if not pasta_audios_projeto.exists():
        print(f"Aviso: {pasta_audios_projeto} não encontrada")
        return []

    # Buscar ambos formatos de áudio
    audios_mp3 = list(pasta_audios_projeto.glob("*.mp3"))
    audios_m4a = list(pasta_audios_projeto.glob("*.m4a"))
    audios = sorted(audios_mp3 + audios_m4a)
    return audios


def processar_audio(client, audio_path, output_dir, template_path):
    """
    Processa um único arquivo de áudio:
    1. Transcrição com timestamps
    2. Segmentação em chunks
    3. Geração de slides JSON
    4. Validação e sincronização
    5. Enriquecimento de conteúdo
    6. Geração de PowerPoint
    7. Exportação para PNG
    """
    try:
        print(f"\n{'=' * 70}")
        print(f"Processando: {audio_path.name}")
        print(f"Output: {output_dir}")
        print(f"{'=' * 70}")

        # Criar diretório de output
        output_dir.mkdir(parents=True, exist_ok=True)

        # ETAPA 1: Transcrição
        print("\n[ETAPA 1] Transcrição do áudio")
        print("-" * 70)
        transcript = transcrever_audio(client, audio_path)
        palavras_com_timestamps = processar_transcricao(transcript)

        if not palavras_com_timestamps:
            print("Aviso: Nenhuma palavra com timestamp encontrada")
            return False

        exibir_resultados(palavras_com_timestamps)
        json_path = salvar_transcricao(palavras_com_timestamps, audio_path, output_dir)
        exibir_resumo(palavras_com_timestamps)

        # ETAPA 1.5: Detecção de tipo de conteúdo e conversão matemática
        print(f"\n{'=' * 70}")
        print("[ETAPA 1.5] Análise de Tipo de Conteúdo")
        print("-" * 70)
        texto_completo = " ".join([p["palavra"] for p in palavras_com_timestamps])
        deteccao = detectar_tipo_conteudo(client, texto_completo)

        # Converte fórmulas para LaTeX se for conteúdo matemático
        if deve_processar_matematica(deteccao):
            print("\n[MATH MODE] Ativando processamento matemático...")
            texto_completo = converter_formulas_para_latex(client, texto_completo)

            # Atualiza palavras_com_timestamps com texto convertido
            # (mantém os timestamps originais, apenas substitui as palavras)
            palavras_convertidas = texto_completo.split()
            if len(palavras_convertidas) == len(palavras_com_timestamps):
                for i, nova_palavra in enumerate(palavras_convertidas):
                    palavras_com_timestamps[i]["palavra"] = nova_palavra
            else:
                print("  ⚠ Aviso: Comprimento do texto convertido difere do original")
                print("  ⚠ Mantendo transcrição original com LaTeX inline")

        # ETAPA 2: Segmentação e Geração de Slides
        print(f"\n{'=' * 70}")
        print("[ETAPA 2] Segmentação e Geração de Slides")
        print("-" * 70)
        chunks = segmentar_transcricao(client, palavras_com_timestamps)
        chunks_com_texto = preparar_chunks_com_texto(palavras_com_timestamps, chunks)
        slides = gerar_slides(client, chunks_com_texto)

        if not slides:
            print("Aviso: Nenhum slide gerado")
            return False

        # ETAPA 3: Validação e Sincronização
        print(f"\n{'=' * 70}")
        print("[ETAPA 3] Validação e Sincronização")
        print("-" * 70)
        texto_transcricao = " ".join([p["palavra"] for p in palavras_com_timestamps])
        resultado_conteudo = validar_conteudo(client, texto_transcricao, slides)

        if not resultado_conteudo.get("conteudo_valido", False):
            erros_conteudo = resultado_conteudo.get("erros_conteudo", [])
            slides = corrigir_conteudo_slides(client, texto_transcricao, slides, erros_conteudo)
        else:
            print("Nenhuma correção de conteúdo necessária")

        slides_sincronizados, stats_sync = sincronizar_todos_slides(slides, palavras_com_timestamps)

        # ETAPA 4: Enriquecimento
        print(f"\n{'=' * 70}")
        print("[ETAPA 4] Enriquecimento de Conteúdo")
        print("-" * 70)
        slides_enriquecidos = enriquecer_todos_slides(client, slides_sincronizados)
        slides_limpos = limpar_metadados_sincronizacao(slides_enriquecidos)
        slides_finais = limpar_metadados_enriquecimento(slides_limpos)
        slides_json_path = salvar_slides(slides_finais, json_path, output_dir)
        exibir_preview_slides(slides_finais)

        # ETAPA 5: Geração de PowerPoint
        print(f"\n{'=' * 70}")
        print("[ETAPA 5] Geração de PowerPoint")
        print("-" * 70)
        pptx_path = gerar_apresentacao_powerpoint(
            slides_json_path,
            template_path if template_path.exists() else None,
            output_dir
        )

        # ETAPA 6: Exportação para PNG
        print(f"\n{'=' * 70}")
        print("[ETAPA 6] Exportação de Slides para PNG")
        print("-" * 70)
        exportar_slides_como_imagens(pptx_path, output_dir / "slides_images")

        # Resumo
        print(f"\n{'=' * 70}")
        print("✓ ÁUDIO PROCESSADO COM SUCESSO")
        print(f"{'=' * 70}")
        print(f"✓ Palavras transcritas: {len(palavras_com_timestamps)}")
        print(f"✓ Chunks: {len(chunks)}")
        print(f"✓ Slides: {len(slides)}")
        print(f"✓ Sincronização: {stats_sync['sincronizados']}/{stats_sync['total']}")
        if pptx_path:
            print(f"✓ PowerPoint: {pptx_path.name}")
        print(f"{'=' * 70}")

        return True

    except Exception as e:
        print(f"\n✗ ERRO ao processar {audio_path.name}: {e}")
        import traceback
        traceback.print_exc()
        return False


def main():
    """
    Função principal com sistema de fila:
    1. Escaneia pastas de projetos em audios/
    2. Para cada projeto, processa todos os áudios
    3. Move projeto para audios/Prontos/ após conclusão
    """
    try:
        print("=" * 70)
        print("SISTEMA DE TRANSCRIÇÃO E GERAÇÃO DE SLIDES - FILA")
        print("=" * 70)

        # Configuração inicial
        api_key = carregar_configuracao()
        client = criar_cliente(api_key)
        template_path = Path("template.pptx")

        # Diretórios base
        pasta_audios_base = Path("audios")
        pasta_output_base = Path("output")
        pasta_prontos = pasta_audios_base / "Prontos"

        # Criar pasta Prontos se não existir
        pasta_prontos.mkdir(exist_ok=True)

        # Obter lista de projetos
        projetos = obter_pastas_projetos(pasta_audios_base)

        if not projetos:
            print("\nNenhuma pasta de projeto encontrada em audios/")
            return

        print(f"\n{len(projetos)} projeto(s) encontrado(s):")
        for p in projetos:
            print(f"  - {p.name}")

        # Processar cada projeto
        total_projetos = len(projetos)
        total_audios_processados = 0
        total_audios_erro = 0

        for idx_projeto, pasta_projeto in enumerate(projetos, 1):
            print(f"\n{'#' * 70}")
            print(f"PROJETO [{idx_projeto}/{total_projetos}]: {pasta_projeto.name}")
            print(f"{'#' * 70}")

            # Obter áudios do projeto
            audios = obter_audios_projeto(pasta_projeto)

            if not audios:
                print(f"Nenhum áudio encontrado em {pasta_projeto.name}/audios/")
                continue

            print(f"\n{len(audios)} áudio(s) encontrado(s):")
            for a in audios:
                print(f"  - {a.name}")

            # Processar cada áudio do projeto
            sucessos_projeto = 0
            erros_projeto = 0

            for idx_audio, audio_path in enumerate(audios, 1):
                print(f"\n{'-' * 70}")
                print(f"ÁUDIO [{idx_audio}/{len(audios)}]: {audio_path.name}")
                print(f"{'-' * 70}")

                # Determinar nome do output (ex: audio_01, audio_02)
                audio_nome = audio_path.stem  # audio_01.mp3 -> audio_01
                output_dir = pasta_output_base / pasta_projeto.name / audio_nome

                # Processar áudio
                sucesso = processar_audio(client, audio_path, output_dir, template_path)

                if sucesso:
                    sucessos_projeto += 1
                    total_audios_processados += 1
                else:
                    erros_projeto += 1
                    total_audios_erro += 1

            # Resumo do projeto
            print(f"\n{'#' * 70}")
            print(f"RESUMO DO PROJETO: {pasta_projeto.name}")
            print(f"{'#' * 70}")
            print(f"✓ Sucessos: {sucessos_projeto}/{len(audios)}")
            print(f"✗ Erros: {erros_projeto}/{len(audios)}")

            # Mover pasta para Prontos se todos os áudios foram processados com sucesso
            if erros_projeto == 0 and len(audios) > 0:
                destino = pasta_prontos / pasta_projeto.name
                print(f"\nMovendo {pasta_projeto.name} para Prontos/")
                shutil.move(str(pasta_projeto), str(destino))
                print(f"✓ Movido para: {destino}")
            else:
                print(f"\n⚠ Projeto NÃO movido para Prontos (houve erros ou sem áudios)")

        # RESUMO FINAL GERAL
        print(f"\n{'=' * 70}")
        print("PROCESSAMENTO COMPLETO - RESUMO GERAL")
        print(f"{'=' * 70}")
        print(f"Total de projetos processados: {total_projetos}")
        print(f"Total de áudios com sucesso: {total_audios_processados}")
        print(f"Total de áudios com erro: {total_audios_erro}")
        print(f"{'=' * 70}")

    except FileNotFoundError as e:
        print(f"\nErro: {e}")
    except ValueError as e:
        print(f"\nErro de configuração: {e}")
    except Exception as e:
        print(f"\nErro inesperado: {e}")
        import traceback
        traceback.print_exc()


if __name__ == "__main__":
    main()
