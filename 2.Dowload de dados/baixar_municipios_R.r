# https://github.com/ipea/geobr
# From CRAN
install.packages("geobr")
install.packages("ggplot2")

library(geobr)
library(sf)
library(dplyr)
library(ggplot2)

#ajustar pasta de trabalho
setwd("C:/Users/larissa.valadao/OneDrive - IPHAN - Instituto do Patrimônio Histórico e Artístico Nacional/Documentos/arquivos_analise/dados")
#nome de saída do arquivo
path = "municipios_2025.shp"

# Available data sets
datasets <- list_geobr(wide = TRUE)
head(datasets)

# Read all municipalities in the country at a given year
mun <- read_municipality(code_muni="all", year = 2025)
print(mun)

# Remove plot axis
no_axis <- theme(axis.title=element_blank(),
                 axis.text=element_blank(),
                 axis.ticks=element_blank())

# Plot all Brazilian states
ggplot() +
  geom_sf(data=mun , fill="#2D3E50", color="#FEBF57", size=.15, show.legend = FALSE) +
  labs(subtitle="Municipalities", size=8) +
  theme_minimal() +
  no_axis

# salvar dados
write_sf(mun , path)