import os
from glob import glob
from qgis.core import (
    QgsVectorLayer, 
    QgsGeometry, 
    QgsCoordinateReferenceSystem,
    QgsCoordinateTransform, 
    QgsProject, 
    QgsFeature, 
    QgsFields, 
    QgsField,
    QgsVectorFileWriter
)
from qgis.PyQt.QtWidgets import QFileDialog, QMessageBox
from qgis.PyQt.QtCore import QVariant

def run_area_calculator():
    """
    Função principal que gerencia as pastas e processa os arquivos.
    """
    # 1. Abre janelas para o usuário escolher as pastas (fácil compartilhamento)
    in_dir = QFileDialog.getExistingDirectory(None, "Selecione a pasta de ENTRADA (onde estão os SHP/KML)")
    if not in_dir:
        print("Operação cancelada pelo usuário (Pasta de entrada não selecionada).")
        return

    out_dir = QFileDialog.getExistingDirectory(None, "Selecione a pasta de SAÍDA (onde salvar os resultados)")
    if not out_dir:
        print("Operação cancelada pelo usuário (Pasta de saída não selecionada).")
        return

    # Parâmetro de limiar
    limiar = 10 

    # Busca arquivos .shp e .km* (.kml, .kmz)
    list_files = glob(os.path.join(in_dir, "*.shp")) + glob(os.path.join(in_dir, "*.km*"))
    print(f"Total de arquivos encontrados: {len(list_files)}\n")

    if not list_files:
        return

    # 2. Configurações de Sistema de Coordenadas (CRS)
    # WKT do Albers IBGE SIRGAS 2000 fornecido no script original
    wkt_albers = (
        'PROJCS["Albers_IBGE_SIRGAS2000",'
        'GEOGCS["GCS_SIRGAS_2000",'
        'DATUM["D_SIRGAS_2000",SPHEROID["GRS_1980",6378137.0,298.257222101]],'
        'PRIMEM["Greenwich",0.0],'
        'UNIT["Degree",0.0174532925199433]],'
        'PROJECTION["Albers_Conic_Equal_Area"],'
        'PARAMETER["False_Easting",5000000.0],'
        'PARAMETER["False_Northing",10000000.0],'
        'PARAMETER["central_meridian",-54.0],'
        'PARAMETER["standard_parallel_1",-12.5],'
        'PARAMETER["standard_parallel_2",-22.5],'
        'PARAMETER["latitude_of_origin",-32.0],'
        'UNIT["Meter",1.0]]'
    )
    
    crs_albers = QgsCoordinateReferenceSystem()
    crs_albers.createFromWkt(wkt_albers)
    crs_out = QgsCoordinateReferenceSystem("EPSG:3857") # Projeção de saída
    context = QgsProject.instance().transformContext()

    # 3. Processamento de cada arquivo
    for file_path in list_files:
        filename = os.path.basename(file_path)
        out_name = os.path.splitext(filename)[0]
        print(f"Processando: {filename}")

        # Carrega o arquivo no QGIS temporariamente
        layer = QgsVectorLayer(file_path, out_name, "ogr")
        if not layer.isValid():
            print(f"  -> Erro ao ler o arquivo {filename}. Pulando...")
            continue

        # --- A. Unificar Geometrias (Dissolve) ---
        unified_geom = None
        for feat in layer.getFeatures():
            geom = feat.geometry()
            if unified_geom is None:
                unified_geom = QgsGeometry(geom)
            else:
                unified_geom = unified_geom.combine(geom)
        
        if unified_geom is None or unified_geom.isEmpty():
            print("  -> Geometria vazia. Pulando...")
            continue
        print("  -> Polígonos unificados.")

        # --- B. Calcular Área (em Albers) ---
        # Reprojeta a geometria unificada para Albers para medir a área em m2
        geom_albers = QgsGeometry(unified_geom)
        transform_albers = QgsCoordinateTransform(layer.crs(), crs_albers, context)
        geom_albers.transform(transform_albers)
        
        area_ha = geom_albers.area() / 10000.0
        perc = limiar / 100.0
        area_max = area_ha * (1 + perc)
        area_min = area_ha * (1 - perc)
        print(f"  -> Área: {area_ha:.2f} ha (Variação de {limiar}%)")

        # --- C. Salvar Novo Shapefile (em EPSG:3857) ---
        # Reprojeta a geometria original para EPSG:3857 para o arquivo final
        geom_out = QgsGeometry(unified_geom)
        transform_out = QgsCoordinateTransform(layer.crs(), crs_out, context)
        geom_out.transform(transform_out)

        # Define as colunas (fields) do novo shapefile
        new_fields = QgsFields()
        new_fields.append(QgsField("area_ha", QVariant.Double, len=20, prec=4))
        new_fields.append(QgsField("area_max", QVariant.Double, len=20, prec=4))
        new_fields.append(QgsField("area_min", QVariant.Double, len=20, prec=4))

        out_path = os.path.join(out_dir, f"{out_name}.shp")

        # Prepara a criação do arquivo shapefile
        options = QgsVectorFileWriter.SaveVectorOptions()
        options.driverName = "ESRI Shapefile"
        options.fileEncoding = "UTF-8"
        
        writer = QgsVectorFileWriter.create(
            out_path, new_fields, geom_out.wkbType(), crs_out, context, options
        )

        # Adiciona a feição com a geometria e os atributos calculados
        out_feat = QgsFeature(new_fields)
        out_feat.setGeometry(geom_out)
        out_feat.setAttribute("area_ha", area_ha)
        out_feat.setAttribute("area_max", area_max)
        out_feat.setAttribute("area_min", area_min)

        writer.addFeature(out_feat)
        del writer # Fecha e salva o arquivo
        
        print(f"  -> Arquivo {out_name}.shp salvo em {out_dir}\n")

    print("=== Processamento concluído! ===")
    
    # Exibe uma mensagem de sucesso na tela do usuário
    QMessageBox.information(None, "Sucesso", "Cálculo de áreas finalizado com sucesso!")

# Executa a função
run_area_calculator()