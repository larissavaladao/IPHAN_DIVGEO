README - Scraper SEI para Download de Arquivos ADA
====================================================

## Problema Resolvido

O fluxo anterior tentava fazer download via links diretos do CSV, mas esses links apontavam para **páginas do processo no SEI**, não para arquivos geoespaciais. Resultado: zero arquivos baixados.

**Solução**: Scraper automatizado que navega no SEI via navegador (Playwright) e faz download real do ZIP do processo.

---

## Setup Rápido

### 1. Instalar Dependências

```bash
# Navegar até a pasta
cd IPHAN_DIVGEO\1.Calcular_areas

# Instalar pacotes Python
pip install -r requirements.txt

# Instalar navegador Chromium (necessário uma única vez)
playwright install chromium
```

**Tempo estimado**: 5-10 minutos (depende da velocidade da internet)

### 2. Verificar Instalação

```bash
# Executar testes
python teste_scraper_sei.py
```

Se tudo passar (ou passar com aviso de Playwright), está pronto.

---

## Como Usar no Notebook

### Pré-requisito
- Ter um arquivo CSV com lista de processos
- Coluna de protocolo no formato: `01450.010421/2026-51`
- Coluna com links (qualquer nome, será detectada automaticamente)

### Código no Notebook

```python
import pandas as pd
from geo_functions import area_files_list

# 1. Carregar lista de processos
df_dados = pd.read_csv(r'caminho\lista_processos.csv', sep=';')

# 2. Definir diretórios
in_dir = r'C:\OneDrive - IPHAN\...\entrada'
out_dir = r'C:\OneDrive - IPHAN\...\saida'

# 3. Executar pipeline (com download automático)
area_files_list(
    in_dir=in_dir,
    out_dir=out_dir,
    download_df=df_dados,           # ← Ativa download automático
    protocolo_col='Protocolo',      # ← Coluna com protocolo
    keep_name=True
)
```

### O que Acontece

1. **Detecção de Links**
   - Se links do CSV apontarem para SEI → Ativa scraper
   - Se forem URLs diretas → Download normal

2. **Scraping (se SEI)**
   ```
   → Solicita usuário SEI
   → Solicita senha SEI
   → Abre navegador (sem GUI)
   → Para cada processo:
      - Faz login (uma única vez, reutilizado)
      - Pesquisa o processo
      - Expande árvore de documentos
      - Faz download do ZIP completo
      - Localiza arquivo "Arquivo ADA"
      - Extrai apenas o ADA para entrada/
   ```

3. **Processamento**
   - Lê os arquivos baixados
   - Processa geometrias
   - Calcula áreas
   - Exporta shapefiles

---

## Arquitetura

### Novos Módulos

**`download_ada_sei_scraper.py`** (500+ linhas)
- Scraper completo com automação Playwright
- Reutiliza padrões de `PIPELINE_DBGEO.py`
- Interface síncrona para notebooks
- Suporta navegar múltiplos processos em uma sessão

**Modificações Existentes**
- `download_ada_zip.py`: Adicionada detecção de links SEI
- `geo_functions.py`: Integração automática de estratégia de download

---

## Arquivos da Solução

```
1.Calcular_areas/
├── download_ada_zip.py             (existente, com melhorias)
├── download_ada_sei_scraper.py     (NEW - scraper SEI)
├── geo_functions.py                (existente, com integração)
├── requirements.txt                (NEW - dependências)
├── INSTRUCOES_SCRAPER_SEI.md       (NEW - documentação detalhada)
├── teste_scraper_sei.py            (NEW - validação)
├── README.md                        (este arquivo)
└── cadastro_dbgeo.ipynb            (notebook - usar normalmente)
```

---

## Exemplos de Uso

### Exemplo 1: Download Automático (Recomendado)

```python
# Notebook de análise
import pandas as pd
from geo_functions import area_files_list

df = pd.read_csv('processos.csv', sep=';')

area_files_list(
    in_dir=r'C:\entrada',
    out_dir=r'C:\saida',
    download_df=df,              # ← Ativa download
    keep_name=True
)
```

### Exemplo 2: Usar Scraper Diretamente

```python
# Se precisar controle fino do download
from download_ada_sei_scraper import baixar_ada_do_sei

df = pd.read_csv('processos.csv', sep=';')

arquivos = baixar_ada_do_sei(
    df_dados=df,
    in_dir=r'C:\entrada',
    usuario='seu_usuario_sei',
    senha='sua_senha_sei'
)

print(f"Download: {len(arquivos)} arquivos")
for arq in arquivos:
    print(f"  - {arq}")
```

### Exemplo 3: Apenas Detecção (Sem Scraper)

```python
# Se quiser apenas testar detecção de links
from download_ada_zip import _is_sei_procedimento_url

link = "https://sei-sip.iphan.gov.br/sei/controlador.php?acao=procedimento_trabalhar&id_procedimento=123"

if _is_sei_procedimento_url(link):
    print("Este é um link do SEI → será usado scraper")
else:
    print("Link direto → será baixado normalmente")
```

---

## Troubleshooting

### "ModuleNotFoundError: No module named 'requests'"

```bash
pip install requests
```

### "ModuleNotFoundError: No module named 'playwright'"

```bash
pip install playwright
playwright install chromium
```

### "Falha no login"
- Verificar usuário e senha
- Confirmar acesso ao SEI-IPHAN
- Verificar firewall/proxy

### "Arquivo ADA não encontrado"
- Verificar manualmente que o processo contém anexo com "ADA"
- Algumas vezes o arquivo tem outro nome (veja logs)
- Contatar IPHAN se o anexo não existir

### "Timeout no download do ZIP"
- Aumentar timeout em `download_ada_sei_scraper.py` (linha ~34)
- Verificar conectividade
- Tentar novamente (às vezes rede instável)

### Notebook fica travado esperando input

Se o notebook mostrar `_` e não responde:
- Olhe para a barra de tarefas
- Pode haver uma caixa de diálogo ou terminal invisível
- Pressione Ctrl+C para interromper
- Tente novamente em uma célula nova

---

## Logs

O progresso é exibido em tempo real no console/notebook:

```
[1/9] Processando: 01450.010421/2026-51 (ID: 8551676)
  Expandindo árvore...
  Árvore expandida
  ✓ Arquivo ADA encontrado: Arquivo_ADA.kml
  ✓ Salvo: C:\entrada\01450_010421_2026_51.kml

[2/9] Processando: 01450.010371/2026-10 (ID: 8549315)
  ...

SCRAPING SEI CONCLUÍDO: 9/9 processos
```

---

## Requisitos de Sistema

- **SO**: Windows 10+ (testado em Windows), Linux, macOS
- **Python**: 3.8+
- **RAM**: 2GB+ (para navegador Playwright)
- **Rede**: Conexão com internet estável
- **SEI**: Usuário com acesso ao SEI-IPHAN

---

## Performance

- **Login**: ~3-5 segundos (primeira vez)
- **Por processo**: ~30-60 segundos (depende de tamanho do ZIP)
- **Total 9 processos**: ~5-10 minutos
- **Processamento pós-download**: ~1-2 minutos

---

## Próximas Etapas Após Download

1. **ETAPA 2**: Descoberta de arquivos baixados
2. **ETAPA 3**: Processamento de geometrias
3. **ETAPA 4**: Cálculo de áreas
4. **ETAPA 5**: Exportação em shapefile/GPKG

Tudo automático no fluxo `area_files_list()`.

---

## Contato / Suporte

Se encontrar problemas:

1. Verifique os logs da execução
2. Tente novamente (às vezes é problema de rede)
3. Valide os dados de entrada (CSV correto?)
4. Consulte `INSTRUCOES_SCRAPER_SEI.md` para detalhes técnicos

---

## Versão

- **v1.0** - Scraper SEI com integração ao fluxo de ADA
- **Data**: 2026-08-12
- **Autor**: GitHub Copilot (automação Python)

---

## Licença

Código reutilizando padrões de:
- `PIPELINE_DBGEO.py` (Vinicius P. Gonçalves, IPHAN-SC)
- `REEXTRAIR_VETOR.py` (idem)

Integração e scraper: GitHub Copilot

Uso livre para fins de pesquisa/análise IPHAN DIVGEO.
