#!/usr/bin/env python3
"""
Analisador de Localização de Arquivos
Vasculha a aplicação para encontrar onde está o problema de localização
dos arquivos de configuração e dados, especialmente no local_setup.py
"""

import os
import sys
import re
import ast
from pathlib import Path
from typing import List, Dict, Any, Optional

def main():
    print("🔍 ANALISADOR DE LOCALIZAÇÃO DE ARQUIVOS")
    print("Vasculhando aplicação para encontrar problemas de localização")
    print("=" * 65)
    
    if not os.path.exists("cobol_to_docs"):
        print("❌ Pasta cobol_to_docs não encontrada!")
        return
    
    # 1. Mapear estrutura atual
    print("\n📁 MAPEANDO ESTRUTURA ATUAL...")
    estrutura_atual = mapear_estrutura_completa()
    
    # 2. Analisar arquivos Python relevantes
    print("\n🔍 ANALISANDO ARQUIVOS PYTHON...")
    arquivos_relevantes = encontrar_arquivos_relevantes()
    
    problemas_encontrados = []
    
    for arquivo in arquivos_relevantes:
        print(f"\n📄 Analisando: {arquivo}")
        problemas_arquivo = analisar_arquivo_python(arquivo, estrutura_atual)
        if problemas_arquivo:
            problemas_encontrados.extend(problemas_arquivo)
    
    # 3. Análise específica do local_setup.py
    local_setup_path = "cobol_to_docs/local_setup.py"
    if os.path.exists(local_setup_path):
        print(f"\n🎯 ANÁLISE ESPECÍFICA: {local_setup_path}")
        problemas_setup = analisar_local_setup(local_setup_path, estrutura_atual)
        problemas_encontrados.extend(problemas_setup)
    else:
        print(f"\n⚠️  {local_setup_path} não encontrado")
    
    # 4. Relatório final
    print("\n" + "=" * 65)
    print("📋 PROBLEMAS ENCONTRADOS E CORREÇÕES NECESSÁRIAS")
    print("=" * 65)
    
    if problemas_encontrados:
        for i, problema in enumerate(problemas_encontrados, 1):
            print(f"\n{i}. {problema['descricao']}")
            print(f"   📄 Arquivo: {problema['arquivo']}")
            if 'linha' in problema:
                print(f"   📍 Linha: {problema['linha']}")
            if 'codigo_atual' in problema:
                print(f"   ❌ Código atual: {problema['codigo_atual']}")
            if 'codigo_corrigido' in problema:
                print(f"   ✅ Correção: {problema['codigo_corrigido']}")
            if 'explicacao' in problema:
                print(f"   💡 Explicação: {problema['explicacao']}")
    else:
        print("✅ Nenhum problema de localização encontrado!")
    
    print(f"\n🎯 RESUMO: {len(problemas_encontrados)} problemas encontrados")

def mapear_estrutura_completa():
    """Mapeia onde estão os arquivos reais na estrutura atual."""
    print("   Mapeando arquivos de configuração e dados...")
    
    estrutura = {
        "config_locations": [],
        "data_locations": [],
        "examples_locations": [],
        "config_files": [],
        "data_files": []
    }
    
    # Locais para procurar
    locais_busca = [
        "cobol_to_docs",
        "build/lib/cobol_to_docs",
        "build/bdist.*/lib/cobol_to_docs",
        "."
    ]
    
    for local_pattern in locais_busca:
        if "*" in local_pattern:
            import glob
            locais = glob.glob(local_pattern)
        else:
            locais = [local_pattern] if os.path.exists(local_pattern) else []
        
        for local in locais:
            # Verificar config/
            config_path = os.path.join(local, "config")
            if os.path.exists(config_path):
                estrutura["config_locations"].append(config_path)
                # Listar arquivos config
                for arquivo in os.listdir(config_path):
                    if arquivo.endswith(('.yaml', '.yml')):
                        estrutura["config_files"].append(os.path.join(config_path, arquivo))
            
            # Verificar data/
            data_path = os.path.join(local, "data")
            if os.path.exists(data_path):
                estrutura["data_locations"].append(data_path)
                # Listar arquivos data
                for arquivo in os.listdir(data_path):
                    if arquivo.endswith(('.json', '.pkl')):
                        estrutura["data_files"].append(os.path.join(data_path, arquivo))
            
            # Verificar examples/
            examples_path = os.path.join(local, "examples")
            if os.path.exists(examples_path):
                estrutura["examples_locations"].append(examples_path)
    
    # Mostrar o que foi encontrado
    print(f"      Config encontrado em {len(estrutura['config_locations'])} locais")
    print(f"      Data encontrado em {len(estrutura['data_locations'])} locais")
    print(f"      Examples encontrado em {len(estrutura['examples_locations'])} locais")
    
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
    
    import glob
    for padrao in padroes_importantes:
        arquivos = glob.glob(padrao, recursive=True)
        arquivos_relevantes.extend(arquivos)
    
    # Remover duplicatas
    arquivos_relevantes = list(set(arquivos_relevantes))
    
    print(f"   Encontrados {len(arquivos_relevantes)} arquivos Python para análise")
    
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
            if re.search(r'["\'][./]*cobol_to_docs[/\\]', linha):
                problemas.append({
                    "arquivo": arquivo_path,
                    "linha": i,
                    "descricao": "Caminho hardcoded para cobol_to_docs",
                    "codigo_atual": linha_strip,
                    "codigo_corrigido": "# Usar detecção dinâmica em vez de caminho fixo",
                    "explicacao": "Caminhos hardcoded quebram quando a estrutura muda"
                })
            
            # Problema 2: Uso de os.path.join com caminhos fixos
            if 'os.path.join' in linha and 'config' in linha and '"' in linha:
                if not any(var in linha for var in ['__file__', 'base_dir', 'root_dir']):
                    problemas.append({
                        "arquivo": arquivo_path,
                        "linha": i,
                        "descricao": "os.path.join com caminho fixo para config",
                        "codigo_atual": linha_strip,
                        "codigo_corrigido": "# Usar caminho relativo a __file__ ou detecção dinâmica",
                        "explicacao": "Deve detectar localização dinamicamente"
                    })
            
            # Problema 3: Criação de pasta cobol_to_docs
            if 'makedirs' in linha and 'cobol_to_docs' in linha:
                problemas.append({
                    "arquivo": arquivo_path,
                    "linha": i,
                    "descricao": "Criando pasta cobol_to_docs desnecessária",
                    "codigo_atual": linha_strip,
                    "codigo_corrigido": "# Criar estrutura no diretório atual, não subpasta",
                    "explicacao": "Não deve criar pasta cobol_to_docs dentro do projeto"
                })
            
            # Problema 4: Não usa __file__ para localização
            if ('config' in linha or 'data' in linha) and 'path' in linha.lower():
                if '__file__' not in linha and 'import' not in linha and '#' not in linha:
                    if any(palavra in linha for palavra in ['join', 'Path', '/']):
                        problemas.append({
                            "arquivo": arquivo_path,
                            "linha": i,
                            "descricao": "Não usa __file__ para localização relativa",
                            "codigo_atual": linha_strip,
                            "codigo_corrigido": "# Usar Path(__file__).parent para localização relativa",
                            "explicacao": "__file__ garante localização correta independente de onde é executado"
                        })
            
            # Problema 5: Função de inicialização problemática
            if 'def' in linha and any(palavra in linha.lower() for palavra in ['init', 'setup', 'inicializar']):
                # Verificar se a função tem problemas comuns
                if i < len(linhas) - 10:  # Verificar próximas linhas
                    funcao_conteudo = '\n'.join(linhas[i:i+10])
                    if 'cobol_to_docs' in funcao_conteudo and 'makedirs' in funcao_conteudo:
                        problemas.append({
                            "arquivo": arquivo_path,
                            "linha": i,
                            "descricao": "Função de inicialização com lógica problemática",
                            "codigo_atual": linha_strip,
                            "explicacao": "Função cria estrutura incorreta ou não encontra arquivos originais"
                        })
    
    except Exception as e:
        print(f"      ⚠️  Erro ao analisar {arquivo_path}: {e}")
    
    return problemas

def analisar_local_setup(arquivo_path: str, estrutura_atual: Dict):
    """Análise específica do local_setup.py."""
    problemas = []
    
    try:
        with open(arquivo_path, 'r', encoding='utf-8') as f:
            conteudo = f.read()
        
        print(f"      📄 Conteúdo do local_setup.py ({len(conteudo)} caracteres)")
        
        # Verificar se tem lógica de localização
        if 'config' in conteudo.lower():
            print("      ✅ Referências a 'config' encontradas")
        else:
            print("      ❌ Nenhuma referência a 'config' encontrada")
        
        if 'data' in conteudo.lower():
            print("      ✅ Referências a 'data' encontradas")
        else:
            print("      ❌ Nenhuma referência a 'data' encontrada")
        
        linhas = conteudo.split('\n')
        
        for i, linha in enumerate(linhas, 1):
            linha_strip = linha.strip()
            
            # Análise específica para local_setup.py
            
            # Problema 1: Não detecta múltiplas localizações
            if 'config' in linha and 'path' in linha.lower():
                if not any(loc in linha for loc in ['build', 'lib', '__file__']):
                    problemas.append({
                        "arquivo": arquivo_path,
                        "linha": i,
                        "descricao": "local_setup.py não verifica múltiplas localizações",
                        "codigo_atual": linha_strip,
                        "codigo_corrigido": "# Verificar build/lib/cobol_to_docs/, cobol_to_docs/, etc.",
                        "explicacao": "Deve procurar em build/lib/cobol_to_docs/ primeiro, depois cobol_to_docs/"
                    })
            
            # Problema 2: Função que não copia arquivos
            if 'def' in linha and any(palavra in linha.lower() for palavra in ['setup', 'init', 'create']):
                # Verificar se a função tem lógica de cópia
                funcao_inicio = i
                funcao_fim = funcao_inicio
                
                # Encontrar fim da função
                for j in range(i, len(linhas)):
                    if linhas[j].startswith('def ') and j > i:
                        funcao_fim = j
                        break
                    elif linhas[j].startswith('class ') and j > i:
                        funcao_fim = j
                        break
                    elif j == len(linhas) - 1:
                        funcao_fim = j
                
                funcao_conteudo = '\n'.join(linhas[funcao_inicio:funcao_fim])
                
                if 'copy' not in funcao_conteudo and 'shutil' not in funcao_conteudo:
                    problemas.append({
                        "arquivo": arquivo_path,
                        "linha": i,
                        "descricao": "Função no local_setup.py não copia arquivos originais",
                        "codigo_atual": linha_strip,
                        "codigo_corrigido": "# Adicionar lógica para copiar arquivos de config/ e data/",
                        "explicacao": "Função deve copiar arquivos originais, não criar padrão"
                    })
                
                # Verificar se detecta localização correta
                if estrutura_atual["config_locations"]:
                    melhor_config = estrutura_atual["config_locations"][0]
                    if 'build/lib' in melhor_config and 'build' not in funcao_conteudo:
                        problemas.append({
                            "arquivo": arquivo_path,
                            "linha": i,
                            "descricao": "local_setup.py não procura em build/lib/cobol_to_docs/",
                            "codigo_atual": f"# Função: {linha_strip}",
                            "codigo_corrigido": f"# Procurar primeiro em: {melhor_config}",
                            "explicacao": f"Arquivos estão em {melhor_config} mas função não procura lá"
                        })
            
            # Problema 3: Importações inadequadas
            if linha_strip.startswith('import ') or linha_strip.startswith('from '):
                if 'pathlib' not in conteudo and 'Path' not in conteudo:
                    if i == 1:  # Só reportar uma vez
                        problemas.append({
                            "arquivo": arquivo_path,
                            "linha": i,
                            "descricao": "local_setup.py não usa pathlib.Path",
                            "codigo_atual": "# Importações atuais",
                            "codigo_corrigido": "from pathlib import Path",
                            "explicacao": "pathlib.Path é mais robusto para manipulação de caminhos"
                        })
        
        # Análise geral do arquivo
        if len(conteudo.strip()) < 100:
            problemas.append({
                "arquivo": arquivo_path,
                "linha": 1,
                "descricao": "local_setup.py muito simples ou vazio",
                "codigo_atual": f"# Arquivo com {len(conteudo)} caracteres",
                "explicacao": "Arquivo pode não ter lógica suficiente para localização de arquivos"
            })
        
        # Verificar se tem lógica de detecção de ambiente
        if 'build' not in conteudo and 'lib' not in conteudo:
            problemas.append({
                "arquivo": arquivo_path,
                "linha": 1,
                "descricao": "local_setup.py não detecta ambiente de build",
                "codigo_atual": "# Lógica atual",
                "codigo_corrigido": "# Adicionar detecção de build/lib/cobol_to_docs/",
                "explicacao": "Deve detectar se está executando de pacote instalado ou desenvolvimento"
            })
    
    except Exception as e:
        print(f"      ❌ Erro ao analisar {arquivo_path}: {e}")
        problemas.append({
            "arquivo": arquivo_path,
            "linha": 1,
            "descricao": f"Erro ao ler local_setup.py: {e}",
            "explicacao": "Arquivo pode ter problemas de codificação ou sintaxe"
        })
    
    return problemas

if __name__ == "__main__":
    main()
