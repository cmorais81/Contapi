#!/usr/bin/env python3
import os
import shutil
from datetime import datetime

def main():
    print("CORRIGINDO --init PARA USAR PACOTE INSTALADO")
    print("=" * 50)
    
    # Verificar se estamos no lugar certo
    if not os.path.exists("cobol_to_docs"):
        print("ERRO: Execute na pasta que contem cobol_to_docs/")
        return
    
    # Encontrar arquivo principal
    print("1. Procurando arquivo principal...")
    arquivo_main = encontrar_main()
    
    if not arquivo_main:
        print("ERRO: Arquivo main nao encontrado")
        return
    
    print(f"   Arquivo: {arquivo_main}")
    
    # Fazer backup
    print("2. Criando backup...")
    timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
    backup = f"{arquivo_main}.backup_{timestamp}"
    shutil.copy2(arquivo_main, backup)
    print(f"   Backup: {backup}")
    
    # Corrigir arquivo
    print("3. Corrigindo funcao para usar pacote instalado...")
    corrigir_arquivo(arquivo_main)
    
    print("CONCLUIDO!")
    print("\nTeste:")
    print("  mkdir teste && cd teste")
    print("  cobol-to-docs --init")

def encontrar_main():
    arquivos = [
        "cobol_to_docs/runner/main.py",
        "cobol_to_docs/runner/cli.py",
        "cobol_to_docs/main.py"
    ]
    
    for arquivo in arquivos:
        if os.path.exists(arquivo):
            return arquivo
    
    return None

def corrigir_arquivo(arquivo_main):
    # Ler arquivo
    with open(arquivo_main, 'r', encoding='utf-8') as f:
        conteudo = f.read()
    
    # Remover funcao antiga se existir
    import re
    conteudo = re.sub(
        r'def inicializar_ambiente.*?(?=\ndef|\nclass|\nif __name__|\Z)',
        '',
        conteudo,
        flags=re.DOTALL
    )
    
    # Criar nova funcao que usa pkg_resources
    nova_funcao = '''
def inicializar_ambiente(diretorio="."):
    import os
    import shutil
    import glob
    
    print(f"Inicializando ambiente em: {os.path.abspath(diretorio)}")
    
    # Criar diretorios
    for pasta in ["config", "data", "examples", "logs", "output", "input"]:
        os.makedirs(os.path.join(diretorio, pasta), exist_ok=True)
        print(f"Criado: {pasta}/")
    
    # Tentar encontrar arquivos do pacote instalado
    config_origem = None
    data_origem = None
    
    # Metodo 1: Usar importlib para encontrar o pacote
    try:
        import cobol_to_docs
        pacote_path = os.path.dirname(cobol_to_docs.__file__)
        
        config_test = os.path.join(pacote_path, "config")
        if os.path.exists(config_test):
            config_origem = config_test
        
        data_test = os.path.join(pacote_path, "data")
        if os.path.exists(data_test):
            data_origem = data_test
            
    except ImportError:
        pass
    
    # Metodo 2: Procurar em locais conhecidos se nao encontrou
    if not config_origem:
        locais = [
            "build/lib/cobol_to_docs/config",
            "cobol_to_docs/config",
            "../cobol_to_docs/config"
        ]
        
        for local in locais:
            if os.path.exists(local):
                yamls = glob.glob(os.path.join(local, "*.yaml"))
                if yamls:
                    config_origem = os.path.abspath(local)
                    break
    
    if not data_origem:
        locais = [
            "build/lib/cobol_to_docs/data",
            "cobol_to_docs/data",
            "../cobol_to_docs/data"
        ]
        
        for local in locais:
            if os.path.exists(local):
                data_origem = os.path.abspath(local)
                break
    
    # Copiar config
    if config_origem and os.path.exists(config_origem):
        print(f"Copiando configuracoes de: {config_origem}")
        config_dest = os.path.join(diretorio, "config")
        
        for yaml_file in glob.glob(os.path.join(config_origem, "*.yaml")):
            nome = os.path.basename(yaml_file)
            shutil.copy2(yaml_file, os.path.join(config_dest, nome))
            print(f"  {nome}")
        
        for yml_file in glob.glob(os.path.join(config_origem, "*.yml")):
            nome = os.path.basename(yml_file)
            shutil.copy2(yml_file, os.path.join(config_dest, nome))
            print(f"  {nome}")
    else:
        print("AVISO: Arquivos de configuracao nao encontrados")
    
    # Copiar data
    if data_origem and os.path.exists(data_origem):
        print(f"Copiando dados de: {data_origem}")
        data_dest = os.path.join(diretorio, "data")
        
        for item in os.listdir(data_origem):
            origem = os.path.join(data_origem, item)
            destino = os.path.join(data_dest, item)
            
            if os.path.isfile(origem):
                shutil.copy2(origem, destino)
                print(f"  {item}")
            elif os.path.isdir(origem):
                if os.path.exists(destino):
                    shutil.rmtree(destino)
                shutil.copytree(origem, destino)
                print(f"  {item}/")
    else:
        print("AVISO: Arquivos de dados nao encontrados")
    
    # Contar arquivos copiados
    config_count = len(glob.glob(os.path.join(diretorio, "config", "*.yaml")))
    config_count += len(glob.glob(os.path.join(diretorio, "config", "*.yml")))
    
    data_items = 0
    data_dir = os.path.join(diretorio, "data")
    if os.path.exists(data_dir):
        data_items = len(os.listdir(data_dir))
    
    print(f"Ambiente inicializado! ({config_count} configs, {data_items} dados)")
    return True
'''
    
    # Adicionar funcao
    if 'def main(' in conteudo:
        conteudo = conteudo.replace('def main(', nova_funcao + '\ndef main(')
    else:
        conteudo += nova_funcao
    
    # Adicionar argparse se necessario
    if '--init' not in conteudo and 'ArgumentParser' in conteudo:
        linhas = conteudo.split('\n')
        for i, linha in enumerate(linhas):
            if 'add_argument' in linha and '--' in linha:
                linhas.insert(i + 1, '    parser.add_argument("--init", action="store_true", help="Inicializar ambiente")')
                break
        conteudo = '\n'.join(linhas)
    
    # Adicionar tratamento se necessario
    if 'args.init' not in conteudo and 'parse_args' in conteudo:
        linhas = conteudo.split('\n')
        for i, linha in enumerate(linhas):
            if 'parse_args' in linha:
                linhas.insert(i + 2, '    if hasattr(args, "init") and args.init:')
                linhas.insert(i + 3, '        inicializar_ambiente()')
                linhas.insert(i + 4, '        return')
                break
        conteudo = '\n'.join(linhas)
    
    # Salvar arquivo
    with open(arquivo_main, 'w', encoding='utf-8') as f:
        f.write(conteudo)
    
    print("   Funcao corrigida para usar pacote instalado")

if __name__ == "__main__":
    main()
