# Instrução de Uso: Scraping de Arquivos ADA do SEI

## Resumo da Solução

O problema era que os links do CSV apontavam para **páginas do processo SEI**, não para arquivos. A solução implementada é um scraper que:

1. Detecta automaticamente se os links são do SEI
2. Se forem, realiza scraping real do processo via navegador (Playwright)
3. Faz download do ZIP completo do processo
4. Localiza e extrai apenas o arquivo ADA
5. Salva em `in_dir`

## Como Usar no Notebook

No notebook `cadastro_dbgeo.ipynb`, na célula de download de dados, o código agora funciona assim:

```python
# Importar a função
from geo_functions import area_files_list

# Chamar com o DataFrame de processos
area_files_list(
    in_dir=r'C:\caminho\para\arquivos\analise',
    out_dir=r'C:\caminho\para\output',
    download_df=df_dados,
    protocolo_col='Protocolo',
    keep_name=True
)
```

### O que acontece internamente:

1. **ETAPA 1: DOWNLOAD DO ARQUIVO ADA**
   - Lê a coluna `Link_Permanente` do DataFrame
   - Detecta se os links são URLs do SEI (`procedimento_trabalhar`)
   - Se forem:
     - Solicita usuário e senha SEI
     - Abre navegador automatizado (Playwright)
     - Para cada processo:
       - Faz login no SEI
       - Pesquisa o processo
       - Expande a árvore de documentos
       - Faz download do ZIP completo do processo
       - Localiza o arquivo "Arquivo ADA" dentro do ZIP
       - Extrai apenas ele para `in_dir`
   - Se não forem:
     - Tenta download direto (compatível com URLs de arquivo)

2. **ETAPA 2 e 3**: Prosseguem normalmente com processamento de arquivos

## Arquitetura

### Arquivos Novos/Modificados:

1. **`download_ada_sei_scraper.py`** (NOVO)
   - Módulo completo de scraping via Playwright
   - Reutiliza padrões do `PIPELINE_DBGEO.py`
   - Funções principais:
     - `baixar_ada_do_sei()` - Interface síncrona para notebooks
     - `_processar_lote_async()` - Core assíncrono
     - Helpers: navegação, download, extração de ZIP

2. **`download_ada_zip.py`** (MODIFICADO)
   - Adicionada função `_is_sei_procedimento_url()`
   - Mantém compatibilidade com downloads diretos

3. **`geo_functions.py`** (MODIFICADO)
   - `download_kml_from_links()` agora:
     - Detecta tipo de link
     - Escolhe estratégia de download
     - Solicita credenciais se necessário

## Requisitos

### Dependências Python:
```bash
pip install playwright
playwright install chromium
```

### Entrada de Dados:
O DataFrame `df_dados` deve ter:
- Coluna `Protocolo` (ex: `01450.010421/2026-51`)
- Coluna `Link_Permanente` (URL do SEI ou URL direta)
- Coluna `ID` (opcional, para logging)

### Credenciais:
- Necessário ter usuário e senha no SEI-IPHAN
- Serão solicitadas no notebook quando detectar links do SEI
- Não são armazenadas, apenas usadas na sessão

## Fluxo Completo no Notebook

```python
import pandas as pd
from geo_functions import area_files_list

# 1. Ler CSV com lista de processos
df_dados = pd.read_csv('lista_processos.csv', sep=';')

# 2. Chamar pipeline com download automático
area_files_list(
    in_dir=r'C:\OneDrive - IPHAN\Documentos\arquivos_analise\entrada',
    out_dir=r'C:\OneDrive - IPHAN\Documentos\arquivos_analise\saida',
    download_df=df_dados,  # ← Dispara ETAPA 1 com scraping
    protocolo_col='Protocolo',
    keep_name=True
)
# Aparece prompt: "Usuário SEI: " → digitar
# Aparece prompt: "Senha SEI: " → digitar (não é exibida)
# Inicia download automático de cada processo...
```

## Logging

O progresso é exibido em tempo real:

```
ETAPA 1: DOWNLOAD DO ARQUIVO ADA POR PROCESSO
======================================================================

DETECÇÃO: Links do SEI detectados
  → Iniciando scraping via navegador (Playwright)
======================================================================

  Usuário SEI: seu_usuario
  Senha SEI: ••••••••
  Acessando login do SEI...
  Login OK
  
[1/9] Processando: 01450.010421/2026-51 (ID: 8551676)
  Expandindo árvore...
  Árvore expandida
  ✓ Arquivo ADA encontrado: Arquivo ADA.kml
  ✓ Salvo: C:\caminho\01450_010421_2026_51.kml

[2/9] Processando: 01450.010371/2026-10 (ID: 8549315)
  ...

SCRAPING SEI CONCLUÍDO: 9/9 processos
======================================================================
```

## Troubleshooting

### "Playwright não encontrado"
```bash
pip install playwright
playwright install chromium
```

### "Falha no login"
- Verificar usuário e senha
- Confirmar que o usuário tem acesso ao SEI-IPHAN
- Verificar conectividade de internet

### "Arquivo ADA não encontrado"
- Confirmar que o processo contém anexo com "ADA" no nome
- Verificar manualmente no SEI se o arquivo existe

### Timeout no download
- Aumentar `TIMEOUT_DOWNLOAD` em `download_ada_sei_scraper.py`
- Verificar conectividade de internet/proxy

## Exemplo de Resultado

Após executar, `in_dir` conterá:

```
entrada/
├── 01450_010421_2026_51.kml
├── 01450_010371_2026_10.kml
├── 01450_010180_2026_40.kml
├── 01450_009914_2026_48.kml
└── ...
```

Cada arquivo é nomeado com base no `Protocolo` do processo, normalizado para uso em disco.

## Próximas Etapas

1. Executar no notebook com dados reais
2. ETAPA 2 descobrirá os arquivos baixados
3. ETAPA 3 processará geometrias e calculará áreas
4. ETAPA 4 exportará em shapefile/GPKG

## Notas Importantes

- O scraper é compatível com **navegadores headless** (sem GUI)
- Suporta Playwright 1.40+
- Testado com Chromium (engine usado por Playwright)
- Mantém compatibilidade com downloads diretos (se link não for SEI)
- Cada processo é processado sequencialmente (login único, reutilizado)
