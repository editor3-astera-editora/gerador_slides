"""
Script principal para montagem de vídeo com slides sincronizados.
Processa projetos em fila: output/ → resultados/
Orquestra todo o pipeline: conversão de slides → script → renderização.
"""

import shutil
from pathlib import Path
from src.pptx_to_images import exportar_slides_como_imagens, verificar_imagens_exportadas
from src.show_script_generator import gerar_show_script, validar_show_script, exibir_preview_show_script
from src.video_renderer import renderizar_video, estimar_tempo_renderizacao, verificar_dependencias_moviepy


def obter_projetos_output(pasta_output):
    """
    Escaneia a pasta output/ e retorna lista de pastas de projetos.
    """
    projetos = []
    for item in sorted(pasta_output.iterdir()):
        if item.is_dir():
            projetos.append(item)
    return projetos


def obter_subpastas_audio(pasta_projeto):
    """
    Retorna lista de subpastas de áudio dentro de um projeto.
    Ex: output/projeto_A/ contém audio_01/, audio_02/, etc.
    """
    subpastas = []
    for item in sorted(pasta_projeto.iterdir()):
        if item.is_dir():
            subpastas.append(item)
    return subpastas


def localizar_audio_original(nome_projeto, nome_audio):
    """
    Localiza o áudio original em audios/Prontos/nome_projeto/audios/

    Args:
        nome_projeto (str): Nome da pasta do projeto
        nome_audio (str): Nome do áudio (ex: audio_01)

    Returns:
        Path ou None: Caminho do arquivo de áudio ou None se não encontrado
    """
    pasta_prontos = Path("audios") / "Prontos" / nome_projeto / "audios"

    if not pasta_prontos.exists():
        print(f"  Aviso: Pasta {pasta_prontos} não encontrada")
        return None

    # Procurar arquivo de áudio em formatos suportados
    extensoes = ['.mp3', '.m4a', '.wav', '.mp4', '.mpeg', '.mpga', '.webm']

    for ext in extensoes:
        audio_path = pasta_prontos / f"{nome_audio}{ext}"
        if audio_path.exists():
            return audio_path

    print(f"  Aviso: Áudio {nome_audio} não encontrado em {pasta_prontos}")
    return None


def processar_audio_para_video(
    pasta_audio,
    nome_projeto,
    resolucao=(1920, 1080),
    fps=24
):
    """
    Processa um único áudio: regenera imagens, monta vídeo.

    Args:
        pasta_audio (Path): Caminho para pasta do áudio (ex: output/projeto_A/audio_01/)
        nome_projeto (str): Nome do projeto
        resolucao (tuple): Resolução do vídeo
        fps (int): Frames por segundo

    Returns:
        bool: True se sucesso, False se erro
    """
    try:
        nome_audio = pasta_audio.name  # audio_01, audio_02, etc.

        print(f"\n{'=' * 70}")
        print(f"Processando: {nome_projeto}/{nome_audio}")
        print(f"{'=' * 70}")

        # 1. Localizar arquivos necessários
        pptx_files = list(pasta_audio.glob("*.pptx"))
        slides_json_files = list(pasta_audio.glob("*_slides.json"))

        if not pptx_files:
            print(f"  ERRO: Nenhum .pptx encontrado em {pasta_audio}")
            return False

        if not slides_json_files:
            print(f"  ERRO: Nenhum *_slides.json encontrado em {pasta_audio}")
            return False

        pptx_path = pptx_files[0]
        slides_json_path = slides_json_files[0]

        print(f"  PowerPoint: {pptx_path.name}")
        print(f"  Slides JSON: {slides_json_path.name}")

        # 2. Localizar áudio (primeiro localmente, depois em audios/Prontos)
        # Procurar arquivos de áudio na pasta atual (múltiplos formatos)
        extensoes = ['*.mp3', '*.m4a', '*.wav', '*.mp4', '*.mpeg', '*.mpga', '*.webm']
        audio_files = []
        for ext in extensoes:
            audio_files.extend(list(pasta_audio.glob(ext)))

        if audio_files:
            # Áudio já existe localmente
            audio_destino = audio_files[0]
            print(f"  Áudio encontrado: {audio_destino.name}")
        else:
            # Buscar em audios/Prontos
            audio_original = localizar_audio_original(nome_projeto, nome_audio)

            if not audio_original:
                print(f"  ERRO: Áudio original não encontrado")
                print(f"    Procurou em: audios/Prontos/{nome_projeto}/audios/{nome_audio}.mp3")
                return False

            # Copiar áudio para pasta de output
            audio_destino = pasta_audio / audio_original.name
            print(f"  Copiando áudio: {audio_original.name}")
            shutil.copy2(audio_original, audio_destino)

        # 3. Regenerar slides_images/
        print("\n[ETAPA 1] Regenerando slides como imagens...")
        images_folder = pasta_audio / "slides_images"
        images_folder.mkdir(exist_ok=True)

        try:
            image_paths = exportar_slides_como_imagens(pptx_path, images_folder)
            print(f"  OK {len(image_paths)} slides exportados")
        except Exception as e:
            print(f"  ERRO ao exportar slides: {e}")
            return False

        # 4. Gerar show_script.json
        print("\n[ETAPA 2] Gerando script de apresentação...")
        show_script_path = pasta_audio / "show_script.json"

        try:
            show_script = gerar_show_script(slides_json_path, show_script_path)
            valido, erros = validar_show_script(show_script)

            if not valido:
                print(f"  ERRO: Script inválido:")
                for erro in erros:
                    print(f"    - {erro}")
                return False

            print("  OK Script validado")
        except Exception as e:
            print(f"  ERRO ao gerar script: {e}")
            return False

        # 5. Renderizar vídeo
        print("\n[ETAPA 3] Renderizando vídeo...")

        # Estimar tempo
        import json
        with open(show_script_path, 'r', encoding='utf-8') as f:
            script_data = json.load(f)

        try:
            from moviepy import AudioFileClip
        except ImportError:
            from moviepy.editor import AudioFileClip

        audio_clip = AudioFileClip(str(audio_destino))
        duracao_audio = audio_clip.duration
        audio_clip.close()

        tempo_estimado = estimar_tempo_renderizacao(duracao_audio, len(script_data))
        print(f"  Tempo estimado: {tempo_estimado:.1f} minutos")

        # Determinar nome do vídeo
        base_name = slides_json_path.stem.replace("_slides", "")
        output_video_path = pasta_audio / f"{base_name}.mp4"

        try:
            video_path = renderizar_video(
                show_script_path=show_script_path,
                audio_path=audio_destino,
                images_folder=images_folder,
                output_path=output_video_path,
                legendas_moviepy=None,
                resolucao=resolucao,
                fps=fps
            )

            print(f"\n{'=' * 70}")
            print(f"OK VIDEO GERADO: {video_path.name}")
            print(f"{'=' * 70}")
            return True

        except Exception as e:
            print(f"\n  ERRO na renderização: {e}")
            import traceback
            traceback.print_exc()
            return False

    except Exception as e:
        print(f"\n  ERRO inesperado: {e}")
        import traceback
        traceback.print_exc()
        return False


def montar_video_completo(
    slides_json_path=None,
    pptx_path=None,
    audio_path=None,
    output_video_path=None,
    resolucao=(1920, 1080),
    fps=24
):
    """
    Pipeline completo de montagem de vídeo.

    Args:
        slides_json_path (Path): Caminho para *_slides.json (auto-detecta se None)
        pptx_path (Path): Caminho para apresentação PowerPoint (auto-detecta se None)
        audio_path (Path): Caminho para áudio (auto-detecta se None)
        output_video_path (Path): Caminho para salvar vídeo (auto-gera se None)
        resolucao (tuple): Resolução do vídeo (largura, altura)
        fps (int): Frames por segundo

    Returns:
        Path: Caminho do vídeo renderizado
    """
    print("=" * 70)
    print("PIPELINE DE MONTAGEM DE VÍDEO")
    print("=" * 70)

    # ETAPA 0: Verificar dependências
    print("\n[ETAPA 0] Verificando dependências...")
    instalado, msg = verificar_dependencias_moviepy()
    if not instalado:
        print(f"ERRO: {msg}")
        return None
    print("OK Dependências verificadas")

    # ETAPA 1: Auto-detectar arquivos se não fornecidos
    print("\n[ETAPA 1] Localizando arquivos...")

    if not slides_json_path:
        # Procura *_slides.json na pasta output/
        output_dir = Path("output")
        slides_json_files = list(output_dir.glob("*_slides.json"))
        if not slides_json_files:
            raise FileNotFoundError("Nenhum arquivo *_slides.json encontrado em output/")
        slides_json_path = slides_json_files[0]
        print(f"  Auto-detectado: {slides_json_path.name}")

    if not pptx_path:
        # Procura .pptx com mesmo nome base na pasta output/
        base_name = slides_json_path.stem.replace("_slides", "")
        pptx_path = Path("output") / f"{base_name}.pptx"
        if not pptx_path.exists():
            raise FileNotFoundError(f"PowerPoint não encontrado: {pptx_path}")
        print(f"  Auto-detectado: {pptx_path.name}")

    if not audio_path:
        # Procura áudio na pasta audios/
        pasta_audios = Path("audios")
        audio_path = obter_primeiro_audio(pasta_audios)
        print(f"  Auto-detectado: {audio_path.name}")

    if not output_video_path:
        base_name = slides_json_path.stem.replace("_slides", "")
        output_video_path = Path("output") / f"{base_name}.mp4"
        print(f"  Vídeo será salvo como: {output_video_path.name}")

    # ETAPA 2: Exportar slides como imagens
    print("\n[ETAPA 2] Exportando slides como imagens...")
    images_folder = Path("output") / "slides_images"
    images_folder.mkdir(exist_ok=True)

    try:
        image_paths = exportar_slides_como_imagens(pptx_path, images_folder)
        print(f"OK {len(image_paths)} slides exportados como imagens")
    except Exception as e:
        print(f"ERRO ao exportar slides: {e}")
        return None

    # ETAPA 3: Gerar script de apresentação
    print("\n[ETAPA 3] Gerando script de apresentação...")
    show_script_path = Path("output") / "show_script.json"

    try:
        show_script = gerar_show_script(slides_json_path, show_script_path)

        # Validar script
        valido, erros = validar_show_script(show_script)
        if not valido:
            print(f"ERRO: Script inválido:")
            for erro in erros:
                print(f"  - {erro}")
            return None

        print("OK Script de apresentação validado")

    except Exception as e:
        print(f"ERRO ao gerar script: {e}")
        return None

    # ETAPA 4: Renderizar vídeo (legendas removidas)
    print("\n[ETAPA 4] Renderizando vídeo final...")

    # Estimar tempo
    import json
    with open(show_script_path, 'r') as f:
        script_data = json.load(f)

    try:
        from moviepy import AudioFileClip
    except ImportError:
        from moviepy.editor import AudioFileClip
    audio_clip = AudioFileClip(str(audio_path))
    duracao_audio = audio_clip.duration
    audio_clip.close()

    tempo_estimado = estimar_tempo_renderizacao(duracao_audio, len(script_data))
    print(f"Tempo estimado de renderização: {tempo_estimado:.1f} minutos")

    try:
        video_path = renderizar_video(
            show_script_path=show_script_path,
            audio_path=audio_path,
            images_folder=images_folder,
            output_path=output_video_path,
            legendas_moviepy=None,  # Legendas removidas
            resolucao=resolucao,
            fps=fps
        )

        return video_path

    except Exception as e:
        print(f"\nERRO na renderização: {e}")
        import traceback
        traceback.print_exc()
        return None


def main():
    """
    Função principal com sistema de fila.
    Processa todos os projetos em output/ e move para resultados/.

    Para renderização RÁPIDA (testes):
    - Resolução: 1280x720
    - FPS: 15
    - Usar: python montar_video.py --fast

    Para renderização FINAL (qualidade):
    - Resolução: 1920x1080
    - FPS: 24
    - Usar: python montar_video.py
    """
    import sys

    try:
        print("=" * 70)
        print("SISTEMA DE MONTAGEM DE VÍDEOS - FILA")
        print("=" * 70)

        # Verificar dependências
        print("\n[VERIFICAÇÃO] Verificando dependências MoviePy...")
        instalado, msg = verificar_dependencias_moviepy()
        if not instalado:
            print(f"ERRO: {msg}")
            return
        print("OK Dependências OK")

        # Modo rápido ou qualidade
        modo_rapido = '--fast' in sys.argv

        if modo_rapido:
            print("\n*** MODO RÁPIDO ATIVADO ***")
            print("Resolução: 1280x720, FPS: 15")
            resolucao = (1280, 720)
            fps = 15
        else:
            print("\n*** MODO QUALIDADE FINAL ***")
            print("Resolução: 1920x1080, FPS: 24")
            resolucao = (1920, 1080)
            fps = 24

        # Diretórios
        pasta_output = Path("output")
        pasta_resultados = Path("resultados")
        pasta_resultados.mkdir(exist_ok=True)

        # Obter projetos
        projetos = obter_projetos_output(pasta_output)

        if not projetos:
            print("\nNenhum projeto encontrado em output/")
            return

        print(f"\n{len(projetos)} projeto(s) encontrado(s):")
        for p in projetos:
            print(f"  - {p.name}")

        # Processar cada projeto
        total_projetos = len(projetos)
        total_videos_gerados = 0
        total_videos_erro = 0

        for idx_projeto, pasta_projeto in enumerate(projetos, 1):
            print(f"\n{'#' * 70}")
            print(f"PROJETO [{idx_projeto}/{total_projetos}]: {pasta_projeto.name}")
            print(f"{'#' * 70}")

            # Obter subpastas de áudio
            subpastas = obter_subpastas_audio(pasta_projeto)

            if not subpastas:
                print(f"Nenhuma subpasta de áudio encontrada em {pasta_projeto.name}")
                continue

            print(f"\n{len(subpastas)} áudio(s) encontrado(s):")
            for s in subpastas:
                print(f"  - {s.name}")

            # Processar cada áudio
            sucessos_projeto = 0
            erros_projeto = 0

            for idx_audio, pasta_audio in enumerate(subpastas, 1):
                print(f"\n{'-' * 70}")
                print(f"ÁUDIO [{idx_audio}/{len(subpastas)}]: {pasta_audio.name}")
                print(f"{'-' * 70}")

                sucesso = processar_audio_para_video(
                    pasta_audio,
                    pasta_projeto.name,
                    resolucao,
                    fps
                )

                if sucesso:
                    sucessos_projeto += 1
                    total_videos_gerados += 1
                else:
                    erros_projeto += 1
                    total_videos_erro += 1

            # Resumo do projeto
            print(f"\n{'#' * 70}")
            print(f"RESUMO DO PROJETO: {pasta_projeto.name}")
            print(f"{'#' * 70}")
            print(f"OK Videos gerados: {sucessos_projeto}/{len(subpastas)}")
            print(f"ERRO Erros: {erros_projeto}/{len(subpastas)}")

            # Mover para resultados se todos os vídeos foram gerados
            if erros_projeto == 0 and len(subpastas) > 0:
                destino = pasta_resultados / pasta_projeto.name
                print(f"\nMovendo {pasta_projeto.name} para resultados/")
                shutil.move(str(pasta_projeto), str(destino))
                print(f"OK Movido para: {destino}")
            else:
                print(f"\nAVISO: Projeto NAO movido para resultados/ (houve erros ou sem audios)")

        # RESUMO FINAL GERAL
        print(f"\n{'=' * 70}")
        print("PROCESSAMENTO COMPLETO - RESUMO GERAL")
        print(f"{'=' * 70}")
        print(f"Total de projetos processados: {total_projetos}")
        print(f"Total de vídeos gerados: {total_videos_gerados}")
        print(f"Total de vídeos com erro: {total_videos_erro}")
        print(f"{'=' * 70}")

    except Exception as e:
        print(f"\nErro inesperado: {e}")
        import traceback
        traceback.print_exc()


if __name__ == "__main__":
    main()
