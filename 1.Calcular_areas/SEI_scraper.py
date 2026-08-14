#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
debug_scraper_manual.py
=======================
Script de debug para testar o scraper SEI manualmente sem notebook.

Uso:
    python debug_scraper_manual.py
"""

import os
import sys
import pandas as pd
from pathlib import Path
from download_ada_sei_scraper import baixar_ada_do_sei
import glob

# Configurações de teste
IN_DIR = Path(__file__).parent / "downloads_teste"
IN_DIR.mkdir(exist_ok=True)

def main():
    """Testa scraper com um único processo."""
    print("\n" + "=" * 70)
    print("DEBUG SCRAPER SEI - TESTE MANUAL")
    print("=" * 70 + "\n")
    
    # Criar DataFrame de teste com um processo
    # df_teste = pd.read_csv(glob.glob(r"C:\Users\larissa.valadao\OneDrive - IPHAN - Instituto do Patrimônio Histórico e Artístico Nacional\Documentos\arquivos_analise\lista_processos\*.csv")[0],sep=";")

    df_teste = pd.DataFrame({
        'Protocolo': ['01450.010421/2026-51'],
        'ID': [123456],
        'Link_Permanente': ['https://sei.iphan.gov.br/sei/controlador.php?acao=procedimento_trabalhar&acao_origem=procedimento_visualizar&id_procedure=123456&infra_sistema=100000100&infra_unidade_atual=110000378&infra_hash=f3e1234567890abc']
    })
    
    print("TESTE 1: Validação de DataFrame")
    print("-" * 70)
    print(f"Processo: {df_teste['Protocolo'].iloc[0]}")
    print(f"Link: {df_teste['Link_Permanente'].iloc[0][:60]}...")
    print(f"Diretório de saída: {IN_DIR}\n")
    
    # Solicitar credenciais
    print("TESTE 2: Entrada de Credenciais")
    print("-" * 70)
    usuario = input("Usuário SEI: ").strip()
    if not usuario:
        print("✗ Usuário não fornecido")
        return
    
    from getpass import getpass
    senha = getpass("Senha SEI: ")
    senha = input("Senha SEI: ").strip()
    if not senha:
        print("✗ Senha não fornecida")
        return
    
    # Executar scraper
    print("\nTESTE 3: Executando Scraper")
    print("-" * 70)
    
    try:
        arquivos = baixar_ada_do_sei(
            df_teste,
            str(IN_DIR),
            usuario=usuario,
            senha=senha,
            protocolo_col='Protocolo',
            id_col='ID',
            headless=False  # Mostrar o navegador para debug visual
        )
        
        print("\n" + "=" * 70)
        print("RESULTADO DO TESTE")
        print("=" * 70)
        if arquivos:
            print(f"✓ Sucesso! {len(arquivos)} arquivo(s) baixado(s):")
            for arq in arquivos:
                print(f"  - {arq}")
        else:
            print("✗ Nenhum arquivo foi baixado")
            
    except Exception as e:
        print("\n" + "=" * 70)
        print("ERRO DURANTE EXECUÇÃO")
        print("=" * 70)
        print(f"✗ {type(e).__name__}: {e}")
        import traceback
        traceback.print_exc()

if __name__ == "__main__":
    main()
