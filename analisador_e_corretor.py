#!/usr/bin/env python3
"""
Analisador e Corretor de Localização de Arquivos
Vasculha a aplicação, identifica problemas e aplica correções automaticamente
"""

import os
import sys
import re
import shutil
import glob
from pathlib import Path
from typing import List, Dict, Any, Optional
from datetime import datetime

def main():
    print("ANALISADOR E CORRETOR DE LOCALIZACAO DE ARQUIVOS")
    print("Vasculhando aplicação e aplicando correções automaticamente")
    print("=" * 65)
    
    if not os.path.exists("cobol_to_docs"):
        print("ERRO: Pasta cobol_to_docs não encontrada!")
        return
    
    # 1. Mapear estrutura atual
    print("\nMAPEANDO ESTRUTURA ATUAL...")
    estrutura_atual = mapear_estrutura_completa()
    
    # 2. Analisar arquivos Python relevantes
    print("\nANALISANDO ARQUIVOS PYTHON...")
    arquivos_relevantes = encontrar_arquivos_relevantes()
    
    problemas_encontrados = []
    
    for arquivo in arquivos_relevantes:
        print(f"Analisando: {arquivo}")
        problemas_arquivo = analisar_arquivo_python(arquivo, estrutura_atual)
        if problemas_arquivo:
            problemas_encontrados.extend(problemas_arquivo)
    
    # 3. Análise específica do local_setup.py
    local_setup_path = "cobol_to_docs/local_setup.py"
    if os.path.exists(local_setup_path):
        print(f"\nANALISE ESPECIFICA: {local_setup_path}")
        problemas_setup = analisar_local_setup(local_setup_path, estrutura_atual)
        problemas_encontrados.extend(problemas_setup)
    else:
        print(f"AVISO: {local_setup_path} não encontrado")
    
    # 4. Mostrar problemas encontrados
    print("\n" + "=" * 65)
    print("PROBLEMAS ENCONTRADOS")
    print("=" * 65)
    
    if problemas_encontrados:
        for i, problema in enumerate(problemas_encontrados, 1):
            print(f"\n{i}. {problema['descricao']}")
            print(f"   Arquivo: {problema['arquivo']}")
            if 'linha' in problema:
                print(f"   Linha: {problema['linha']}")
            if 'codigo_atual' in problema:
                print(f"   Codigo atual: {problema['codigo_atual']}")
            if 'codigo_corrigido' in problema:
                print(f"   Correcao: {problema['codigo_corrigido']}")
    else:
        print("Nenhum problema de localização encontrado!")
        return
    
    # 5. Aplicar correções
    print(f"\nAPLICANDO CORRECOES ({len(problemas_encontrados)} problemas)...")
    aplicar_correcoes(problemas_encontrados, estrutura_atual)
    
    print(f"\nCORRECAO CONCLUIDA!")
    print("Teste recomendado:")
    print("  mkdir teste_init && cd teste_init")
    print("  cobol-to-docs --init")
    print("  ls -la config/ data/ examples/")

def mapear_estrutura_completa():
    """Mapeia onde estão os arquivos reais na estrutura atual."""
    print("  Mapeando arquivos de configuração e dados...")
    
    estrutura = {
        "config_locations": [],
        "data_locations": [],
        "examples_locations": [],
        "config_files": [],
        "data_files": [],
        "melhor_config": None,
        "melhor_data": None
    }
    
    # Locais para procurar (em ordem de prioridade)
    locais_busca = [
        "build/lib/cobol_to_docs",
        "cobol_to_docs",
        "build/bdist.*/lib/cobol_to_docs",
        "."
    ]
    
    for local_pattern in locais_busca:
        if "*" in local_pattern:
            locais = glob.glob(local_pattern)
        else:
            locais = [local_pattern] if os.path.exists(local_pattern) else []
        
        for local in locais:
            # Verificar config/
            config_path = os.path.join(local, "config")
            if os.path.exists(config_path):
                estrutura["config_locations"].append(config_path)
                if not estrutura["melhor_config"]:
                    estrutura["melhor_config"] = config_path
                
                # Listar arquivos config
                for arquivo in os.listdir(config_path):
                    if arquivo.endswith(('.yaml', '.yml')):
                        estrutura["config_files"].append(os.path.join(config_path, arquivo))
            
            # Verificar data/
            data_path = os.path.join(local, "data")
            if os.path.exists(data_path):
                estrutura["data_locations"].append(data_path)
                if not estrutura["melhor_data"]:
                    estrutura["melhor_data"] = data_path
                
                # Listar arquivos data
                for arquivo in os.listdir(data_path):
                    if arquivo.endswith(('.json', '.pkl')) or os.path.isdir(os.path.join(data_path, arquivo)):
                        estrutura["data_files"].append(os.path.join(data_path, arquivo))
            
            # Verificar examples/
            examples_path = os.path.join(local, "examples")
            if os.path.exists(examples_path):
                estrutura["examples_locations"].append(examples_path)
    
    print(f"    Config encontrado em {len(estrutura['config_locations'])} locais")
    print(f"    Data encontrado em {len(estrutura['data_locations'])} locais")
    print(f"    Melhor config: {estrutura['melhor_config']}")
    print(f"    Melhor data: {estrutura['melhor_data']}")
    
    return estrutura

def encontrar_arquivos_relevantes():
    """Encontra arquivos Python que podem ter lógica de localização."""
    arquivos_relevantes = []
    
    # Padrões de arquivos importantes
    padroes_importantes = [
        "cobol_to_docs/runner/*.py",
        "cobol_to_docs/*.py",
        "cobol_to_docs/src/**/*.py",
        "setup.py"
    ]
    
    for padrao in padroes_importantes:
        arquivos = glob.glob(padrao, recursive=True)
        arquivos_relevantes.extend(arquivos)
    
    # Remover duplicatas e arquivos irrelevantes
    arquivos_relevantes = list(set(arquivos_relevantes))
    arquivos_relevantes = [a for a in arquivos_relevantes if not a.endswith('__pycache__')]
    
    print(f"  Encontrados {len(arquivos_relevantes)} arquivos Python para análise")
    
    return arquivos_relevantes

def analisar_arquivo_python(arquivo_path: str, estrutura_atual: Dict):
    """Analisa um arquivo Python procurando por problemas de localização."""
    problemas = []
    
    try:
        with open(arquivo_path, 'r', encoding='utf-8') as f:
            conteudo = f.read()
        
        linhas = conteudo.split('\n')
        
        for i, linha in enumerate(linhas, 1):
            linha_strip = linha.strip()
            
            # Problema 1: Caminhos hardcoded
            if re.search(r'["\'][./]*cobol_to_docs[/\\]', linha) and 'import' not in linha:
                problemas.append({
                    "tipo": "caminho_hardcoded",
                    "arquivo": arquivo_path,
                    "linha": i,
                    "descricao": "Caminho hardcoded para cobol_to_docs",
                    "codigo_atual": linha_strip,
                    "linha_completa": linha
                })
            
            # Problema 2: Criação de pasta cobol_to_docs
            if 'makedirs' in linha and 'cobol_to_docs' in linha:
                problemas.append({
                    "tipo": "pasta_duplicada",
                    "arquivo": arquivo_path,
                    "linha": i,
                    "descricao": "Criando pasta cobol_to_docs desnecessária",
                    "codigo_atual": linha_strip,
                    "linha_completa": linha
                })
            
            # Problema 3: Função de inicialização problemática
            if 'def' in linha and any(palavra in linha.lower() for palavra in ['init', 'inicializar']):
                # Verificar se a função tem problemas
                if 'args' not in linha:  # Não é def main(args)
                    problemas.append({
                        "tipo": "funcao_init",
                        "arquivo": arquivo_path,
                        "linha": i,
                        "descricao": "Função de inicialização precisa ser reescrita",
                        "codigo_atual": linha_strip,
                        "linha_completa": linha
                    })
    
    except Exception as e:
        print(f"    ERRO ao analisar {arquivo_path}: {e}")
    
    return problemas

def analisar_local_setup(arquivo_path: str, estrutura_atual: Dict):
    """Análise específica do local_setup.py."""
    problemas = []
    
    try:
        with open(arquivo_path, 'r', encoding='utf-8') as f:
            conteudo = f.read()
        
        print(f"    Conteudo do local_setup.py: {len(conteudo)} caracteres")
        
        if len(conteudo.strip()) < 50:
            problemas.append({
                "tipo": "local_setup_vazio",
                "arquivo": arquivo_path,
                "linha": 1,
                "descricao": "local_setup.py muito simples ou vazio",
                "codigo_atual": "# Arquivo quase vazio"
            })
            return problemas
        
        linhas = conteudo.split('\n')
        
        # Verificar se tem lógica de localização adequada
        tem_build_lib = 'build/lib' in conteudo or 'build\\lib' in conteudo
        tem_deteccao_dinamica = '__file__' in conteudo
        tem_copia_arquivos = 'copy' in conteudo or 'shutil' in conteudo
        
        if not tem_build_lib:
            problemas.append({
                "tipo": "sem_build_lib",
                "arquivo": arquivo_path,
                "linha": 1,
                "descricao": "local_setup.py não procura em build/lib/cobol_to_docs",
                "codigo_atual": "# Lógica atual não verifica build/lib"
            })
        
        if not tem_deteccao_dinamica:
            problemas.append({
                "tipo": "sem_deteccao_dinamica",
                "arquivo": arquivo_path,
                "linha": 1,
                "descricao": "local_setup.py não usa __file__ para detecção dinâmica",
                "codigo_atual": "# Não usa __file__ para localização"
            })
        
        if not tem_copia_arquivos:
            problemas.append({
                "tipo": "sem_copia_arquivos",
                "arquivo": arquivo_path,
                "linha": 1,
                "descricao": "local_setup.py não copia arquivos originais",
                "codigo_atual": "# Não tem lógica de cópia de arquivos"
            })
        
        # Analisar funções específicas
        for i, linha in enumerate(linhas, 1):
            if 'def' in linha and any(palavra in linha.lower() for palavra in ['setup', 'init', 'create']):
                problemas.append({
                    "tipo": "funcao_local_setup",
                    "arquivo": arquivo_path,
                    "linha": i,
                    "descricao": "Função no local_setup.py precisa ser corrigida",
                    "codigo_atual": linha.strip(),
                    "linha_completa": linha
                })
    
    except Exception as e:
        print(f"    ERRO ao analisar {arquivo_path}: {e}")
        problemas.append({
            "tipo": "erro_leitura",
            "arquivo": arquivo_path,
            "linha": 1,
            "descricao": f"Erro ao ler local_setup.py: {e}"
        })
    
    return problemas

def aplicar_correcoes(problemas: List[Dict], estrutura_atual: Dict):
    """Aplica as correções automaticamente."""
    
    # Criar backups
    print("  Criando backups...")
    timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
    backup_dir = f"backup_correcoes_{timestamp}"
    os.makedirs(backup_dir, exist_ok=True)
    
    arquivos_modificados = set()
    
    for problema in problemas:
        arquivo = problema['arquivo']
        if arquivo not in arquivos_modificados:
            # Criar backup
            backup_path = os.path.join(backup_dir, os.path.basename(arquivo))
            shutil.copy2(arquivo, backup_path)
            arquivos_modificados.add(arquivo)
    
    print(f"    Backups criados em: {backup_dir}")
    
    # Aplicar correções por tipo
    print("  Aplicando correções...")
    
    # Correção 1: Reescrever local_setup.py se necessário
    local_setup_problemas = [p for p in problemas if p['arquivo'].endswith('local_setup.py')]
    if local_setup_problemas:
        corrigir_local_setup(estrutura_atual)
    
    # Correção 2: Corrigir funções de inicialização
    funcoes_init = [p for p in problemas if p['tipo'] == 'funcao_init']
    for problema in funcoes_init:
        corrigir_funcao_init(problema, estrutura_atual)
    
    # Correção 3: Remover caminhos hardcoded
    caminhos_hardcoded = [p for p in problemas if p['tipo'] == 'caminho_hardcoded']
    for problema in caminhos_hardcoded:
        corrigir_caminho_hardcoded(problema)
    
    # Correção 4: Remover criação de pastas duplicadas
    pastas_duplicadas = [p for p in problemas if p['tipo'] == 'pasta_duplicada']
    for problema in pastas_duplicadas:
        corrigir_pasta_duplicada(problema)
    
    print(f"    {len(arquivos_modificados)} arquivos modificados")

def corrigir_local_setup(estrutura_atual: Dict):
    """Corrige ou cria local_setup.py com lógica adequada."""
    local_setup_path = "cobol_to_docs/local_setup.py"
    
    print(f"    Corrigindo: {local_setup_path}")
    
    # Novo conteúdo para local_setup.py
    novo_conteudo = f'''"""
Local Setup - Configuração de localização de arquivos
Detecta automaticamente onde estão os arquivos de configuração e dados
"""

import os
import shutil
import glob
from pathlib import Path

def detectar_localizacao_arquivos():
    """
    Detecta onde estão os arquivos originais de config e data.
    Prioriza build/lib/cobol_to_docs/, depois cobol_to_docs/
    """
    # Locais para procurar (em ordem de prioridade)
    locais_busca = [
        Path("build/lib/cobol_to_docs"),  # Pacote instalado
        Path(__file__).parent,           # Mesmo diretório do local_setup.py
        Path(__file__).parent.parent / "cobol_to_docs",  # Desenvolvimento
        Path("cobol_to_docs"),           # Relativo ao diretório atual
    ]
    
    melhor_localizacao = None
    
    for local in locais_busca:
        if local.exists():
            config_path = local / "config"
            data_path = local / "data"
            
            # Verificar se tem arquivos importantes
            if config_path.exists() and data_path.exists():
                # Contar arquivos
                config_files = len(list(config_path.glob("*.yaml")))
                data_files = len(list(data_path.glob("*.json")))
                
                if config_files > 0 and data_files > 0:
                    melhor_localizacao = local
                    break
    
    return melhor_localizacao

def inicializar_ambiente_completo(diretorio_trabalho="."):
    """
    Inicializa ambiente completo copiando TODOS os arquivos originais.
    """
    diretorio_trabalho = Path(diretorio_trabalho).resolve()
    print(f"Inicializando ambiente em: {{diretorio_trabalho}}")
    
    # Detectar localização dos arquivos originais
    origem = detectar_localizacao_arquivos()
    
    if not origem:
        print("ERRO: Não foi possível encontrar arquivos originais!")
        return False
    
    print(f"Arquivos originais encontrados em: {{origem}}")
    
    # Estrutura para criar
    estrutura = {{
        "config": {{
            "pasta": True,
            "copiar_tudo": True,
            "extensoes": [".yaml", ".yml"]
        }},
        "data": {{
            "pasta": True,
            "copiar_tudo": True,
            "extensoes": [".json", ".pkl"],
            "subpastas": ["cache", "embeddings", "rag_sessions", "knowledge_base"]
        }},
        "examples": {{
            "pasta": True,
            "copiar_tudo": True,
            "extensoes": [".ipynb", ".cbl", ".cob", ".cobol"]
        }},
        "logs": {{"pasta": True}},
        "output": {{"pasta": True}},
        "input": {{"pasta": True}}
    }}
    
    print("Criando estrutura de diretórios...")
    
    # Criar estrutura
    for pasta_nome, config in estrutura.items():
        pasta_destino = diretorio_trabalho / pasta_nome
        pasta_destino.mkdir(parents=True, exist_ok=True)
        print(f"  Criado: {{pasta_nome}}/")
        
        # Criar subpastas se especificado
        for subpasta in config.get("subpastas", []):
            subpasta_destino = pasta_destino / subpasta
            subpasta_destino.mkdir(parents=True, exist_ok=True)
            print(f"  Criado: {{pasta_nome}}/{{subpasta}}/")
    
    print("Copiando arquivos originais...")
    
    # Copiar arquivos
    for pasta_nome, config in estrutura.items():
        if not config.get("copiar_tudo", False):
            continue
        
        pasta_origem = origem / pasta_nome
        pasta_destino = diretorio_trabalho / pasta_nome
        
        if not pasta_origem.exists():
            print(f"  AVISO: {{pasta_nome}}/ não encontrado na origem")
            continue
        
        print(f"  Copiando {{pasta_nome}}/:")
        
        # Copiar por extensão
        arquivos_copiados = 0
        for extensao in config.get("extensoes", []):
            pattern = f"*{{extensao}}"
            for arquivo_origem in pasta_origem.glob(pattern):
                arquivo_destino = pasta_destino / arquivo_origem.name
                try:
                    shutil.copy2(arquivo_origem, arquivo_destino)
                    print(f"    Copiado: {{arquivo_origem.name}}")
                    arquivos_copiados += 1
                except Exception as e:
                    print(f"    ERRO ao copiar {{arquivo_origem.name}}: {{e}}")
        
        # Copiar outros arquivos importantes
        for item in pasta_origem.iterdir():
            if item.is_file() and item.suffix not in config.get("extensoes", []):
                # Copiar arquivos sem extensão ou com extensões não listadas
                if item.name in ["README.md", "knowledge_base"] or item.suffix in [".txt", ".md"]:
                    arquivo_destino = pasta_destino / item.name
                    try:
                        if item.is_file():
                            shutil.copy2(item, arquivo_destino)
                        else:
                            shutil.copytree(item, arquivo_destino, dirs_exist_ok=True)
                        print(f"    Copiado: {{item.name}}")
                        arquivos_copiados += 1
                    except Exception as e:
                        print(f"    ERRO ao copiar {{item.name}}: {{e}}")
        
        print(f"    Total copiado: {{arquivos_copiados}} arquivos")
    
    # Criar marcador
    marcador = diretorio_trabalho / ".cobol_analyzer_initialized"
    with open(marcador, 'w', encoding='utf-8') as f:
        f.write(f"Inicializado com estrutura completa\\n")
        f.write(f"Origem: {{origem}}\\n")
        f.write(f"Data: {{__import__('datetime').datetime.now().isoformat()}}\\n")
    
    print("AMBIENTE INICIALIZADO COM SUCESSO!")
    print(f"Local: {{diretorio_trabalho}}")
    print(f"Origem: {{origem}}")
    
    # Verificar resultado
    config_count = len(list((diretorio_trabalho / "config").glob("*.yaml")))
    data_count = len(list((diretorio_trabalho / "data").glob("*")))
    
    print(f"Resumo: {{config_count}} configs, {{data_count}} dados")
    
    return True
'''
    
    # Escrever novo arquivo
    with open(local_setup_path, 'w', encoding='utf-8') as f:
        f.write(novo_conteudo)
    
    print(f"    local_setup.py reescrito com {len(novo_conteudo)} caracteres")

def corrigir_funcao_init(problema: Dict, estrutura_atual: Dict):
    """Corrige função de inicialização para usar local_setup."""
    arquivo = problema['arquivo']
    
    print(f"    Corrigindo função init em: {arquivo}")
    
    try:
        with open(arquivo, 'r', encoding='utf-8') as f:
            conteudo = f.read()
        
        # Adicionar import do local_setup se não existir
        if 'from .local_setup import' not in conteudo and 'import local_setup' not in conteudo:
            # Adicionar import
            linhas = conteudo.split('\n')
            insert_pos = 0
            
            for i, linha in enumerate(linhas):
                if linha.strip().startswith('import ') or linha.strip().startswith('from '):
                    insert_pos = i + 1
            
            linhas.insert(insert_pos, 'from .local_setup import inicializar_ambiente_completo')
            conteudo = '\n'.join(linhas)
        
        # Substituir função de inicialização
        # Procurar por def inicializar ou similar
        conteudo = re.sub(
            r'def\s+(inicializar\w*|setup\w*)\s*\([^)]*\):.*?(?=\ndef\s+|\nclass\s+|\nif\s+__name__|\Z)',
            'def inicializar_ambiente(diretorio_trabalho="."):\n    """Inicializa ambiente usando local_setup."""\n    return inicializar_ambiente_completo(diretorio_trabalho)',
            conteudo,
            flags=re.DOTALL
        )
        
        # Salvar arquivo modificado
        with open(arquivo, 'w', encoding='utf-8') as f:
            f.write(conteudo)
        
        print(f"      Função init corrigida")
    
    except Exception as e:
        print(f"      ERRO ao corrigir função init: {e}")

def corrigir_caminho_hardcoded(problema: Dict):
    """Remove caminhos hardcoded."""
    arquivo = problema['arquivo']
    linha_num = problema['linha']
    
    try:
        with open(arquivo, 'r', encoding='utf-8') as f:
            linhas = f.readlines()
        
        # Comentar linha problemática
        if linha_num <= len(linhas):
            linha_original = linhas[linha_num - 1]
            linhas[linha_num - 1] = f"    # CORRIGIDO: {linha_original.strip()}\n"
            linhas.insert(linha_num - 1, "    # TODO: Usar detecção dinâmica de caminhos\n")
        
        with open(arquivo, 'w', encoding='utf-8') as f:
            f.writelines(linhas)
        
        print(f"      Caminho hardcoded comentado na linha {linha_num}")
    
    except Exception as e:
        print(f"      ERRO ao corrigir caminho: {e}")

def corrigir_pasta_duplicada(problema: Dict):
    """Remove criação de pasta cobol_to_docs duplicada."""
    arquivo = problema['arquivo']
    linha_num = problema['linha']
    
    try:
        with open(arquivo, 'r', encoding='utf-8') as f:
            linhas = f.readlines()
        
        # Comentar linha problemática
        if linha_num <= len(linhas):
            linha_original = linhas[linha_num - 1]
            linhas[linha_num - 1] = f"    # CORRIGIDO: {linha_original.strip()}\n"
            linhas.insert(linha_num - 1, "    # TODO: Criar estrutura no diretório atual, não subpasta\n")
        
        with open(arquivo, 'w', encoding='utf-8') as f:
            f.writelines(linhas)
        
        print(f"      Criação de pasta duplicada removida na linha {linha_num}")
    
    except Exception as e:
        print(f"      ERRO ao corrigir pasta duplicada: {e}")

if __name__ == "__main__":
    main()
