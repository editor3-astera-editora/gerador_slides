"""
Módulo para renderização de vídeo com moviepy.
Combina imagens de slides, áudio e legendas sincronizadas.
"""

try:
    # moviepy 2.x (nova API)
    from moviepy import ImageClip, AudioFileClip, CompositeVideoClip, TextClip, concatenate_videoclips
except ImportError:
    # moviepy 1.x (API antiga)
    from moviepy.editor import ImageClip, AudioFileClip, CompositeVideoClip, TextClip, concatenate_videoclips

from pathlib import Path
import json


def renderizar_video(
    show_script_path,
    audio_path,
    images_folder,
    output_path,
    legendas_moviepy=None,
    resolucao=(1920, 1080),
    fps=24
):
    """
    Renderiza o vídeo final com slides sincronizados, áudio e legendas.

    Args:
        show_script_path (Path): Caminho para o show_script.json
        audio_path (Path): Caminho para o arquivo de áudio
        images_folder (Path): Pasta com as imagens dos slides
        output_path (Path): Caminho para salvar o vídeo final
        legendas_moviepy (list): Lista de legendas [(inicio, fim, texto)]
        resolucao (tuple): Resolução do vídeo (largura, altura)
        fps (int): Frames por segundo

    Returns:
        Path: Caminho do vídeo renderizado
    """
    show_script_path = Path(show_script_path)
    audio_path = Path(audio_path)
    images_folder = Path(images_folder)
    output_path = Path(output_path)

    print("=" * 70)
    print("RENDERIZAÇÃO DE VÍDEO")
    print("=" * 70)

    # Validar arquivos
    if not show_script_path.exists():
        raise FileNotFoundError(f"Script de apresentação não encontrado: {show_script_path}")

    if not audio_path.exists():
        raise FileNotFoundError(f"Arquivo de áudio não encontrado: {audio_path}")

    if not images_folder.exists():
        raise FileNotFoundError(f"Pasta de imagens não encontrada: {images_folder}")

    # Carregar show script
    print(f"\nCarregando script de apresentação: {show_script_path.name}")
    with open(show_script_path, 'r', encoding='utf-8') as f:
        show_script = json.load(f)

    # Carregar áudio
    print(f"Carregando áudio: {audio_path.name}")
    audio_clip = AudioFileClip(str(audio_path))
    duracao_audio = audio_clip.duration
    print(f"  Duração do áudio: {duracao_audio:.2f}s")

    # Criar clipes de vídeo para cada slide
    print(f"\nCriando clipes de vídeo para {len(show_script)} slides...")
    clips = []

    # Se o primeiro slide não começa em 0, estender para cobrir desde o início
    primeiro_timestamp = show_script[0]["timestamp"] if show_script else 0
    if primeiro_timestamp > 0.1:  # Tolerância de 0.1s
        print(f"\nAviso: Primeiro slide começa em {primeiro_timestamp:.2f}s")
        print(f"Estendendo primeiro slide para cobrir desde 0.0s (evitar tela preta)")

    for i, evento in enumerate(show_script):
        timestamp_inicio = evento["timestamp"]
        slide_index = evento["slide_index"]

        # Se é o primeiro slide e não começa em 0, ajustar para começar em 0
        if i == 0 and timestamp_inicio > 0.1:
            timestamp_inicio = 0.0
            print(f"  Ajuste: Slide {slide_index} agora inicia em 0.0s")

        # Determinar duração do clipe
        if i + 1 < len(show_script):
            timestamp_fim = show_script[i + 1]["timestamp"]
        else:
            timestamp_fim = duracao_audio

        duracao = timestamp_fim - timestamp_inicio

        # Ignorar clipes com duração inválida
        if duracao <= 0:
            print(f"  Aviso: Slide {slide_index} tem duração inválida ({duracao:.2f}s), ignorando...")
            continue

        # Caminho da imagem do slide
        image_path = images_folder / f"slide_{slide_index}.png"

        if not image_path.exists():
            print(f"  Aviso: Imagem não encontrada para slide {slide_index}: {image_path.name}")
            continue

        # Criar clipe de imagem
        clip = ImageClip(str(image_path), duration=duracao)

        # MoviePy 2.x usa with_* ao invés de set_*
        clip = clip.with_start(timestamp_inicio)
        clip = clip.with_position("center")

        # Redimensionar para resolução desejada se necessário
        clip = clip.resized(resolucao)

        clips.append(clip)

        print(f"  Slide {slide_index}: {timestamp_inicio:.2f}s -> {timestamp_fim:.2f}s (duracao: {duracao:.2f}s)")

    if not clips:
        raise ValueError("Nenhum clipe foi criado. Verifique as imagens dos slides.")

    print(f"\nOK {len(clips)} clipes criados")

    # Compor vídeo com CompositeVideoClip para respeitar os timestamps
    print("\nCompondo vídeo...")
    video = CompositeVideoClip(clips, size=resolucao)

    # Adicionar áudio
    print("Adicionando áudio...")
    video_com_audio = video.with_audio(audio_clip)

    # Adicionar legendas se fornecidas
    if legendas_moviepy:
        print(f"Adicionando {len(legendas_moviepy)} legendas...")
        video_com_audio = adicionar_legendas(video_com_audio, legendas_moviepy, resolucao)

    # Renderizar vídeo final
    print(f"\nRenderizando vídeo final para '{output_path.name}'...")
    print(f"  Resolução: {resolucao[0]}x{resolucao[1]}")
    print(f"  FPS: {fps}")
    print(f"  Codec: libx264")
    print("\nEste processo pode levar alguns minutos...\n")

    output_path.parent.mkdir(parents=True, exist_ok=True)

    # MoviePy 2.x mudou os parâmetros de write_videofile
    # Otimizações para renderização mais rápida:
    # - preset='ultrafast': Compressão mais rápida (arquivo maior, mas render 5-10x mais rápido)
    # - threads=4: Usa múltiplos threads para codificação paralela
    # - logger='bar': Barra de progresso limpa
    video_com_audio.write_videofile(
        str(output_path),
        fps=fps,
        codec='libx264',
        audio_codec='aac',
        temp_audiofile='temp-audio.m4a',
        remove_temp=True,
        preset='ultrafast',  # Opções: ultrafast, superfast, veryfast, faster, fast, medium, slow, slower, veryslow
        threads=4,  # Número de threads para codificação paralela
        logger='bar'  # Barra de progresso limpa
    )

    # Fechar clipes para liberar recursos
    video_com_audio.close()
    audio_clip.close()

    print("\n" + "=" * 70)
    print("OK VÍDEO RENDERIZADO COM SUCESSO!")
    print("=" * 70)
    print(f"Vídeo salvo em: {output_path}")
    print(f"Duração: {duracao_audio:.2f}s")
    print(f"Total de slides: {len(clips)}")
    if legendas_moviepy:
        print(f"Legendas: {len(legendas_moviepy)} legendas adicionadas")
    print("=" * 70)

    return output_path


def adicionar_legendas(video_clip, legendas_moviepy, resolucao):
    """
    Adiciona legendas ao vídeo usando PIL (sem necessidade de ImageMagick).

    Args:
        video_clip: Clipe de vídeo base
        legendas_moviepy (list): Lista de legendas [(inicio, fim, texto)]
        resolucao (tuple): Resolução do vídeo (largura, altura)

    Returns:
        CompositeVideoClip: Vídeo com legendas
    """
    # Tenta primeiro com TextClip (requer ImageMagick)
    # Se falhar, usa método alternativo com PIL
    try:
        return _adicionar_legendas_textclip(video_clip, legendas_moviepy, resolucao)
    except Exception as e:
        print(f"  Aviso: TextClip não disponível ({e})")
        print(f"  Usando método alternativo com PIL...")
        return _adicionar_legendas_pil(video_clip, legendas_moviepy, resolucao)


def _adicionar_legendas_textclip(video_clip, legendas_moviepy, resolucao):
    """Adiciona legendas usando TextClip (requer ImageMagick)."""
    texto_clips = []

    for inicio, fim, texto in legendas_moviepy:
        duracao = fim - inicio
        if duracao <= 0:
            continue

        txt_clip = TextClip(
            texto,
            fontsize=40,
            color='white',
            font='Arial',
            stroke_color='black',
            stroke_width=2,
            method='caption',
            size=(resolucao[0] - 100, None)
        )

        txt_clip = txt_clip.with_position(('center', resolucao[1] - 150))
        txt_clip = txt_clip.with_start(inicio)
        txt_clip = txt_clip.with_duration(duracao)
        texto_clips.append(txt_clip)

    if texto_clips:
        return CompositeVideoClip([video_clip] + texto_clips)
    return video_clip


def _adicionar_legendas_pil(video_clip, legendas_moviepy, resolucao):
    """Adiciona legendas usando PIL (funciona sem ImageMagick)."""
    from PIL import Image, ImageDraw, ImageFont
    import numpy as np

    texto_clips = []
    largura, altura = resolucao

    # Tenta carregar fonte do sistema
    try:
        # Windows - Arial
        fonte = ImageFont.truetype("arial.ttf", 40)
    except:
        try:
            # Linux - DejaVu Sans
            fonte = ImageFont.truetype("/usr/share/fonts/truetype/dejavu/DejaVuSans-Bold.ttf", 40)
        except:
            # Fallback - fonte padrão
            fonte = ImageFont.load_default()

    for inicio, fim, texto in legendas_moviepy:
        duracao = fim - inicio
        if duracao <= 0:
            continue

        try:
            # Criar imagem de legenda com PIL
            # Dimensões da caixa de legenda
            largura_legenda = largura - 100  # Margem de 50px cada lado
            altura_legenda = 150

            # Criar imagem transparente
            img = Image.new('RGBA', (largura_legenda, altura_legenda), (0, 0, 0, 0))
            draw = ImageDraw.Draw(img)

            # Calcular posição do texto (centralizado)
            bbox = draw.textbbox((0, 0), texto, font=fonte)
            text_width = bbox[2] - bbox[0]
            text_height = bbox[3] - bbox[1]

            x = (largura_legenda - text_width) // 2
            y = (altura_legenda - text_height) // 2

            # Desenhar borda (contorno) do texto
            for dx, dy in [(-2, -2), (-2, 2), (2, -2), (2, 2)]:
                draw.text((x + dx, y + dy), texto, font=fonte, fill='black')

            # Desenhar texto principal
            draw.text((x, y), texto, font=fonte, fill='white')

            # Converter PIL Image para numpy array
            img_array = np.array(img)

            # Criar ImageClip com a imagem da legenda
            legenda_clip = ImageClip(img_array, duration=duracao)
            legenda_clip = legenda_clip.with_start(inicio)
            legenda_clip = legenda_clip.with_position(('center', altura - 180))

            texto_clips.append(legenda_clip)

        except Exception as e:
            print(f"  Aviso: Erro ao criar legenda '{texto[:30]}...': {e}")
            continue

    # Compor vídeo com legendas
    if texto_clips:
        return CompositeVideoClip([video_clip] + texto_clips)
    return video_clip


def estimar_tempo_renderizacao(duracao_audio, num_slides):
    """
    Estima o tempo aproximado de renderização.

    Args:
        duracao_audio (float): Duração do áudio em segundos
        num_slides (int): Número de slides

    Returns:
        float: Tempo estimado em minutos
    """
    # Heurística: aproximadamente 2x a duração do áudio
    tempo_base = duracao_audio * 2

    # Adiciona tempo por slide
    tempo_por_slide = num_slides * 2

    tempo_total_segundos = tempo_base + tempo_por_slide

    return tempo_total_segundos / 60  # Retorna em minutos


def verificar_dependencias_moviepy():
    """
    Verifica se moviepy e suas dependências estão instaladas.

    Returns:
        tuple: (instalado: bool, mensagem: str)
    """
    try:
        import moviepy
        return True, "moviepy instalado corretamente"
    except ImportError:
        mensagem = (
            "moviepy não está instalado.\n"
            "Instale com: pip install moviepy\n"
            "Dependências adicionais:\n"
            "  - ImageMagick (para TextClip)\n"
            "  - ffmpeg (para codecs de vídeo)"
        )
        return False, mensagem
