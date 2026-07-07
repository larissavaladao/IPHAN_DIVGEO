import pandas as pd
import geopandas as gpd
from glob import glob
import os

def area_calc(gdf, crs=None, area_unit="ha"):
  try:
    area_unit is in ["ha", "km2", "m2"]
  except:
    print("Unidade de área não permitida. Utilize 'ha', 'km2' ou 'm2'")
    
  if crs is None:
    crs = PROJCS["Albers_IBGE_SIRGAS2000",
    GEOGCS["GCS_SIRGAS_2000",
        DATUM["D_SIRGAS_2000",
            SPHEROID["GRS_1980",6378137.0,298.257222101]],
        PRIMEM["Greenwich",0.0],
        UNIT["Degree",0.0174532925199433]],
    PROJECTION["Albers_Conic_Equal_Area"],
    PARAMETER["False_Easting",5000000.0],
    PARAMETER["False_Northing",10000000.0],
    PARAMETER["central_meridian",-54.0],
    PARAMETER["standard_parallel_1",-12.5],
    PARAMETER["standard_parallel_2",-22.5],
    PARAMETER["latitude_of_origin",-32.0],
    UNIT["Meter",1.0]]

    gdf_crs = gdf.to_crs(crs)
    print("Projeção utilizada: Albers IBGE SIRGAS 2000")
    
  else:
    gdf_crs = gdf.to_crs(crs)
    try: 
      gdf_crs.crs.is_projected
    except:
      print(f"A projeção {gdf_crs.crs} não é planar (é geográfica/angular).")
    else:
      print(f"Projeção utilizada: {gdf_crs.crs}")

  
