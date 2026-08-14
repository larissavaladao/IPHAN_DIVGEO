#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
download_ada_sei_scraper.py
===========================
Faz scraping real do SEI para baixar os arquivos ADA dos processos.
Reutiliza padrão de PIPELINE_DBGEO.py com foco em ADA.

Uso:
    df_dados = pd.read_csv('lista.csv', sep=';')
    resultado = baixar_ada_do_sei(df_dados, in_dir, usuario, senha)
"""

import asyncio
import io
import logging
import os
import re
import sys
import zipfile
from pathlib import Path

try:
    import nest_asyncio
    nest_asyncio.apply()
except ImportError:
    pass  # nest_asyncio é opcional, para suporte a Jupyter

try:
    from playwright.async_api import async_playwright, TimeoutError as PlaywrightTimeout
except ImportError:
    raise ImportError("Instale: pip install playwright && playwright install chromium")


# ============================================================
# LOGGING
# ============================================================
logging.basicConfig(
    level=logging.INFO,
    format='%(message)s',
    handlers=[logging.StreamHandler(sys.stdout)]
)


# ============================================================
# CONFIGURAÇÃO
# ============================================================
SEI_URL = "https://sei-sip.iphan.gov.br"
SEI_LOGIN_URL = (SEI_URL + "/sip/login.php?sigla_orgao_sistema=IPHAN&sigla_sistema=SEI")

TIMEOUT_NAV = 60000
TIMEOUT_DOWNLOAD = 120000
WAIT_MS = 5000
WAIT_SHORT = 2000

EXTENSOES_VETORIAIS = {'.kml', '.kmz', '.shp', '.geojson', '.gpkg', '.gml'}
EXTENSOES_SHP_AUX = {'.dbf', '.shx', '.prj', '.cpg', '.qix', '.sbn', '.sbx'}


# ============================================================
# HELPERS
# ============================================================
def _is_sei_procedimento_url(link):
    """Verifica se link aponta para procedimento do SEI."""
    if not link:
        return False
    texto = str(link).lower()
    return (
        'procedimento_trabalhar' in texto
        or 'acao=procedimento_trabalhar' in texto
        or ('sei/controlador.php' in texto and 'acao=' in texto)
    )


def _normalizar_nome_arquivo(protocolo):
    """Normaliza protocolo para nome de arquivo seguro."""
    replacements = str.maketrans({'.': '', '-': '_', '/': '_', ' ': '_'})
    return str(protocolo).translate(replacements)


def _is_ada_name(nome_arquivo):
    """Verifica se nome corresponde a um arquivo ADA."""
    nome = Path(nome_arquivo).name.upper()
    if not nome:
        return False
    palavras = (
        'ADA',
        'ARQUIVO_ADA',
        'AREA_UTIL',
        'AREA_DIRETAMENTE',
        'EMPREENDIMENTO',
        'AREA_PROJETO',
        'POLIGONO',
    )
    return any(p in nome for p in palavras)


def _filtrar_vetoriais(membros):
    """Filtra apenas arquivos vetoriais."""
    vetoriais = []
    for membro in membros:
        nome = Path(membro).name
        if nome.endswith('/'):
            continue
        if Path(membro).suffix.lower() in EXTENSOES_VETORIAIS:
            vetoriais.append(membro)
    return vetoriais


def _selecionar_arquivo_ada(membros):
    """Escolhe o arquivo ADA mais provável do ZIP."""
    vetoriais = _filtrar_vetoriais(membros)
    if not vetoriais:
        return None

    candidatos_ada = [m for m in vetoriais if _is_ada_name(m)]
    if candidatos_ada:
        candidatos_ada.sort(key=lambda x: (len(x), x.lower()))
        return candidatos_ada[0]

    vetoriais.sort(key=lambda x: (len(x), x.lower()))
    return vetoriais[0]


def _arquivos_familia_shp(zf, membro):
    """Retorna arquivos da família de um shapefile."""
    stem = Path(membro).stem
    return [
        name for name in zf.namelist()
        if Path(name).stem == stem and 
           Path(name).suffix.lower() in (EXTENSOES_VETORIAIS | EXTENSOES_SHP_AUX)
    ]


def _extrair_membro_zip(zf, membro, destino_dir, nome_final):
    """Extrai um membro do ZIP, mantendo família do SHP."""
    destino_dir = Path(destino_dir)
    destino_dir.mkdir(parents=True, exist_ok=True)

    if Path(membro).suffix.lower() == '.shp':
        familia = _arquivos_familia_shp(zf, membro)
        for item in familia:
            nome_rel = Path(item).name
            alvo = destino_dir / nome_rel
            with zf.open(item, 'r') as src, open(alvo, 'wb') as dst:
                dst.write(src.read())
        return destino_dir / nome_final

    alvo = destino_dir / nome_final
    with zf.open(membro, 'r') as src, open(alvo, 'wb') as dst:
        dst.write(src.read())
    return alvo


def _extrair_ada_do_zip(conteudo_zip, protocolo, in_dir):
    """Extrai arquivo ADA de um ZIP."""
    with zipfile.ZipFile(io.BytesIO(conteudo_zip)) as zf:
        membros = [m for m in zf.namelist() if not m.endswith('/')]
        membro_ada = _selecionar_arquivo_ada(membros)
        if membro_ada is None:
            return None

        nome_base = _normalizar_nome_arquivo(protocolo)
        extensao = Path(membro_ada).suffix.lower()

        if extensao == '.shp':
            nome_saida = f"{nome_base}.shp"
        elif extensao in {'.kml', '.kmz'}:
            nome_saida = f"{nome_base}.kml"
        elif extensao in {'.geojson', '.gpkg', '.gml'}:
            nome_saida = f"{nome_base}{extensao}"
        else:
            nome_saida = f"{nome_base}.kml"

        # Remove artefatos antigos
        for arq in Path(in_dir).glob(f"{nome_base}*"):
            if arq.is_file():
                arq.unlink()

        alvo = _extrair_membro_zip(zf, membro_ada, in_dir, nome_saida)
        return str(alvo)


# ============================================================
# NAVEGAÇÃO SEI (async)
# ============================================================
async def _login_sei(page, usuario, senha):
    """Faz login no SEI."""
    msg = "  Acessando login do SEI..."
    logging.info(msg)
    print(msg)
    
    try:
        await page.goto(SEI_LOGIN_URL, wait_until='domcontentloaded',
                        timeout=TIMEOUT_NAV)
    except Exception as e:
        msg = f"  ✗ Erro ao acessar URL do login: {e}"
        logging.error(msg)
        print(msg)
        return False
    
    try:
        await page.wait_for_timeout(3000)
        
        # Aguardar campos aparecerem
        await page.wait_for_selector("#txtUsuario", timeout=10000)
        await page.wait_for_selector("#pwdSenha", timeout=10000)
        
        await page.fill("#txtUsuario", usuario)
        await page.fill("#pwdSenha", senha, force=True)
        await page.press("#pwdSenha", "Enter")
        await page.wait_for_timeout(WAIT_MS)

        if "controlador.php" in page.url or "principal.php" in page.url:
            msg = "  ✓ Login OK"
            logging.info(msg)
            print(msg)
            return True
        else:
            msg = f"  ✗ Falha no login. URL: {page.url}"
            logging.error(msg)
            print(msg)
            return False
    except Exception as e:
        msg = f"  ✗ Erro durante login: {e}"
        logging.error(msg)
        print(msg)
        return False


async def _pesquisar_processo(page, numero_sei):
    """Pesquisa e abre um processo."""
    msg = f"    Pesquisando processo {numero_sei}..."
    logging.info(msg)
    print(msg)
    
    try:
        campo = page.locator('input[id="txtPesquisaRapida"]')
        await campo.fill(numero_sei)
        await campo.press('Enter')
        await page.wait_for_load_state('domcontentloaded', timeout=TIMEOUT_NAV)
        await page.wait_for_timeout(WAIT_MS)
    except Exception as e:
        msg = f"    ✗ Erro ao pesquisar processo: {e}"
        logging.error(msg)
        print(msg)
        raise


async def _safe_click(element, description="elemento"):
    """Click seguro via JavaScript."""
    try:
        await element.scroll_into_view_if_needed()
        await asyncio.sleep(0.3)
    except Exception:
        pass
    try:
        await element.evaluate("el => el.click()")
    except Exception:
        await element.click(force=True, timeout=10000)


async def _expandir_arvore(page):
    """Expande árvore de documentos."""
    arvore = page.frame("ifrArvore")
    if not arvore:
        logging.warning("    Frame ifrArvore não encontrado")
        return False

    try:
        btn = arvore.locator('img[id^="iconAP"]').first
        if await btn.count() > 0:
            await btn.click()
            logging.info("    Expandindo árvore...")
            await page.wait_for_timeout(2000)
            for tentativa in range(5):
                aguarde_count = await arvore.locator('text=Aguarde').count()
                if aguarde_count == 0:
                    logging.info("    Árvore expandida")
                    return True
                await page.wait_for_timeout(2000)
            return True
        else:
            return False
    except Exception as e:
        logging.warning(f"    Erro ao expandir árvore: {e}")
        return False


async def _baixar_zip_processo(page, pasta_saida):
    """Baixa o ZIP completo do processo."""
    zip_path = pasta_saida / "_PROCESSO.zip"
    zip_dir = pasta_saida / "_ZIP"

    if zip_dir.exists() and any(zip_dir.rglob("*")):
        logging.debug("    ZIP já existe localmente")
        return zip_dir

    try:
        # Buscar botão ZIP
        btn_zip = None
        seletores_zip = [
            '[title*="ZIP" i]',
            '[title*="Gerar Arquivo" i]',
            'img[src*="gerar_zip"]',
            'img[src*="ico_gerar_zip"]',
        ]

        for frame in page.frames:
            if frame.name == 'ifrArvore':
                continue
            for sel in seletores_zip:
                try:
                    loc = frame.locator(sel)
                    if await loc.count() > 0:
                        btn_zip = loc.first
                        break
                except Exception:
                    pass
            if btn_zip:
                break

        if not btn_zip:
            logging.warning("    Botão ZIP não encontrado")
            return None

        # Clicar no ZIP
        popup_page = None
        try:
            async with page.context.expect_page(timeout=5000) as popup_info:
                await _safe_click(btn_zip, "botao_zip")
            popup_page = await popup_info.value
            await popup_page.wait_for_load_state('domcontentloaded')
            await popup_page.wait_for_timeout(2000)
        except Exception:
            await page.wait_for_timeout(2000)

        # Buscar botão Gerar
        btn_gerar = None
        seletores_gerar = [
            'button:has-text("Gerar")',
            'input[value="Gerar"]',
            'input[value="Gerar Arquivo"]',
            'a:has-text("Gerar")',
            '#btnGerar',
            'button.infraButton:has-text("Gerar")',
            'input.infraButton[value*="Gerar"]',
        ]

        paginas = [popup_page] if popup_page else []
        for tentativa in range(3):
            for pg in paginas:
                if pg and not pg.is_closed():
                    for sel in seletores_gerar:
                        try:
                            loc = pg.locator(sel)
                            if await loc.count() > 0:
                                btn_gerar = loc.first
                                break
                        except Exception:
                            pass
                    if btn_gerar:
                        break
            if not btn_gerar:
                for frame in page.frames:
                    for sel in seletores_gerar:
                        try:
                            loc = frame.locator(sel)
                            if await loc.count() > 0:
                                btn_gerar = loc.first
                                break
                        except Exception:
                            pass
                    if btn_gerar:
                        break
            if btn_gerar:
                break
            await page.wait_for_timeout(2000)

        if not btn_gerar:
            logging.warning("    Botão Gerar não encontrado")
            if popup_page and not popup_page.is_closed():
                await popup_page.close()
            return None

        # Download
        download_page = popup_page if popup_page and not popup_page.is_closed() else page
        try:
            async with download_page.expect_download(timeout=TIMEOUT_DOWNLOAD) as dl:
                await _safe_click(btn_gerar, "botao_gerar")
            download = await dl.value
            await download.save_as(str(zip_path))
        except Exception:
            if download_page != page:
                try:
                    async with page.expect_download(timeout=TIMEOUT_DOWNLOAD) as dl:
                        await _safe_click(btn_gerar, "botao_gerar")
                    download = await dl.value
                    await download.save_as(str(zip_path))
                except Exception as e:
                    logging.warning(f"    Erro no download: {e}")
                    if popup_page and not popup_page.is_closed():
                        await popup_page.close()
                    return None

        if popup_page and not popup_page.is_closed():
            await popup_page.close()

        # Extrair ZIP
        zip_dir.mkdir(exist_ok=True)
        try:
            with zipfile.ZipFile(zip_path) as zf:
                zf.extractall(zip_dir)
            zip_path.unlink(missing_ok=True)
            logging.info(f"    ZIP extraído: {len(list(zip_dir.iterdir()))} arquivos")
            return zip_dir
        except Exception as e:
            logging.warning(f"    Erro ao extrair ZIP: {e}")
            return None

    except Exception as e:
        logging.warning(f"    Erro baixando ZIP: {e}")
        return None


# ============================================================
# FUNÇÃO PRINCIPAL ASSÍNCRONA
# ============================================================
async def _processar_lote_async(df_dados, in_dir, usuario, senha,
                                 protocolo_col='Protocolo', id_col='ID',
                                 headless=True):
    """Processa um lote de processos via scraping SEI."""
    print("\n" + "=" * 70)
    print("INICIANDO SCRAPER DO SEI")
    print("=" * 70)
    
    os.makedirs(in_dir, exist_ok=True)
    arquivos_baixados = []

    async with async_playwright() as p:
        print("  Iniciando navegador Chromium...")
        browser = await p.chromium.launch(headless=headless)
        context = await browser.new_context()
        page = await context.new_page()

        try:
            # Login uma única vez
            print("\n" + "-" * 70)
            print("ETAPA 1: LOGIN")
            print("-" * 70)
            if not await _login_sei(page, usuario, senha):
                logging.error("Falha no login. Abortando.")
                print("✗ Abortando due to login failure")
                return arquivos_baixados

            # Processar cada linha
            print("\n" + "-" * 70)
            print("ETAPA 2: PROCESSANDO PROCESSOS")
            print("-" * 70)
            for idx, row in df_dados.iterrows():
                protocolo = row.get(protocolo_col)
                id_processo = row.get(id_col)

                if pd_isna(protocolo) or not str(protocolo).strip():
                    logging.warning(f"[{idx + 1}/{len(df_dados)}] Protocolo vazio; ignorando")
                    continue

                logging.info(f"[{idx + 1}/{len(df_dados)}] Processando: {protocolo} (ID: {id_processo})")

                try:
                    # Pesquisar processo
                    await _pesquisar_processo(page, str(protocolo))

                    # Criar pasta do processo
                    pasta_proc = Path(in_dir) / _normalizar_nome_arquivo(protocolo)

                    # Expandir árvore (opcional)
                    try:
                        await _expandir_arvore(page)
                    except Exception:
                        pass

                    # Baixar ZIP do processo
                    zip_dir = await _baixar_zip_processo(page, pasta_proc)
                    if not zip_dir or not zip_dir.exists():
                        logging.warning(f"  ✗ Falha ao baixar ZIP do processo")
                        continue

                    # Procurar arquivo ADA no ZIP
                    arquivo_ada = None
                    for root, dirs, files in os.walk(str(zip_dir)):
                        for file in files:
                            caminho_relativo = os.path.relpath(
                                os.path.join(root, file),
                                str(zip_dir)
                            )
                            if _is_ada_name(file):
                                arquivo_ada = os.path.join(root, file)
                                logging.info(f"  ✓ Arquivo ADA encontrado: {file}")
                                break
                        if arquivo_ada:
                            break

                    if not arquivo_ada:
                        logging.warning(f"  ✗ Nenhum arquivo ADA encontrado no ZIP")
                        continue

                    # Extrair o ZIP inteiro e selecionar o ADA
                    try:
                        with open(arquivo_ada, 'rb') as f:
                            conteudo = f.read()

                        if zipfile.is_zipfile(io.BytesIO(conteudo)):
                            # Se o arquivo ADA é um ZIP, extrair dele
                            arquivo_extraido = _extrair_ada_do_zip(
                                conteudo, protocolo, in_dir
                            )
                            if arquivo_extraido:
                                arquivos_baixados.append(arquivo_extraido)
                                logging.info(f"  ✓ Salvo: {arquivo_extraido}")
                        else:
                            # Se o arquivo ADA é um vetor direto, copiar para in_dir
                            nome_arquivo = f"{_normalizar_nome_arquivo(protocolo)}{Path(arquivo_ada).suffix.lower()}"
                            destino = os.path.join(in_dir, nome_arquivo)

                            with open(arquivo_ada, 'rb') as src, open(destino, 'wb') as dst:
                                dst.write(src.read())

                            arquivos_baixados.append(destino)
                            logging.info(f"  ✓ Salvo: {destino}")
                    except Exception as e:
                        logging.warning(f"  ✗ Erro ao processar arquivo ADA: {e}")
                        continue

                except Exception as exc:
                    logging.error(f"  ✗ ERRO no processo {protocolo}: {exc}")
                    continue

        finally:
            await browser.close()

    print("\n" + "=" * 70)
    msg = f"SCRAPING SEI CONCLUÍDO: {len(arquivos_baixados)}/{len(df_dados)} processos"
    logging.info(msg)
    print(msg)
    print("=" * 70 + "\n")

    return arquivos_baixados


# ============================================================
# WRAPPER SÍNCRONO (para chamar de notebooks)
# ============================================================
def baixar_ada_do_sei(df_dados, in_dir, usuario, senha,
                      protocolo_col='Protocolo', id_col='ID',
                      headless=True):
    """
    Interface síncrona para scraping de arquivos ADA do SEI.

    Parâmetros:
    -----------
    df_dados : pd.DataFrame
        DataFrame com lista de processos. Deve incluir as colunas:
        - Protocolo (ou a coluna especificada em protocolo_col)
        - ID (ou a coluna especificada em id_col)
    in_dir : str
        Diretório para salvar arquivos baixados.
    usuario : str
        Usuário SEI.
    senha : str
        Senha SEI.
    protocolo_col : str
        Nome da coluna com protocolo do processo.
    id_col : str
        Nome da coluna com ID do processo.
    headless : bool
        Se True, executa browser em modo headless (sem GUI).

    Retorno:
    --------
    list
        Lista de caminhos dos arquivos baixados.
    """
    return asyncio.run(
        _processar_lote_async(
            df_dados, in_dir, usuario, senha,
            protocolo_col, id_col, headless
        )
    )


def pd_isna(value):
    """Verifica se valor é NaN (compatível com pandas)."""
    try:
        import pandas as pd
        return pd.isna(value)
    except Exception:
        return value is None
