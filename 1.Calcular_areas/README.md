# Pasta com duas opções de código para cálculo de área de todos os arquivos de um diretório

## Calculadora de Áreas e Limiares no QGIS (PyQGIS)

Este repositório contém um script em Python (PyQGIS) desenvolvido para rodar nativamente dentro do QGIS. Ele automatiza o cálculo de áreas de polígonos em lote, eliminando a necessidade de dependências externas como `geopandas` ou instalações via terminal.

O script unifica os polígonos de cada arquivo, calcula a área exata em hectares utilizando a projeção cônica equivalente de Albers (IBGE SIRGAS 2000), gera colunas com limiares de tolerância de 10% (máximo e mínimo) e exporta o resultado em novos arquivos Shapefile (EPSG:3857).

---

### Principais Funcionalidades

* **Processamento em Lote:** Lê múltiplos arquivos de uma vez e processa um por um.
* **Suporte a Múltiplos Formatos:** Aceita arquivos `.shp`, `.kml` e `.kmz` como entrada.
* **Interface Interativa:** Abre janelas nativas do sistema operacional para seleção fácil e visual das pastas de entrada e saída.
* **Zero Configuração:** Roda diretamente no Console Python do QGIS sem exigir instalação de bibliotecas adicionais.

---

### Pré-requisitos

* QGIS instalado (testado nas versões 3.x).
* Arquivos vetoriais contendo dados de polígonos, organizados em uma única pasta.
Importante: por hora os arquivos incluídos por meio de PyQGIS devem necessariamente conter apenas polygonos e/ou multipolígonos e kml/kmz devem conter apenas uma layer
---

### Como usar o script no QGIS

1. Abra o seu projeto no QGIS.
2. Na barra de menus superior, clique em **Complementos** e selecione **Console Python** (ou use o atalho `Ctrl + Alt + P`).
3. No painel do Console Python que se abrirá (geralmente na parte inferior da tela), clique no ícone **Mostrar Editor** (um ícone de bloco de notas).
4. Copie todo o código do arquivo `.py` deste repositório e cole no editor do QGIS, ou use o botão **Abrir Script** para carregar o arquivo salvo no seu computador.
5. Clique no botão **Executar Script** (ícone de "Play" verde) no topo do editor.
6. Uma janela do seu sistema operacional será aberta. Selecione a **pasta de entrada** onde estão os seus arquivos `.shp` ou `.kml`.
7. Outra janela será aberta logo em seguida. Selecione a **pasta de saída** onde os novos arquivos gerados devem ser salvos.
8. Aguarde a mensagem de confirmação na tela indicando que o processamento foi concluído com sucesso.

---

### Estrutura do Dado de Saída

Para cada arquivo processado, um novo arquivo `.shp` será gerado na pasta de destino escolhida, contendo uma geometria unificada (Multipolígono) e a seguinte tabela de atributos:

* **area_ha:** Área total calculada em hectares.
* **area_max:** Limite superior da área (+10%).
* **area_min:** Limite inferior da área (-10%).

> **Nota:** O sistema de coordenadas (CRS) dos arquivos finais exportados será o `EPSG:3857` (Pseudo-Mercator), facilitando a integração com mapas base da web, como o Google Maps ou OpenStreetMap.

## Cálculo de Áreas e Limiares em Lote (Jupyter Notebook)

Este diretório contém um Jupyter Notebook (`calculo_de_areas.ipynb`) desenvolvido para automatizar o processamento e o cálculo de áreas de arquivos geoespaciais. O script utiliza a biblioteca `geopandas` juntamente com `fiona` e `shapely` para ler dados complexos, corrigir e manipular geometrias, e gerar novos arquivos com métricas de área atualizadas.

Recebe kml/kmz com múltiplas camadas. Também realiza conversão de linhas em polígonos, quando possível e permite a alteração dos nomes do arquivos para padroniza-los com os números dos processos, ao mesmo tempo que adiciona uma coluna "processo" compatível com a camada de destino do DBGEO.

---

### Principais Funcionalidades

* **Processamento em Lote:** O script utiliza os módulos `glob` e `os` para varrer automaticamente um diretório em busca de arquivos compatíveis.
* **Gerenciamento de arquivos:** Alteração dos nomes dos arquivos e adição de numero de processo na tabela de atributos da camada.
* **Leitura Integral de KML/KMZ:** Através da função `ler_todas_camadas_kml`, o código contorna a limitação padrão do GeoPandas (que lê apenas a primeira camada) e extrai todas as camadas de arquivos iterando com a biblioteca `fiona`, garantindo que nenhuma feição seja perdida.
* **Conversão de Linhas para Polígonos:** A função `poligonize_lines` identifica automaticamente geometrias lineares (`LineString`, `MultiLineString`) e tenta fechá-las em polígonos através de operações topológicas, permitindo o cálculo de área em arquivos originais que foram desenhados como linhas.
* **Unificação de Geometrias:** A função `unify_geometries` mescla todos os polígonos de um arquivo em uma única geometria contínua (Multipolígono), preservando os atributos da primeira feição encontrada.
* **Cálculo Preciso de Área:** A função `area_calc` reprojeta temporariamente os dados para uma projeção plana, utilizando por padrão a projeção cônica equivalente *Albers IBGE SIRGAS 2000*, o que garante o cálculo correto da área métrica em hectares (`area_ha`).
* **Geração de Limiares:** O algoritmo calcula automaticamente um limite superior (`area_max`) e inferior (`area_min`) de área, baseado em um limiar configurável que, por padrão, é de 10%.
* **Exportação Padronizada:** O resultado final (contendo apenas as colunas de área e a geometria unificada) é exportado no formato Shapefile (`.shp`) e projetado em `EPSG:3857` (Pseudo-Mercator).

---

### Pré-requisitos

Para rodar este notebook, você precisará de um ambiente Python configurado. Certifique-se de ter os seguintes pacotes instalados:

* `pandas`
* `geopandas`
* `fiona`
* `shapely`

Você pode rodar este código em qualquer IDE compatível com notebooks `.ipynb` (como JupyterLab, VS Code com extensão Python, ou até mesmo no Google Colab). No próprio arquivo, há uma célula dedicada ao gerenciamento de pacotes onde é possível usar `%pip install <nome do pacote>` caso precise instalar dependências como o `fiona` de imediato.

---

### Como Utilizar o Script

1. Abra o arquivo `calculo_de_areas.ipynb` em sua IDE de preferência.
2. **Configuração de Diretórios:** Vá até a célula intitulada "definir caminhos fixos" e altere as variáveis `in_dir` e `out_dir` para que apontem para os caminhos absolutos das pastas de entrada e saída de arquivos no seu sistema.
* *Alternativa interativa:* Você pode descomentar o código na seção "copiar caminhos no prompt" para inserir os caminhos dinamicamente durante a execução.


3. **Variáveis de Projeção:** Caso queira usar o padrão do código (Albers IBGE), mantenha a variável `projecao = None`. Se precisar de outro CRS, insira o código EPSG no lugar (ex: `'EPSG:31983'`).
4. **Inserção de dicionário de dados:** Caso deseje renomear/inserir o numero de processo nos arquivos altere a variável `dados` para que as chaves do dicionário sejam o nome de entrada dos arquivos assim como aparecem quando baixados e os valores sejam os numeros dos processos como consta no SEI.
5. Execute as células sequencialmente para importar os pacotes e declarar as funções de trabalho (`area_calc`, `unify_geometries`, `extract_polygons`,`poligonize_lines`, `files_management`, `ler_todas_camadas_kml` e `area_files_list`).
6. **Execução Final:** Na última seção ("Aplicação das funções"), execute a célula `area_files_list(in_dir=in_dir, out_dir=out_dir, crs=projecao, )` para iniciar o processamento em lote. O log no console informará o andamento arquivo por arquivo e confirmará a criação dos novos `.shp` na pasta de saída.

---

### Funcionamento Interno (Visão Técnica)

A lógica central deste código é estruturada em torno de manipulações de `GeoDataFrames` utilizando o ecossistema geoespacial do Python. O fluxo principal opera da seguinte maneira:

1. A função central `area_files_list()` itera sobre a lista de arquivos encontrados na pasta fonte de dados.
2. **Leitura Condicional:** Se o arquivo for um Shapefile (`.shp`), é lido normalmente com `gpd.read_file()`. Se for um `.kml` ou `.kmz`, a função `ler_todas_camadas_kml()` assume o controle, ativando os drivers do `fiona`, lendo camada por camada e empilhando tudo via `pd.concat`.
3. **Poligonização:** O `GeoDataFrame` passa pela função `poligonize_lines()`, que separa as linhas dos polígonos pré-existentes, aplica o `shapely.ops.polygonize` para transformar anéis lineares fechados em novos polígonos, e recombina a base de dados.
4. **Unificação:** Caso a flag booleana de unificação esteja ativa (comportamento padrão), o código isola a primeira linha (`gdf[0:1].copy()`) para reter atributos, valida as geometrias (`make_valid()`) e sobrescreve sua coluna geométrica pela união massiva de todos os dados usando `union_all()`.
5. **Cálculo e Reprojeção:** Durante o cálculo na função `area_calc`, o dado sofre o processo analítico de reprojeção (`to_crs()`), seguido pelo cálculo algébrico `gdf.area / 10000` para registrar o quantitativo em hectares, além da aplicação de matemática básica para calcular limites máximo e mínimo.
6. **Exportação:** A tabela do `GeoDataFrame` é filtrada mantendo estritamente os campos `["area_ha", "area_max", "area_min", "geometry"]` e convertida para projeção Web Mercator (`EPSG:3857`), finalizando com o dump do arquivo no disco com a instrução de saída `.to_file()`.
