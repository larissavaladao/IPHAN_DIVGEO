# referencia  https://git.disroot.org/jpcasares/medir_distancia_entre.git
# selecionar layers
  # ADA - apenas um polígono / sítios - multipolígono ou multiponto
# definir projeção de medida - ibge
  # checar/reprojetar para a projeção  
# filtrar por distância
  # se sitios são pontos filtrar sitios a 600 metros da ADA
  # se sítios são polígonos filtras sitios a 300 da ADA
    # se o numero de geometrias do filtro for 0 
      #printar que não há sitios arquelogicos proximos que justifiquem analise manual
    # se o numero de geometrias for > 0:
      # calcular menor distancia entre sitios/ ADA
        #printar a distancia e o nome dos sítios
