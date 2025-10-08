#!/usr/bin/env python3
"""
Script para corrigir o comando --init do COBOL Analyzer da forma CORRETA.

O problema: main.py chama auto_setup_environment() sem parâmetros
A solução: Passar os caminhos corretos dos diretórios como parâmetros

Simples e direto, como deveria ser.
"""

import os
import re
from pathlib import Path

def corrigir_main_py(caminho_projeto):
    """Corrige o main.py para passar os parâmetros corretos para auto_setup_environment"""
    
    main_py = Path(caminho_projeto) / "main.py"
    
    if not main_py.exists():
        print(f"ERRO: {main_py} não encontrado")
        return False
    
    print(f"Corrigindo: {main_py}")
    
    # Ler conteúdo atual
    conteudo = main_py.read_text(encoding='utf-8')
    
    # Encontrar a linha que chama auto_setup_environment()
    # Substituir por uma chamada com os parâmetros corretos
    padrao_antigo = r'(\s+)auto_setup_environment\(\)'
    
    # Novo código que detecta os diretórios e passa como parâmetros
    codigo_novo = r'''\1# Detectar onde estão os diretórios originais
\1script_dir = Path(__file__).parent
\1config_source = str(script_dir / "config") if (script_dir / "config").exists() else None
\1data_source = str(script_dir / "data") if (script_dir / "data").exists() else None
\1
\1# Chamar auto_setup_environment com os parâmetros corretos
\1auto_setup_environment(
\1    config_dir=config_source,
\1    data_dir=data_source,
\1    logs_dir=None  # logs sempre no diretório atual
\1)'''
    
    # Verificar se encontrou o padrão
    if not re.search(padrao_antigo, conteudo):
        print("ERRO: Não encontrei a chamada auto_setup_environment() no main.py")
        return False
    
    # Fazer backup
    backup = main_py.with_suffix('.py.backup')
    if backup.exists():
        backup.unlink()  # Remove backup anterior se existir
    main_py.rename(backup)
    print(f"Backup salvo: {backup}")
    
    # Aplicar correção
    novo_conteudo = re.sub(padrao_antigo, codigo_novo, conteudo)
    main_py.write_text(novo_conteudo, encoding='utf-8')
    
    print("✓ main.py corrigido!")
    print("Agora auto_setup_environment() recebe os parâmetros corretos.")
    return True

if __name__ == "__main__":
    # Caminho para seu projeto COBOL Analyzer
    projeto = "/home/ubuntu/cobol_analyzer_final"
    
    print("=== CORRETOR SIMPLES E CORRETO ===")
    print("Corrige o main.py para passar os parâmetros corretos")
    print("para auto_setup_environment()\n")
    
    if Path(projeto).exists():
        if corrigir_main_py(projeto):
            print("\n✓ CORREÇÃO APLICADA!")
            print("O --init agora funcionará corretamente.")
        else:
            print("\n✗ FALHA NA CORREÇÃO")
    else:
        print(f"✗ ERRO: Projeto não encontrado em {projeto}")
        print("Edite este script e ajuste a variável 'projeto'")
    
    print("\n=== FIM ===")
