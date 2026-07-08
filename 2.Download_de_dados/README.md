# Download de Dados Espaciais (IBGE, MMA e outros)

## Download de dados

Nesta pasta, estão incluídas opções em Python e R para baixar dados atualizados de fontes de dados institucionais, como IBGE e MMA, por meio do pacote GeoBr desenvolvido pelo IPEA.

> **Referência Oficial:**
> Pereira, R.H.M.; Barbosa, R.J.; et. all (2026) geobr: Download Official Spatial Data Sets of Brazil. v2.0.0 GitHub repository - https://github.com/ipea/geobr.

---

## Arquivos Disponíveis no Repositório

* **`baixar_municipios.ipynb` (Python):** Um Jupyter Notebook que importa a base de dados oficial utilizando as bibliotecas `geobr` e `geopandas`. Ele lista os conjuntos de dados disponíveis e realiza o download focado na malha municipal brasileira do ano de 2025, exportando-a no formato Shapefile (`.shp`).
* **`baixar_municipios_R.r` (R):** Um script em linguagem R que utiliza as bibliotecas `geobr` e `sf` para o processamento e salvamento dos dados espaciais. Além do download dos limites de 2025, este script utiliza o `ggplot2` para gerar uma visualização (plot) simples do mapa do Brasil com fundo minimalista antes de realizar a exportação final.

---

## Pré-requisitos e Dependências

Para rodar estes arquivos, você precisará preparar o seu ambiente instalando as bibliotecas essenciais listadas abaixo. 

**No ambiente Python:**
* `pandas`
* `geopandas`
* `geobr`

**No ambiente R:**
* `geobr`
* `sf`
* `dplyr`
* `ggplot2`

---

## Como Utilizar

1. Escolha o script correspondente à linguagem de sua preferência.
2. Abra o script na sua IDE de trabalho (como JupyterLab, VS Code ou RStudio).
3. Localize as configurações de diretório no código (a variável `diretorio` no Python, ou a função `setwd()` no R). 
4. Substitua o caminho do arquivo inserindo a localização da pasta no seu computador onde deseja salvar os arquivos shapefile baixados.
5. Execute o código. O resultado final será o arquivo `municipios_2025.shp` salvo diretamente na sua máquina, pronto para análise.