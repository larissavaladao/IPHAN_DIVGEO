# 🔍 GUIA DE DEBUG - SCRAPER SEI TRAVADO

## Problema
O scraper parece iniciar mas depois não retorna saída e o notebook fica travado.

## Possíveis Causas e Soluções

### 1. **Navegador Chromium não consegue aparecer**
Se `headless=True`, o navegador roda em background sem interface.

**Solução:**
1. Modifique a célula do notebook para usar `headless=False`:
```python
from geo_functions import area_files_list

area_files_list(
    in_dir=in_dir,
    out_dir=out_dir,
    download_df=df_dados,
    protocolo_col='Protocolo',
    link_col='Link_Permanente',
    keep_name=True,
    headless=False  # ← Adicione isto
)
```

Isso abrirá uma janela do navegador onde você pode ver o que está acontecendo.

---

### 2. **Problema de Credenciais**
O notebook pode não estar capturando a entrada de senha corretamente.

**Diagnóstico:**
- Verifique se a célula fica aguardando input (você vê o campo "Usuário SEI:" mas não consegue digitar)

**Solução:**
Execute o script de debug manualmente no terminal:
```bash
cd "C:\Users\larissa.valadao\Documents\GitHub\IPHAN_DIVGEO\1.Calcular_areas"
python debug_scraper_manual.py
```

Este script:
- Testa credenciais de forma mais robusta
- Mostra mensagens de erro detalhadas
- Abre o navegador visualmente (não headless)

---

### 3. **Timeout no Login**
O SEI pode estar demorando a carregar ou a estrutura HTML mudou.

**Diagnóstico:**
- Execute com `headless=False` para ver se o navegador está abrindo
- Verifique se consegue fazer login manualmente em https://sei-sip.iphan.gov.br

**Solução:**
Aumente os timeouts editando `download_ada_sei_scraper.py`, linha ~45:
```python
TIMEOUT_NAV = 120000  # Aumentar de 60000 para 120000 (ms)
TIMEOUT_DOWNLOAD = 240000  # Aumentar de 120000 para 240000 (ms)
```

---

### 4. **Problema com Nested Asyncio (Jupyter)**
Embora tenhamos instalado `nest_asyncio`, pode haver conflito.

**Diagnóstico:**
- Reinicie o kernel do Jupyter
- Limpe variáveis: `%reset -f`
- Execute novamente

**Solução:**
```python
# No início da célula, reinicie o environment:
import sys
if 'jupyter' in sys.modules:
    # Limpar qualquer event loop anterior
    import asyncio
    try:
        loop = asyncio.get_event_loop()
        if loop.is_running():
            loop.close()
    except:
        pass
```

---

## Passos de Debug Recomendados (em ordem)

1. **Execute o teste rápido:**
   ```bash
   python teste_scraper_sei.py
   ```
   Confirme que todos os 5 testes passam.

2. **Execute o debug manual:**
   ```bash
   python debug_scraper_manual.py
   ```
   Forneça suas credenciais reais. Isso testará o scraper fora do notebook e mostrará exatamente onde falha.

3. **Se funcionar no debug manual:**
   - Volte ao notebook
   - Aumente timeouts em `download_ada_sei_scraper.py`
   - Use `headless=False` para ver o navegador
   - Execute novamente

4. **Se travar no debug manual:**
   - Verifique credenciais (especialmente senha com caracteres especiais)
   - Tente fazer login manualmente em https://sei-sip.iphan.gov.br
   - Verifique se há 2FA (autenticação de dois fatores) ativada
   - Procure por limitações de IP ou bloqueios da conta

---

## Informações para Incluir em Relatório de Erro

Se nenhum dos passos acima funcionar, reúna estas informações:

```python
# No notebook, execute:
import platform
import sys
print(f"Python: {sys.version}")
print(f"SO: {platform.system()} {platform.release()}")

from playwright.async_api import __version__ as pw_version
print(f"Playwright: {pw_version}")

import pandas as pd
print(f"Pandas: {pd.__version__}")
```

E:
- Última mensagem que apareceu no notebook
- Tempo que ficou travado (segundos/minutos)
- Se o navegador abriu ou não
- Se consegue fazer login manualmente no SEI

---

## Contacto para Suporte

Com essas informações, será possível diagnosticar o problema com precisão.
