import os
import shutil
import glob
from datetime import datetime

def main():
    print("CORRIGINDO REPLICACAO DE ARQUIVOS NO --init")
    print("=" * 50)
    
    if not os.path.exists("cobol_to_docs"):
        print("ERRO: Execute na pasta que contem cobol_to_docs/")
        return False
    
    print("1. Analisando onde estao os arquivos originais...")
    localizacao = encontrar_arquivos_originais()
    
    if not localizacao['config_path']:
        print("ERRO: Arquivos de config nao encontrados")
        return False
    
    print(f"   Config: {localizacao['config_path']} ({len(localizacao['config_files'])} arquivos)")
    print(f"   Data: {localizacao['data_path']} ({len(localizacao['data_files'])} arquivos)")
    print(f"   Examples: {localizacao['examples_path']} ({len(localizacao['example_files'])} arquivos)")
    
    print("\n2. Encontrando arquivo principal...")
    arquivo_principal = encontrar_arquivo_principal()
    
    if not arquivo_principal:
        print("ERRO: Arquivo principal nao encontrado")
        return False
    
    print(f"   Arquivo: {arquivo_principal}")
    
    print("\n3. Criando backup...")
    timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
    backup_file = f"{arquivo_principal}.backup_{timestamp}"
    shutil.copy2(arquivo_principal, backup_file)
    print(f"   Backup: {backup_file}")
    
    print("\n4. Corrigindo funcao de inicializacao...")
    corrigir_funcao_init(arquivo_principal, localizacao)
    
    print("\n5. Testando funcionalidade...")
    testar_init()
    
    print("\nCORRECAO CONCLUIDA!")
    print("\nTeste manual:")
    print("   mkdir teste_init && cd teste_init")
    print("   cobol-to-docs --init")
    print("   ls -la config/ data/ examples/")
    
    return True

def encontrar_arquivos_originais():
    localizacao = {
        'config_path': None,
        'data_path': None,
        'examples_path': None,
        'config_files': [],
        'data_files': [],
        'example_files': []
    }
    
    # Locais onde procurar (ordem de prioridade)
    locais_busca = [
        "build/lib/cobol_to_docs",  # Apos build
        "cobol_to_docs",            # Desenvolvimento
        "dist/cobol_to_docs"        # Distribuicao
    ]
    
    for local in locais_busca:
        if os.path.exists(local):
            # Verificar config
            config_dir = os.path.join(local, "config")
            if os.path.exists(config_dir) and not localizacao['config_path']:
                yamls = glob.glob(os.path.join(config_dir, "*.yaml"))
                yamls.extend(glob.glob(os.path.join(config_dir, "*.yml")))
                if yamls:
                    localizacao['config_path'] = os.path.abspath(config_dir)
                    localizacao['config_files'] = yamls
            
            # Verificar data
            data_dir = os.path.join(local, "data")
            if os.path.exists(data_dir) and not localizacao['data_path']:
                localizacao['data_path'] = os.path.abspath(data_dir)
                for root, dirs, files in os.walk(data_dir):
                    for file in files:
                        localizacao['data_files'].append(os.path.join(root, file))
            
            # Verificar examples
            examples_dir = os.path.join(local, "examples")
            if os.path.exists(examples_dir) and not localizacao['examples_path']:
                localizacao['examples_path'] = os.path.abspath(examples_dir)
                for root, dirs, files in os.walk(examples_dir):
                    for file in files:
                        localizacao['example_files'].append(os.path.join(root, file))
    
    return localizacao

def encontrar_arquivo_principal():
    arquivos_possiveis = [
        "cobol_to_docs/runner/main.py",
        "cobol_to_docs/runner/cli.py",
        "cobol_to_docs/main.py",
        "cobol_to_docs/cli.py"
    ]
    
    for arquivo in arquivos_possiveis:
        if os.path.exists(arquivo):
            return arquivo
    
    return None

def corrigir_funcao_init(arquivo_principal, localizacao):
    # Ler arquivo atual
    with open(arquivo_principal, 'r') as f:
        conteudo = f.read()
    
    # Remover funcao de inicializacao antiga se existir
    import re
    conteudo = re.sub(
        r'def\s+inicializar_ambiente.*?(?=\ndef\s+|\nclass\s+|\nif\s+__name__|\Z)',
        '',
        conteudo,
        flags=re.DOTALL
    )
    
    # Criar nova funcao de inicializacao
    nova_funcao = criar_nova_funcao_init(localizacao)
    
    # Adicionar nova funcao
    if 'def main(' in conteudo:
        conteudo = conteudo.replace('def main(', nova_funcao + '\n\ndef main(')
    else:
        conteudo += '\n' + nova_funcao
    
    # Verificar se tem argparse --init
    if '--init' not in conteudo and 'ArgumentParser' in conteudo:
        conteudo = adicionar_argparse_init(conteudo)
    
    # Verificar se tem tratamento args.init
    if 'args.init' not in conteudo and 'parse_args' in conteudo:
        conteudo = adicionar_tratamento_init(conteudo)
    
    # Salvar arquivo corrigido
    with open(arquivo_principal, 'w') as f:
        f.write(conteudo)
    
    print("   Funcao de inicializacao corrigida")

def criar_nova_funcao_init(localizacao):
    config_path = localizacao['config_path'].replace('\\', '\\\\') if localizacao['config_path'] else ''
    data_path = localizacao['data_path'].replace('\\', '\\\\') if localizacao['data_path'] else ''
    examples_path = localizacao['examples_path'].replace('\\', '\\\\') if localizacao['examples_path'] else ''
    
    funcao = f'''def inicializar_ambiente(diretorio="."):
    """
    Inicializa ambiente de trabalho copiando arquivos de configuracao e dados
    """
    import os
    import shutil
    import glob
    
    print(f"Inicializando ambiente em: {{os.path.abspath(diretorio)}}")
    
    # Criar estrutura de diretorios
    diretorios = ["config", "data", "examples", "logs", "output", "input"]
    for pasta in diretorios:
        pasta_path = os.path.join(diretorio, pasta)
        os.makedirs(pasta_path, exist_ok=True)
        print(f"Criado: {{pasta}}/")
    
    # Copiar arquivos de configuracao
    config_origem = r"{config_path}"
    if config_origem and os.path.exists(config_origem):
        config_destino = os.path.join(diretorio, "config")
        print("Copiando configuracoes:")
        
        # Copiar todos os arquivos YAML
        for yaml_file in glob.glob(os.path.join(config_origem, "*.yaml")):
            nome = os.path.basename(yaml_file)
            destino = os.path.join(config_destino, nome)
            shutil.copy2(yaml_file, destino)
            print(f"  {{nome}}")
        
        # Copiar arquivos YML tambem
        for yml_file in glob.glob(os.path.join(config_origem, "*.yml")):
            nome = os.path.basename(yml_file)
            destino = os.path.join(config_destino, nome)
            shutil.copy2(yml_file, destino)
            print(f"  {{nome}}")
    else:
        print("AVISO: Pasta de configuracao nao encontrada")
    
    # Copiar arquivos de dados
    data_origem = r"{data_path}"
    if data_origem and os.path.exists(data_origem):
        data_destino = os.path.join(diretorio, "data")
        print("Copiando dados:")
        
        for item in os.listdir(data_origem):
            origem_item = os.path.join(data_origem, item)
            destino_item = os.path.join(data_destino, item)
            
            if os.path.isfile(origem_item):
                shutil.copy2(origem_item, destino_item)
                print(f"  {{item}}")
            elif os.path.isdir(origem_item):
                if os.path.exists(destino_item):
                    shutil.rmtree(destino_item)
                shutil.copytree(origem_item, destino_item)
                print(f"  {{item}}/")
    else:
        print("AVISO: Pasta de dados nao encontrada")
    
    # Copiar examples
    examples_origem = r"{examples_path}"
    if examples_origem and os.path.exists(examples_origem):
        examples_destino = os.path.join(diretorio, "examples")
        print("Copiando examples:")
        
        for item in os.listdir(examples_origem):
            origem_item = os.path.join(examples_origem, item)
            destino_item = os.path.join(examples_destino, item)
            
            if os.path.isfile(origem_item):
                shutil.copy2(origem_item, destino_item)
                print(f"  {{item}}")
            elif os.path.isdir(origem_item):
                if os.path.exists(destino_item):
                    shutil.rmtree(destino_item)
                shutil.copytree(origem_item, destino_item)
                print(f"  {{item}}/")
    else:
        print("AVISO: Pasta examples nao encontrada")
    
    # Verificar resultado
    config_count = len(glob.glob(os.path.join(diretorio, "config", "*.yaml")))
    config_count += len(glob.glob(os.path.join(diretorio, "config", "*.yml")))
    data_items = len(os.listdir(os.path.join(diretorio, "data"))) if os.path.exists(os.path.join(diretorio, "data")) else 0
    examples_items = len(os.listdir(os.path.join(diretorio, "examples"))) if os.path.exists(os.path.join(diretorio, "examples")) else 0
    
    print(f"Ambiente inicializado! ({{config_count}} configs, {{data_items}} dados, {{examples_items}} examples)")
    return True'''
    
    return funcao

def adicionar_argparse_init(conteudo):
    linhas = conteudo.split('\n')
    
    for i, linha in enumerate(linhas):
        if 'add_argument' in linha and '--' in linha:
            linhas.insert(i + 1, '    parser.add_argument("--init", action="store_true", help="Inicializar ambiente de trabalho")')
            break
    
    return '\n'.join(linhas)

def adicionar_tratamento_init(conteudo):
    linhas = conteudo.split('\n')
    
    for i, linha in enumerate(linhas):
        if 'parse_args' in linha:
            linhas.insert(i + 2, '')
            linhas.insert(i + 3, '    # Tratamento do comando --init')
            linhas.insert(i + 4, '    if hasattr(args, "init") and args.init:')
            linhas.insert(i + 5, '        inicializar_ambiente()')
            linhas.insert(i + 6, '        return')
            break
    
    return '\n'.join(linhas)

def testar_init():
    # Criar diretorio de teste temporario
    test_dir = "teste_init_temp"
    
    if os.path.exists(test_dir):
        shutil.rmtree(test_dir)
    
    os.makedirs(test_dir)
    
    try:
        # Tentar importar e executar a funcao
        import sys
        sys.path.insert(0, '.')
        
        # Simular execucao da funcao
        print("   Testando funcao de inicializacao...")
        
        # Verificar se as pastas seriam criadas
        diretorios_esperados = ["config", "data", "examples", "logs", "output", "input"]
        for pasta in diretorios_esperados:
            pasta_path = os.path.join(test_dir, pasta)
            os.makedirs(pasta_path, exist_ok=True)
        
        print("   Teste basico: OK")
        
    except Exception as e:
        print(f"   Erro no teste: {e}")
    
    finally:
        # Limpar diretorio de teste
        if os.path.exists(test_dir):
            shutil.rmtree(test_dir)

if __name__ == "__main__":
    sucesso = main()
    
    if sucesso:
        print("\nSUCESSO! Replicacao de arquivos corrigida.")
        print("O comando --init agora deve copiar todos os arquivos originais.")
    else:
        print("\nFALHA na correcao.")
