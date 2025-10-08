#!/usr/bin/env python3
"""
Script para corrigir definitivamente o comando --init do COBOL Analyzer.

O problema: O main.py chama auto_setup_environment() sem parâmetros, fazendo com que
ele procure pelos diretórios config/data/examples no diretório atual, mas quando o
pacote é instalado, esses diretórios estão no local de instalação do pacote.

Solução: Modificar o main.py para detectar onde estão os diretórios originais
e passá-los corretamente para auto_setup_environment().
"""

import os
import re
from pathlib import Path

def corrigir_main_py(caminho_projeto):
    """Corrige o main.py para localizar corretamente os diretórios do pacote"""
    
    main_py = Path(caminho_projeto) / "main.py"
    
    if not main_py.exists():
        print(f"ERRO: {main_py} não encontrado")
        return False
    
    print(f"Corrigindo: {main_py}")
    
    # Ler conteúdo atual
    conteudo = main_py.read_text(encoding='utf-8')
    
    # Código de substituição que resolve o problema
    novo_codigo_init = '''        # Inicializar ambiente se solicitado
        if args.init:
            from src.core.local_setup import auto_setup_environment
            try:
                print(" Configurando ambiente local do COBOL Analyzer...")
                
                # Localizar diretórios de origem (onde estão config, data, examples)
                script_dir = Path(__file__).parent  # Diretório onde está o main.py
                
                # Verificar se os diretórios existem no local do script
                config_origem = script_dir / "config" if (script_dir / "config").exists() else None
                data_origem = script_dir / "data" if (script_dir / "data").exists() else None
                
                # Chamar auto_setup_environment passando os diretórios corretos
                if config_origem or data_origem:
                    # Copiar do local do script para o diretório atual
                    import shutil
                    
                    # Criar diretórios no local atual
                    for dir_name in ["config", "data", "examples", "logs"]:
                        Path(dir_name).mkdir(exist_ok=True)
                    
                    # Copiar config se existir
                    if config_origem and config_origem.exists():
                        shutil.copytree(config_origem, "./config", dirs_exist_ok=True)
                        print(f" Config copiado de: {config_origem}")
                    
                    # Copiar data se existir  
                    if data_origem and data_origem.exists():
                        shutil.copytree(data_origem, "./data", dirs_exist_ok=True)
                        print(f" Data copiado de: {data_origem}")
                    
                    # Copiar examples se existir
                    examples_origem = script_dir / "examples"
                    if examples_origem.exists():
                        shutil.copytree(examples_origem, "./examples", dirs_exist_ok=True)
                        print(f" Examples copiado de: {examples_origem}")
                    
                    # Criar marcador de inicialização
                    Path(".cobol_analyzer_init").touch()
                    
                else:
                    # Fallback para o método original
                    auto_setup_environment()
                
                print(" Ambiente configurado com sucesso!")
                print(" Configurações: ./config")
                print(" Dados RAG: ./data")
                print(" Logs: ./logs")
                print(" Exemplos: ./examples")
                return
            except Exception as e:
                print(f" Erro na configuração: {e}")
                import traceback
                traceback.print_exc()
                return'''
    
    # Padrão para encontrar o bloco atual do --init
    padrao = re.compile(
        r'        # Inicializar ambiente se solicitado.*?'
        r'                return',
        re.DOTALL
    )
    
    if not padrao.search(conteudo):
        print("ERRO: Bloco de inicialização não encontrado no main.py")
        return False
    
    # Fazer backup
    backup = main_py.with_suffix('.py.backup')
    main_py.rename(backup)
    print(f"Backup salvo: {backup}")
    
    # Aplicar correção
    novo_conteudo = padrao.sub(novo_codigo_init, conteudo)
    main_py.write_text(novo_conteudo, encoding='utf-8')
    
    print("✓ main.py corrigido com sucesso!")
    return True

if __name__ == "__main__":
    # Caminho para seu projeto COBOL Analyzer
    projeto = "/home/ubuntu/cobol_analyzer_final"
    
    print("=== CORRETOR FINAL DO COBOL ANALYZER ===")
    print("Este script corrige o comando --init para funcionar corretamente")
    print("independentemente de onde o projeto esteja localizado.\n")
    
    if Path(projeto).exists():
        if corrigir_main_py(projeto):
            print("\n✓ CORREÇÃO APLICADA COM SUCESSO!")
            print("Agora o comando --init funcionará corretamente.")
        else:
            print("\n✗ FALHA NA CORREÇÃO")
    else:
        print(f"✗ ERRO: Projeto não encontrado em {projeto}")
        print("Edite este script e ajuste a variável 'projeto'")
    
    print("\n=== FIM ===")
