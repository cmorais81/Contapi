import os
import shutil
import glob
import re
from datetime import datetime

def main():
    print("RESTAURANDO COBOL ANALYZER - FUNCIONALIDADE COMPLETA")
    print("=" * 60)
    
    if not os.path.exists("cobol_to_docs"):
        print("ERRO: Execute na pasta raiz que contem cobol_to_docs/")
        return False
    
    timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
    backup_dir = f"backup_completo_{timestamp}"
    print(f"1. Criando backup: {backup_dir}")
    criar_backup(backup_dir)
    
    print("\n2. Analisando estrutura...")
    analise = analisar_estrutura()
    mostrar_analise(analise)
    
    print("\n3. Corrigindo problemas...")
    corrigir_setup_py(analise)
    corrigir_init_files()
    corrigir_arquivo_principal(analise)
    criar_manifest()
    
    print("\n4. Restauracao concluida!")
    print("\nProximos passos:")
    print("   rm -rf build/ dist/ *.egg-info")
    print("   pip uninstall cobol-to-docs -y")
    print("   pip install -e .")
    print("   cobol-to-docs --help")
    
    return True

def criar_backup(backup_dir):
    os.makedirs(backup_dir, exist_ok=True)
    
    arquivos = ["setup.py", "MANIFEST.in"]
    for arquivo in arquivos:
        if os.path.exists(arquivo):
            shutil.copy2(arquivo, backup_dir)
    
    if os.path.exists("cobol_to_docs/runner"):
        shutil.copytree("cobol_to_docs/runner", os.path.join(backup_dir, "runner"))

def analisar_estrutura():
    analise = {
        'config_path': None,
        'data_path': None,
        'arquivo_principal': None,
        'config_files': [],
        'data_files': []
    }
    
    # Procurar config e data
    locais = ["cobol_to_docs", "build/lib/cobol_to_docs"]
    
    for local in locais:
        if os.path.exists(local):
            config_dir = os.path.join(local, "config")
            if os.path.exists(config_dir) and not analise['config_path']:
                analise['config_path'] = os.path.abspath(config_dir)
                analise['config_files'] = glob.glob(os.path.join(config_dir, "*.yaml"))
            
            data_dir = os.path.join(local, "data")
            if os.path.exists(data_dir) and not analise['data_path']:
                analise['data_path'] = os.path.abspath(data_dir)
                for root, dirs, files in os.walk(data_dir):
                    for file in files:
                        analise['data_files'].append(os.path.join(root, file))
    
    # Procurar arquivo principal
    arquivos = ["cobol_to_docs/runner/main.py", "cobol_to_docs/runner/cli.py"]
    for arquivo in arquivos:
        if os.path.exists(arquivo):
            analise['arquivo_principal'] = arquivo
            break
    
    return analise

def mostrar_analise(analise):
    print(f"   Config: {len(analise['config_files'])} arquivos")
    print(f"   Data: {len(analise['data_files'])} arquivos")
    print(f"   Arquivo principal: {analise['arquivo_principal'] or 'NAO ENCONTRADO'}")

def corrigir_setup_py(analise):
    print("   Corrigindo setup.py...")
    
    setup_content = '''from setuptools import setup, find_packages

setup(
    name="cobol-to-docs",
    version="1.0.0",
    packages=find_packages(),
    include_package_data=True,
    package_data={
        "cobol_to_docs": [
            "config/*.yaml",
            "config/*.yml",
            "data/**/*",
            "examples/**/*",
        ],
    },
    entry_points={
        "console_scripts": [
            "cobol-to-docs=cobol_to_docs.runner.main:main",
            "cobol-analyzer=cobol_to_docs.runner.cli:main",
        ],
    },
    python_requires=">=3.7",
    install_requires=[
        "pyyaml",
        "markdown",
    ],
)
'''
    
    with open("setup.py", 'w') as f:
        f.write(setup_content)
    
    print("      Setup.py criado")

def corrigir_init_files():
    print("   Corrigindo __init__.py...")
    
    init_files = [
        "cobol_to_docs/__init__.py",
        "cobol_to_docs/runner/__init__.py"
    ]
    
    for init_file in init_files:
        if not os.path.exists(init_file):
            os.makedirs(os.path.dirname(init_file), exist_ok=True)
            with open(init_file, 'w') as f:
                f.write('"""COBOL to Docs package"""\n')
            print(f"      Criado: {init_file}")

def corrigir_arquivo_principal(analise):
    if not analise['arquivo_principal']:
        print("   AVISO: Arquivo principal nao encontrado")
        return
    
    print("   Corrigindo arquivo principal...")
    arquivo = analise['arquivo_principal']
    
    with open(arquivo, 'r') as f:
        conteudo = f.read()
    
    if 'def inicializar_ambiente' not in conteudo:
        funcao_init = criar_funcao_init(analise)
        if 'def main(' in conteudo:
            conteudo = conteudo.replace('def main(', funcao_init + '\n\ndef main(')
        else:
            conteudo += '\n' + funcao_init
    
    if '--init' not in conteudo and 'ArgumentParser' in conteudo:
        conteudo = adicionar_argparse(conteudo)
    
    if 'args.init' not in conteudo and 'parse_args' in conteudo:
        conteudo = adicionar_tratamento(conteudo)
    
    with open(arquivo, 'w') as f:
        f.write(conteudo)
    
    print(f"      Arquivo corrigido: {arquivo}")

def criar_funcao_init(analise):
    config_path = analise['config_path'] or ''
    data_path = analise['data_path'] or ''
    
    return f'''def inicializar_ambiente(diretorio="."):
    import os
    import shutil
    import glob
    
    print(f"Inicializando ambiente em: {{os.path.abspath(diretorio)}}")
    
    for pasta in ["config", "data", "examples", "logs", "output", "input"]:
        os.makedirs(os.path.join(diretorio, pasta), exist_ok=True)
        print(f"Criado: {{pasta}}/")
    
    config_origem = r"{config_path}"
    if config_origem and os.path.exists(config_origem):
        config_dest = os.path.join(diretorio, "config")
        print("Copiando configuracoes:")
        for yaml in glob.glob(os.path.join(config_origem, "*.yaml")):
            nome = os.path.basename(yaml)
            shutil.copy2(yaml, os.path.join(config_dest, nome))
            print(f"  {{nome}}")
    
    data_origem = r"{data_path}"
    if data_origem and os.path.exists(data_origem):
        data_dest = os.path.join(diretorio, "data")
        print("Copiando dados:")
        for item in os.listdir(data_origem):
            origem = os.path.join(data_origem, item)
            destino = os.path.join(data_dest, item)
            if os.path.isfile(origem):
                shutil.copy2(origem, destino)
                print(f"  {{item}}")
            elif os.path.isdir(origem):
                if os.path.exists(destino):
                    shutil.rmtree(destino)
                shutil.copytree(origem, destino)
                print(f"  {{item}}/")
    
    print("Ambiente inicializado com sucesso!")
    return True'''

def adicionar_argparse(conteudo):
    linhas = conteudo.split('\n')
    for i, linha in enumerate(linhas):
        if 'add_argument' in linha and '--' in linha:
            linhas.insert(i + 1, '    parser.add_argument("--init", action="store_true", help="Inicializar ambiente")')
            break
    return '\n'.join(linhas)

def adicionar_tratamento(conteudo):
    linhas = conteudo.split('\n')
    for i, linha in enumerate(linhas):
        if 'parse_args' in linha:
            linhas.insert(i + 2, '    if hasattr(args, "init") and args.init:')
            linhas.insert(i + 3, '        inicializar_ambiente()')
            linhas.insert(i + 4, '        return')
            break
    return '\n'.join(linhas)

def criar_manifest():
    print("   Criando MANIFEST.in...")
    
    manifest_content = """# MANIFEST.in
recursive-include cobol_to_docs/config *.yaml
recursive-include cobol_to_docs/config *.yml
recursive-include cobol_to_docs/data *
recursive-include cobol_to_docs/examples *
include README.md
global-exclude *.pyc
global-exclude __pycache__
"""
    
    with open("MANIFEST.in", 'w') as f:
        f.write(manifest_content)
    
    print("      MANIFEST.in criado")

if __name__ == "__main__":
    sucesso = main()
    
    if sucesso:
        print("\nRESTAURACAO CONCLUIDA COM SUCESSO!")
        print("Seu COBOL Analyzer deve estar funcionando completamente agora.")
    else:
        print("\nFALHA NA RESTAURACAO")
