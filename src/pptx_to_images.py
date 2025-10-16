"""
Módulo para converter slides PowerPoint em imagens PNG.
"""

from pathlib import Path
from pptx import Presentation
from pptx.util import Inches
import os


def exportar_slides_como_imagens(pptx_path, output_folder, width=1920, height=1080):
    """
    Exporta cada slide de uma apresentação PowerPoint como imagem PNG.

    NOTA: Esta função usa COM automation (Windows) ou conversão manual.
    Para conversão automática completa, é necessário ter PowerPoint instalado.

    Args:
        pptx_path (Path): Caminho para o arquivo PowerPoint
        output_folder (Path): Pasta onde salvar as imagens
        width (int): Largura da imagem em pixels
        height (int): Altura da imagem em pixels

    Returns:
        list: Lista de caminhos das imagens geradas
    """
    output_folder = Path(output_folder)
    output_folder.mkdir(exist_ok=True)

    pptx_path = Path(pptx_path)

    if not pptx_path.exists():
        raise FileNotFoundError(f"Arquivo PowerPoint não encontrado: {pptx_path}")

    print(f"Exportando slides de {pptx_path.name} para imagens...")

    # Verifica quantos slides existem
    prs = Presentation(pptx_path)
    total_slides = len(prs.slides)

    print(f"Total de slides a exportar: {total_slides}")

    # Tenta usar COM automation no Windows
    try:
        return _exportar_com_powerpoint_windows(pptx_path, output_folder, width, height, total_slides)
    except Exception as e:
        print(f"Aviso: Não foi possível usar PowerPoint COM automation: {e}")
        print("Tentando método alternativo com LibreOffice/conversão manual...")
        return _exportar_com_libreoffice(pptx_path, output_folder, total_slides)


def _exportar_com_powerpoint_windows(pptx_path, output_folder, width, height, total_slides):
    """
    Exporta slides usando PowerPoint COM automation (Windows apenas).
    Requer PowerPoint instalado.

    IMPORTANTE: Usa SaveAs com formato PNG para evitar bug do Export() que duplica slides.
    """
    import win32com.client
    import pythoncom
    import time
    import shutil

    # CRÍTICO: Inicializa COM para esta thread
    # Necessário pois pode ter sido desligado anteriormente
    try:
        pythoncom.CoInitialize()
    except:
        pass  # Já estava inicializado

    # Inicializa PowerPoint
    powerpoint = win32com.client.Dispatch("PowerPoint.Application")
    powerpoint.Visible = 1

    # Abre apresentação
    presentation = powerpoint.Presentations.Open(str(pptx_path.absolute()), WithWindow=False)

    # Aguarda o PowerPoint carregar completamente
    time.sleep(1)

    image_paths = []

    try:
        # Debug: verificar total de slides no COM
        com_total_slides = presentation.Slides.Count
        print(f"  DEBUG: PowerPoint COM reporta {com_total_slides} slides")

        if com_total_slides != total_slides:
            print(f"  AVISO: Divergência! python-pptx={total_slides}, COM={com_total_slides}")
            print(f"  Usando valor do COM: {com_total_slides}")
            total_slides = com_total_slides

        # SOLUÇÃO: Usar indexação 0-based (PowerPoint COM aceita Slides[0])
        # Bug identificado: range(1, N+1) pula Slides[0] e acessa Slides[N] que duplica o último
        print(f"  Exportando slides com indexação 0-based (Slides[0] até Slides[{total_slides-1}])...")

        # Fecha apresentação inicial
        presentation.Close()

        # CORREÇÃO: Usar range(0, total_slides) ao invés de range(1, total_slides+1)
        for i in range(0, total_slides):
            # Reabre apresentação para cada slide (força refresh completo)
            print(f"  Abrindo apresentação para slide COM[{i}]...")
            pres = powerpoint.Presentations.Open(str(pptx_path.absolute()), WithWindow=False)
            time.sleep(0.5)

            image_path = output_folder / f"slide_{i}.png"

            # Delete arquivo anterior se existir
            if image_path.exists():
                image_path.unlink()

            # Exporta usando indexação 0-based
            pres.Slides[i].Export(
                str(image_path.absolute()),
                "PNG",
                width,
                height
            )

            time.sleep(0.3)

            # Fecha apresentação
            pres.Close()

            # Verifica resultado
            if image_path.exists():
                size_kb = image_path.stat().st_size / 1024
                print(f"    COM Slides[{i}] -> slide_{i}.png ({size_kb:.1f} KB)")
                image_paths.append(image_path)
            else:
                print(f"    ERRO: Slide {i} nao foi criado!")

        # presentation já foi fechado no loop
        presentation = None

    finally:
        # Fecha apresentação e PowerPoint
        if presentation:
            try:
                presentation.Close()
            except:
                pass

        try:
            powerpoint.Quit()
        except:
            pass

        # CRÍTICO: Liberar recursos COM do Windows
        # Sem isso, arquivos .pptx ficam bloqueados
        import gc
        import time

        # Força liberação de objetos COM
        del presentation
        del powerpoint

        # Força garbage collection
        gc.collect()

        # Aguarda sistema liberar arquivos (Windows leva tempo)
        time.sleep(0.5)

        # NÃO chamar CoUninitialize() aqui!
        # Deixar COM ativo para próximas chamadas na mesma thread

    print(f"\nOK {len(image_paths)} slides exportados com sucesso")
    return image_paths


def _exportar_com_libreoffice(pptx_path, output_folder, total_slides):
    """
    Exporta slides usando LibreOffice (alternativa multiplataforma).
    Requer LibreOffice instalado.
    """
    import subprocess

    # Caminho absoluto do arquivo
    pptx_abs = pptx_path.absolute()
    output_abs = output_folder.absolute()

    # Comando LibreOffice para exportar como PNG
    # --headless: roda sem interface
    # --convert-to png: converte para PNG
    # --outdir: diretório de saída

    cmd = [
        "soffice",
        "--headless",
        "--convert-to", "png",
        "--outdir", str(output_abs),
        str(pptx_abs)
    ]

    try:
        result = subprocess.run(cmd, capture_output=True, text=True, timeout=60)

        if result.returncode != 0:
            raise Exception(f"LibreOffice falhou: {result.stderr}")

        # LibreOffice cria arquivos com nomes diferentes
        # Renomeia para o padrão esperado (slide_0.png, slide_1.png, etc.)
        image_paths = []
        for i in range(total_slides):
            # Nome gerado pelo LibreOffice (geralmente: nome_do_arquivo_i.png)
            libreoffice_name = output_folder / f"{pptx_path.stem}_{i}.png"
            target_name = output_folder / f"slide_{i}.png"

            if libreoffice_name.exists():
                libreoffice_name.rename(target_name)
                image_paths.append(target_name)
                print(f"  Slide {i+1}/{total_slides} exportado: {target_name.name}")

        return image_paths

    except FileNotFoundError:
        raise Exception("LibreOffice não encontrado. Instale LibreOffice ou use Windows com PowerPoint instalado.")


def verificar_imagens_exportadas(output_folder, total_slides):
    """
    Verifica se todas as imagens foram exportadas corretamente.

    Args:
        output_folder (Path): Pasta com as imagens
        total_slides (int): Número esperado de slides

    Returns:
        tuple: (sucesso: bool, imagens_faltando: list)
    """
    output_folder = Path(output_folder)
    imagens_faltando = []

    for i in range(total_slides):
        image_path = output_folder / f"slide_{i}.png"
        if not image_path.exists():
            imagens_faltando.append(i)

    sucesso = len(imagens_faltando) == 0

    return sucesso, imagens_faltando


def listar_imagens_exportadas(output_folder):
    """
    Lista todas as imagens de slides exportadas.

    Args:
        output_folder (Path): Pasta com as imagens

    Returns:
        list: Lista ordenada de caminhos das imagens
    """
    output_folder = Path(output_folder)

    images = sorted(output_folder.glob("slide_*.png"))

    return images
