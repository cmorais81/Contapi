import os
import shutil
import glob
from datetime import datetime

def main():
    print("RESOLVENDO PROBLEMA COBOL ANALYZER")
    print("=" * 40)
    
    if not os.path.exists("cobol_to_docs"):
        print("ERRO: Execute na pasta que contem cobol_to_docs/")
        return
    
    config_path = None
    data_path = None
    
    locais = ["build/lib/cobol_to_docs", "cobol_to_docs"]
    
    for local in locais:
        if os.path.exists(local):
            config_test = os.path.join(local, "config")
            data_test = os.path.join(local, "data")
            
            if os.path.exists(config_test) and not config_path:
                yamls = glob.glob(os.path.join(config_test, "*.yaml"))
                if yamls:
                    config_path = os.path.abspath(config_test)
                    print(f"Config encontrado: {config_test} ({len(yamls)} YAMLs)")
            
            if os.path.exists(data_test) and not data_path:
                data_path = os.path.abspath(data_test)
                print(f"Data encontrado: {data_test}")
    
    if not config_path:
        print("ERRO: Pasta config nao encontrada")
        return
    
    arquivo_principal = None
    for arquivo in ["cobol_to_docs/runner/main.py", "cobol_to_docs/runner/cli.py"]:
        if os.path.exists(arquivo):
            arquivo_principal = arquivo
            print(f"Arquivo principal: {arquivo}")
            break
    
    if not arquivo_principal:
        print("ERRO: Arquivo principal nao encontrado")
        return
    
    timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
    backup_dir = f"backup_{timestamp}"
    os.makedirs(backup_dir, exist_ok=True)
    print(f"Backup criado: {backup_dir}")
    
    shutil.copy2(arquivo_principal, os.path.join(backup_dir, os.path.basename(arquivo_principal)))
    
    with open(arquivo_principal, 'r') as f:
        conteudo = f.read()
    
    funcao_init = criar_funcao_init(config_path, data_path)
    
    if 'def main(' in conteudo:
        conteudo = conteudo.replace('def main(', funcao_init + '\n\ndef main(')
    else:
        conteudo += '\n' + funcao_init
    
    if '--init' not in conteudo and 'ArgumentParser' in conteudo:
        conteudo = adicionar_argparse(conteudo)
    
    if 'args.init' not in conteudo and 'parse_args' in conteudo:
        conteudo = adicionar_tratamento(conteudo)
    
    with open(arquivo_principal, 'w') as f:
        f.write(conteudo)
    
    print(f"Arquivo corrigido: {arquivo_principal}")
    print("Concluido!")
    print("\nTeste recomendado:")
    print("  mkdir teste_init && cd teste_init")
    print("  cobol-to-docs --init")
    print("  ls -la config/ data/")

def criar_funcao_init(config_path, data_path):
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
    
    data_origem = r"{data_path or ''}"
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

if __name__ == "__main__":
    main()
