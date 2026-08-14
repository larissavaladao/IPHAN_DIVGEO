# ============================================================================
# REFACTORED GEOSPATIAL PROCESSING WORKFLOW
# Organização: Utilitários → Leitura → Processamento → Pipeline Principal
# ============================================================================

import io
import os
import re
import zipfile
import sys
from glob import glob
import pandas as pd
from pathlib import Path
from urllib.parse import urlparse

# Importações geoespaciais (opcionais - podem não estar disponíveis no Windows)
try:
    import fiona
    import geopandas as gpd
    from shapely.ops import polygonize
    from shapely.geometry import MultiPolygon
    GEOSPATIAL_DISPONIVEL = True
except ImportError:
    GEOSPATIAL_DISPONIVEL = False
    gpd = None
    fiona = None
    polygonize = None
    MultiPolygon = None

import requests


from download_ada_sei_scraper import baixar_ada_do_sei


# ============================================================================
# 1. FUNÇÕES UTILITÁRIAS - Download e Gerenciamento de Arquivos
# ============================================================================

def files_management(file):
    """
    Realiza a leitura de arquivos geoespaciais e prepara informações para exportação.

    Parâmetros:
    -----------
    file : str
        Caminho do arquivo de entrada.
    dados : dict, opcional
        Dicionário contendo associação entre nome base e número do processo.

    Retorno:
    --------
    tuple
        (nome_saida, GeoDataFrame)
    """
    
    name = os.path.split(file)[-1]
    in_name = name.split(".")[0]
    type_name = name.split(".")[-1]
    
    print(f"Processando {name}")
    
    # Lê o arquivo
    if type_name != 'shp':
        gdf = ler_todas_camadas_kml(file)
        out_name = in_name
    else:
        gdf = gpd.read_file(file)
        # Renomeação com transformação de caracteres
        replacements = str.maketrans({".": "", "-": "_", "/": "_"})
        out_name = str(file.parent.name).translate(replacements)
    
    if gdf is None or gdf.empty:
        return None, None
    
    
    return out_name, gdf



# ============================================================================
# 2. FUNÇÕES DE LEITURA E TRANSFORMAÇÃO GEOESPACIAL
# ============================================================================

def ler_todas_camadas_kml(caminho_kml):
    """
    Lê todas as camadas (layers) de um arquivo KML e as combina em um único GeoDataFrame.
    """
    
    fiona.drvsupport.supported_drivers['KML'] = 'rw'
    fiona.drvsupport.supported_drivers['LIBKML'] = 'rw'

    try:
        camadas = fiona.listlayers(caminho_kml)
        print(f"  ↳ {len(camadas)} camadas encontradas")
    except ValueError as e:
        print(f"  ✗ Erro ao ler KML: {e}")
        return None

    lista_gdfs = []
    
    # Prioriza camada "ADA" se existir
    if ("ADA" in camadas) or ("ada" in camadas):
        camadas = ["ADA"]
    
    for camada in camadas:
        print(f"  ↳ Lendo: {camada}")
        gdf_camada = gpd.read_file(caminho_kml, driver='KML', layer=camada)
        
        if not gdf_camada.empty:
            gdf_camada['nome_camada_origem'] = camada 
            lista_gdfs.append(gdf_camada)
        else:
            print(f"    (vazia, ignorada)")

    if lista_gdfs:
        gdf_completo = pd.concat(lista_gdfs, ignore_index=True)
        print(f"  ✓ Total: {len(gdf_completo)} registros\n")
        return gdf_completo
    
    print("  ✗ Nenhuma geometria válida encontrada\n")
    return None


def extract_polygons(geom):
    """
    Extrai apenas Polygon e MultiPolygon de qualquer geometria, 
    incluindo GeometryCollection.
    """
    
    if geom.geom_type in ("Polygon", "MultiPolygon"):
        return geom

    if geom.geom_type == "GeometryCollection":
        polys = [g for g in geom.geoms if g.geom_type in ("Polygon", "MultiPolygon")]
        
        if len(polys) == 1:
            return polys[0]
        elif len(polys) > 1:
            return MultiPolygon([
                p for g in polys
                for p in (g.geoms if g.geom_type == "MultiPolygon" else [g])
            ])
    
    return None


def poligonize_lines(gdf):
    """
    Converte geometrias lineares (LineString, MultiLineString) em polígonos.
    """
    
    is_line = gdf['geometry'].type.isin(["LineString", "MultiLineString"])
    is_plo = gdf['geometry'].type.isin(["Polygon", "MultiPolygon"])
    
    gdf_lines = gdf[is_line]
    gdf_pol = gdf[is_plo].copy()
    
    if gdf_lines.empty:
        print("  ↳ Sem geometrias lineares")
        return gdf
    
    print(f"  ↳ Convertendo {len(gdf_lines)} linhas em polígonos...")
    
    lines_list = gdf_lines['geometry'].tolist()
    polygons = list(polygonize(lines_list))
    
    if not polygons:
        print("  ✗ Nenhum polígono fechado formado")
        return gdf_pol
    
    gdf_poligonos = gpd.GeoDataFrame(geometry=polygons, crs=gdf.crs)
    
    # Copia atributos da primeira linha
    for col in gdf.columns:
        if col != 'geometry':
            try:
                gdf_poligonos[col] = gdf[col].iloc[0]
            except:
                pass
    
    print(f"  ✓ {len(gdf_poligonos)} polígonos criados")

    if not gdf_pol.empty:
        gdf_result = pd.concat([gdf_pol, gdf_poligonos], ignore_index=True)
        gdf_result.geometry = gdf_result.geometry.force_2d()
        gdf_result["geometry"] = gdf_result.geometry.apply(extract_polygons)
        gdf_result = gdf_result[gdf_result.geometry.notna()]
        return gdf_result
    else:
        gdf_poligonos.geometry = gdf_poligonos.geometry.force_2d()
        gdf_poligonos["geometry"] = gdf_poligonos.geometry.apply(extract_polygons)
        gdf_poligonos = gdf_poligonos[gdf_poligonos.geometry.notna()]
        return gdf_poligonos


def unify_geometries(gdf):
    """
    Unifica todas as geometrias de um GeoDataFrame em uma única geometria.
    """
    
    gdf_union = gdf[0:1].copy()
    geometrias_validas = gdf.geometry.make_valid()
    geometria_unica = geometrias_validas.union_all()
    gdf_union['geometry'] = [geometria_unica]
    
    print("  ✓ Geometrias unificadas")
    return gdf_union


def area_calc(gdf, crs=None, limiar=10):
    """
    Calcula a área em hectares de cada feição com limiares superior e inferior.
    """
    
    if crs is None:
        wkt = 'PROJCS["Albers_IBGE_SIRGAS2000",\
        GEOGCS["GCS_SIRGAS_2000",\
            DATUM["D_SIRGAS_2000",\
                SPHEROID["GRS_1980",6378137.0,298.257222101]],\
            PRIMEM["Greenwich",0.0],\
            UNIT["Degree",0.0174532925199433]],\
        PROJECTION["Albers_Conic_Equal_Area"],\
        PARAMETER["False_Easting",5000000.0],\
        PARAMETER["False_Northing",10000000.0],\
        PARAMETER["central_meridian",-54.0],\
        PARAMETER["standard_parallel_1",-12.5],\
        PARAMETER["standard_parallel_2",-22.5],\
        PARAMETER["latitude_of_origin",-32.0],\
        UNIT["Meter",1.0]]'
        
        gdf_crs = gdf.to_crs(wkt)
        print("  ↳ Projeção: Albers IBGE SIRGAS 2000")
    else:
        gdf_crs = gdf.to_crs(crs)
        print(f"  ↳ Projeção: {gdf_crs.crs}")

    gdf_crs["area_ha"] = gdf_crs.area / 10000
    perc = (limiar / 100)
    gdf_crs["area_max"] = gdf_crs['area_ha'] * (1 + perc)
    gdf_crs["area_min"] = gdf_crs['area_ha'] * (1 - perc)

    print(f"  ✓ Áreas calculadas (±{limiar}%)")
    return gdf_crs.to_crs('EPSG:3857')


# ============================================================================
# 3. FUNÇÃO DE PIPELINE PRINCIPAL
# ============================================================================

def area_files_list(in_dir, out_dir, unify=True, 
                    crs=None, limiar=10):
    """
    Pipeline principal: baixa KMLs (opcional), processa geometrias e calcula áreas.
    
    Parâmetros:
    -----------
    in_dir : str
        Diretório com arquivos de entrada.
    out_dir : str
        Diretório para salvar shapefiles processados.
    keep_name : bool
        Se True, mantém nomes originais dos arquivos.
    dados : dict, opcional
        Dicionário para renomeação de arquivos.
    unify : bool
        Se True, unifica todas as geometrias.
    crs : str, opcional
        Sistema de referência de coordenadas para cálculo de área.
    limiar : int
        Limiar percentual para áreas máximas/mínimas (default: 10%).
    download_df : pd.DataFrame, opcional
        DataFrame com links para download automático de KMLs.
    protocolo_col : str
        Coluna com protocolo (nome do arquivo) no download_df.
    link_col : str
        Coluna com links no download_df.
    
    Exemplo:
    --------
    # Com download automático
    area_files_list(in_dir, out_dir, download_df=df_dados, keep_name=True)
    
    # Sem download, apenas processamento
    area_files_list(in_dir, out_dir, dados=dados_dict, keep_name=False)
    """
    
    
    # ETAPA 1: Descoberta de arquivos
    print("=" * 70)
    print("ETAPA 1: DESCOBERTA DE ARQUIVOS")
    print("=" * 70 + "\n")
    
    list_shapefiles = glob(os.path.join(in_dir, "*.shp"))
    list_kml = glob(os.path.join(in_dir, "*.kml"))
    list_kmz = glob(os.path.join(in_dir, "*.kmz"))
    
    print(f"  • Shapefiles: {len(list_shapefiles)}")
    print(f"  • KML: {len(list_kml)}")
    print(f"  • KMZ: {len(list_kmz)}")
    
    list_files = list_shapefiles + list_kml + list_kmz
    total_arquivos = len(list_files)
    
    print(f"\n  TOTAL: {total_arquivos} arquivos para processar\n")
    
    os.makedirs(out_dir, exist_ok=True)
    
    # ETAPA 3: Processamento de cada arquivo
    print("=" * 70)
    print(f"ETAPA 2: PROCESSAMENTO ({total_arquivos} arquivos)")
    print("=" * 70 + "\n")
    
    arquivos_processados = 0
    
    for idx, file in enumerate(list_files, 1):
        print(f"\n[{idx}/{total_arquivos}] {os.path.basename(file)}")
        print("-" * 70)
        
        try:
            # Lê o arquivo
            out_name, gdf = files_management(file=file)
            
            if gdf is None or gdf.empty:
                print(f"  ✗ Arquivo vazio, pulando\n")
                continue
            
            # Converte linhas em polígonos
            print("  Transformando geometrias...")
            gdf = poligonize_lines(gdf)
            
            # Unifica geometrias (opcional)
            if unify:
                gdf = unify_geometries(gdf)
            
            # Calcula áreas
            print("  Calculando áreas...")
            gdf_area = area_calc(gdf=gdf, crs=crs, limiar=limiar)
            
            # Seleciona colunas finais
            gdf_area = gdf_area[["area_ha", "area_max", "area_min", "geometry"]]
            
            
            # Remove GeometryCollections
            print("  Validando geometrias...")
            gdf_area["geometry"] = gdf_area.geometry.apply(extract_polygons)
            gdf_area = gdf_area[gdf_area.geometry.notna()]
            
            # Salva
            arquivo_saida = os.path.join(out_dir, f"{out_name}.shp")
            gdf_area.to_file(arquivo_saida)
            
            print(f"  ✓ Salvo: {arquivo_saida}")
            arquivos_processados += 1
            
        except Exception as e:
            print(f"  ✗ ERRO: {e}\n")
    
    # Resumo final
    print("\n" + "=" * 70)
    print("PROCESSAMENTO CONCLUÍDO")
    print("=" * 70)
    print(f"  • Arquivos processados com sucesso: {arquivos_processados}/{total_arquivos}")
    print(f"  • Diretório de saída: {out_dir}")
    print("=" * 70 + "\n")
