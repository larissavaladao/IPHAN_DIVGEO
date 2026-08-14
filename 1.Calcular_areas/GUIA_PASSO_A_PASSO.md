GUIA PASSO A PASSO - Usando o Scraper SEI
==========================================

Este guia assume que você está usando Windows e tem acesso ao SEI-IPHAN.

## Passo 1: Preparar Ambiente (5 minutos)

### 1.1 Abrir Terminal PowerShell

- Pressione `Win + R`
- Digite `powershell`
- Pressione Enter

### 1.2 Navegar até a Pasta do Projeto

```powershell
cd "C:\Users\larissa.valadao\Documents\GitHub\IPHAN_DIVGEO\1.Calcular_areas"
```

### 1.3 Instalar Dependências

```powershell
pip install -r requirements.txt
```

Espere até aparecer a mensagem "Successfully installed" (pode levar vários minutos).

### 1.4 Instalar Navegador Chromium

```powershell
playwright install chromium
```

Espere completar (precisa fazer download).

### 1.5 Validar Instalação

```powershell
python teste_scraper_sei.py
```

Você deve ver:
- ✓ PASS: Compilação
- ✓ PASS: Imports
- ✓ PASS: Detecção de Links
- ✓ PASS: Integração
- FAIL: Playwright (OK se for resultado desta última)

Se aparecer "Tudo ok!", pode prosseguir para o Passo 2.

---

## Passo 2: Preparar Dados de Entrada (2 minutos)

### 2.1 Certifique-se de que tem um CSV com lista de processos

O arquivo deve ter:
- Delimitador: `;` (ponto-e-vírgula)
- Coluna `Protocolo`: ex `01450.010421/2026-51`
- Coluna `Link_Permanente` ou `Link_SEI`: com URLs

Exemplo de primeiras 3 linhas:

```
ID;Protocolo;Link_Permanente;...
8551676;01450.010421/2026-51;https://sei-sip.iphan.gov.br/sei/controlador.php?acao=procedimento_trabalhar&id_procedimento=8551676;...
8549315;01450.010371/2026-10;https://sei-sip.iphan.gov.br/sei/controlador.php?acao=procedimento_trabalhar&id_procedimento=8549315;...
```

### 2.2 Defina os Caminhos de Entrada/Saída

Escolha onde quer que os arquivos sejam salvos. Exemplo:

- **Entrada (onde baixar)**: `C:\OneDrive - IPHAN\Documentos\arquivos_analise\entrada`
- **Saída (onde processar)**: `C:\OneDrive - IPHAN\Documentos\arquivos_analise\saida`

Crie as pastas se não existirem (clique direito → Nova Pasta).

---

## Passo 3: Usar no Notebook (10-30 minutos)

### 3.1 Abrir Notebook

```powershell
jupyter notebook cadastro_dbgeo.ipynb
```

Ou abra no VS Code:
- File → Open Notebook
- Navegue até `cadastro_dbgeo.ipynb`

### 3.2 Carregar CSV com Lista de Processos

Célula de código:

```python
import pandas as pd

# Caminho até seu arquivo CSV
csv_path = r'C:\Users\larissa.valadao\OneDrive - IPHAN - Instituto do Patrimônio Histórico e Artístico Nacional\Documentos\arquivos_analise\lista_processos\ListaProcessos_SEIPro_20260812_15_00_57.csv'

# Carregar
df_dados = pd.read_csv(csv_path, sep=';')

# Ver primeiras linhas
print(f"Carregado: {len(df_dados)} processos")
print(df_dados[['Protocolo', 'Link_Permanente']].head())
```

Execute (Shift + Enter).

Se aparecer a lista de processos, tudo certo!

### 3.3 Executar Download com Scraper

Célula de código:

```python
from geo_functions import area_files_list

# Definir caminhos
in_dir = r'C:\OneDrive - IPHAN - Instituto do Patrimônio Histórico e Artístico Nacional\Documentos\arquivos_analise\entrada'
out_dir = r'C:\OneDrive - IPHAN - Instituto do Patrimônio Histórico e Artístico Nacional\Documentos\arquivos_analise\saida'

# Executar pipeline com download automático
area_files_list(
    in_dir=in_dir,
    out_dir=out_dir,
    download_df=df_dados,           # ← Dispara download automático!
    protocolo_col='Protocolo',
    keep_name=True
)
```

### 3.4 Fornecer Credenciais

Quando executar a célula acima, o notebook vai parar e mostrar:

```
  Usuário SEI: _
```

Digite seu usuário SEI e pressione Enter:

```
  Usuário SEI: seu_usuario
  Senha SEI: _
```

Digite sua senha (não será exibida) e pressione Enter.

### 3.5 Acompanhar Download

O notebook mostrará o progresso em tempo real:

```
======================================================================
DETECÇÃO: Links do SEI detectados
  → Iniciando scraping via navegador (Playwright)
======================================================================

  Acessando login do SEI...
  Login OK
  
[1/9] Processando: 01450.010421/2026-51 (ID: 8551676)
  Expandindo árvore...
  Árvore expandida
    ✓ Arquivo ADA encontrado: Arquivo_ADA.kml
  ✓ Salvo: C:\OneDrive - IPHAN\...\01450_010421_2026_51.kml

[2/9] Processando: 01450.010371/2026-10 (ID: 8549315)
  ...

SCRAPING SEI CONCLUÍDO: 9/9 processos
======================================================================
```

**Não feche nem interrompa enquanto está processando!**

### 3.6 Verificar Resultado

Após completar, você verá:

```
ETAPA 2: DESCOBERTA DE ARQUIVOS
  • Shapefiles: 0
  • KML: 9
  • KMZ: 0
  TOTAL: 9 arquivos para processar

ETAPA 3: PROCESSAMENTO (9 arquivos)
  Transformando geometrias...
  Calculando áreas...
  ...
```

E ao final:

```
RESULTADO FINAL
  Processados: 9/9 arquivos
  Shapefiles gerados: 9
  
Área total calculada: XXXX ha
```

Pronto! Os dados foram processados e salvos em `out_dir`.

---

## Passo 4: Verificar Arquivos Gerados

### 4.1 Abrir Pasta de Entrada

Navegue até a pasta que definiu em `in_dir`:

```
entrada/
├── 01450_010421_2026_51.kml
├── 01450_010371_2026_10.kml
├── 01450_010180_2026_40.kml
├── 01450_009914_2026_48.kml
├── ...
└── 01450_XXXXXXX_XXXX_XX.kml
```

Esses são os arquivos ADA baixados do SEI.

### 4.2 Abrir Pasta de Saída

Navegue até a pasta que definiu em `out_dir`:

```
saida/
├── 01450_010421_2026_51.shp
├── 01450_010421_2026_51.shx
├── 01450_010421_2026_51.dbf
├── 01450_010371_2026_10.shp
├── ...
└── resultado.csv
```

Esses são os shapefiles processados e o CSV com resultado.

### 4.3 Visualizar no QGIS (opcional)

1. Abra QGIS
2. File → Open
3. Selecione um arquivo `.shp` da pasta `saida/`
4. Clique Open

Você verá os polígonos da ADA mapeados!

---

## Passo 5: Próximas Etapas

### Se precisar processar novos lotes:

1. Prepare novo CSV com lista de processos
2. Repita do Passo 3.2 em diante
3. Cada execução sobrescreve `in_dir` (cuidado!)

### Se quiser usar apenas download (sem processamento):

```python
from download_ada_sei_scraper import baixar_ada_do_sei

df = pd.read_csv(csv_path, sep=';')

arquivos = baixar_ada_do_sei(
    df_dados=df,
    in_dir=in_dir,
    usuario='seu_usuario',
    senha='sua_senha'
)

print(f"Baixados: {len(arquivos)} arquivos")
```

---

## Troubleshooting Rápido

### Erro: "ModuleNotFoundError: No module named 'requests'"

```powershell
pip install requests
```

### Erro: "ModuleNotFoundError: No module named 'playwright'"

```powershell
pip install playwright
playwright install chromium
```

### Erro: "Falha no login"

- Verificar usuário/senha
- Tente acessar manualmente o SEI no navegador primeiro
- Verifique se tem VPN/proxy ativo

### Erro: "Timeout"

- Aumentar espera no download (tomar mais tempo)
- Verificar conexão de internet
- Tentar novamente (às vezes é problema temporário)

### Notebook fica "preso" esperando input

Se aparecer um `_` e não responde:

- Pressione Ctrl+C (interrompe)
- Tente novamente em nova célula
- Pode ser que precisa fornecer a entrada

---

## Checklist de Sucesso

Depois de completar este guia, você deve ter:

- [ ] Python 3.8+ instalado
- [ ] Dependências instaladas (`pip install -r requirements.txt`)
- [ ] Chromium instalado (`playwright install chromium`)
- [ ] Testes passando (`teste_scraper_sei.py`)
- [ ] CSV preparado com lista de processos
- [ ] Pastas de entrada/saída criadas
- [ ] Primeiro download realizado com sucesso
- [ ] Arquivos ADA em `in_dir`
- [ ] Shapefiles processados em `out_dir`

Se tiver todos os itens, **parabéns! Está funcionando!** 🎉

---

## Contato / Dúvidas

Se precisar de ajuda:

1. Verifique os logs da execução (console do notebook)
2. Leia `INSTRUCOES_SCRAPER_SEI.md` (documentação técnica)
3. Consulte `README_SCRAPER_SEI.md` (troubleshooting)
4. Teste novamente (às vezes conexão instável)

---

## Resumo do Fluxo

```
CSV de Processos
       ↓
   Download ADA
   (via SEI scraper)
       ↓
    Entrada/
   (9 arquivos KML)
       ↓
  Processamento
  (geometrias)
       ↓
   Saída/
  (9 Shapefiles)
   + resultado.csv
       ↓
   Visualização QGIS
   (mapeamento de dados)
```

Pronto! Você agora pode usar o scraper SEI para automatizar o download de arquivos ADA do processo IPHAN.
