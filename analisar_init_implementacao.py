#!/usr/bin/env python3
import os
import re
import glob

def main():
    print("ANALISANDO IMPLEMENTACAO DO COMANDO --init")
    print("=" * 50)
    
    if not os.path.exists("cobol_to_docs"):
        print("ERRO: Execute na pasta que contem cobol_to_docs/")
        return
    
    print("1. Procurando arquivos Python...")
    arquivos_py = encontrar_arquivos_python()
    print(f"   Encontrados {len(arquivos_py)} arquivos Python")
    
    print("\n2. Procurando implementacao do --init...")
    implementacoes = analisar_init(arquivos_py)
    
    if not implementacoes:
        print("   NENHUMA implementacao encontrada!")
        return
    
    print(f"   Encontradas {len(implementacoes)} implementacoes")
    
    print("\n3. DETALHES DAS IMPLEMENTACOES:")
    for i, impl in enumerate(implementacoes, 1):
        print(f"\n   === IMPLEMENTACAO {i} ===")
        print(f"   Arquivo: {impl['arquivo']}")
        print(f"   Linha: {impl['linha']}")
        print(f"   Tipo: {impl['tipo']}")
        print(f"   Codigo:")
        for linha in impl['codigo']:
            print(f"      {linha}")
    
    print("\n4. PROCURANDO FUNCOES DE INICIALIZACAO...")
    funcoes_init = procurar_funcoes_inicializacao(arquivos_py)
    
    if funcoes_init:
        print(f"   Encontradas {len(funcoes_init)} funcoes")
        for func in funcoes_init:
            print(f"\n   === FUNCAO ===")
            print(f"   Arquivo: {func['arquivo']}")
            print(f"   Nome: {func['nome']}")
            print(f"   Linha: {func['linha']}")
            print(f"   Busca arquivos em:")
            for caminho in func['caminhos']:
                print(f"      {caminho}")
    else:
        print("   Nenhuma funcao de inicializacao encontrada")
    
    print("\n5. RECOMENDACOES:")
    if implementacoes:
        for impl in implementacoes:
            print(f"   - Verifique o arquivo: {impl['arquivo']}")
            print(f"     Na linha {impl['linha']}, o comando --init chama alguma funcao")
    
    if funcoes_init:
        for func in funcoes_init:
            print(f"   - A funcao {func['nome']} em {func['arquivo']}")
            print(f"     Esta procurando arquivos nos caminhos listados acima")
            print(f"     ALTERE ESTA FUNCAO para procurar no local correto")

def encontrar_arquivos_python():
    arquivos = []
    
    # Procurar em cobol_to_docs
    for root, dirs, files in os.walk("cobol_to_docs"):
        for file in files:
            if file.endswith(".py"):
                arquivos.append(os.path.join(root, file))
    
    # Adicionar arquivos na raiz se existirem
    for arquivo in ["main.py", "cli.py", "setup.py"]:
        if os.path.exists(arquivo):
            arquivos.append(arquivo)
    
    return arquivos

def analisar_init(arquivos_py):
    implementacoes = []
    
    for arquivo in arquivos_py:
        try:
            with open(arquivo, 'r', encoding='utf-8') as f:
                linhas = f.readlines()
            
            for i, linha in enumerate(linhas, 1):
                linha_clean = linha.strip()
                
                # Procurar por --init em argumentos
                if '--init' in linha_clean and 'add_argument' in linha_clean:
                    implementacoes.append({
                        'arquivo': arquivo,
                        'linha': i,
                        'tipo': 'argparse_definition',
                        'codigo': [linha_clean]
                    })
                
                # Procurar por tratamento de args.init
                if 'args.init' in linha_clean or 'args["init"]' in linha_clean:
                    codigo = [linha_clean]
                    # Pegar algumas linhas seguintes para contexto
                    for j in range(1, 5):
                        if i + j - 1 < len(linhas):
                            codigo.append(linhas[i + j - 1].strip())
                    
                    implementacoes.append({
                        'arquivo': arquivo,
                        'linha': i,
                        'tipo': 'args_handling',
                        'codigo': codigo
                    })
        
        except Exception as e:
            print(f"   Erro ao ler {arquivo}: {e}")
    
    return implementacoes

def procurar_funcoes_inicializacao(arquivos_py):
    funcoes = []
    
    for arquivo in arquivos_py:
        try:
            with open(arquivo, 'r', encoding='utf-8') as f:
                conteudo = f.read()
                linhas = conteudo.split('\n')
            
            # Procurar por funcoes que podem ser de inicializacao
            patterns = [
                r'def\s+(inicializar|init|setup|configure).*\(',
                r'def\s+.*init.*\(',
                r'def\s+.*setup.*\(',
                r'def\s+.*ambiente.*\('
            ]
            
            for pattern in patterns:
                matches = re.finditer(pattern, conteudo, re.IGNORECASE)
                for match in matches:
                    # Encontrar numero da linha
                    linha_num = conteudo[:match.start()].count('\n') + 1
                    
                    # Extrair nome da funcao
                    nome_match = re.search(r'def\s+(\w+)', match.group())
                    nome_funcao = nome_match.group(1) if nome_match else "desconhecida"
                    
                    # Procurar caminhos na funcao
                    caminhos = extrair_caminhos_funcao(conteudo, match.start())
                    
                    funcoes.append({
                        'arquivo': arquivo,
                        'nome': nome_funcao,
                        'linha': linha_num,
                        'caminhos': caminhos
                    })
        
        except Exception as e:
            print(f"   Erro ao analisar {arquivo}: {e}")
    
    return funcoes

def extrair_caminhos_funcao(conteudo, inicio_funcao):
    caminhos = []
    
    # Encontrar o fim da funcao (proxima def ou fim do arquivo)
    resto_conteudo = conteudo[inicio_funcao:]
    fim_funcao = len(resto_conteudo)
    
    next_def = resto_conteudo.find('\ndef ', 1)
    if next_def != -1:
        fim_funcao = next_def
    
    funcao_conteudo = resto_conteudo[:fim_funcao]
    
    # Procurar por caminhos de arquivos
    patterns = [
        r'["\']([^"\']*(?:config|data|examples)[^"\']*)["\']',
        r'os\.path\.join\([^)]*["\']([^"\']*)["\'][^)]*\)',
        r'glob\.glob\([^)]*["\']([^"\']*)["\'][^)]*\)'
    ]
    
    for pattern in patterns:
        matches = re.findall(pattern, funcao_conteudo)
        for match in matches:
            if match and ('config' in match or 'data' in match or 'examples' in match):
                caminhos.append(match)
    
    return list(set(caminhos))  # Remover duplicatas

if __name__ == "__main__":
    main()
