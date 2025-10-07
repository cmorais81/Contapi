#!/usr/bin/env python3
"""
Analisador Completo de Estrutura de Projeto COBOL_ANALYZER
Identifica problemas de importação, build, entry points e comandos globais após mudanças estruturais.

Uso:
    python analisador_projeto_cobol_completo.py

Configuração:
    Modifique as variáveis CAMINHO_BASE e NOME_PACOTE_PROJETO abaixo.
"""

import os
import sys
import re
import ast
from pathlib import Path
from typing import List, Dict, Any, Tuple, Optional

class AnalisadorProjetoCobolCompleto:
    def __init__(self, caminho_base: str, nome_pacote: str):
        self.caminho_base = os.path.abspath(caminho_base)
        self.nome_pacote = nome_pacote
        self.caminho_projeto = os.path.join(self.caminho_base, nome_pacote)
        
        self.relatorio = {
            "arquivos_com_problemas": [],
            "manipulacao_sys_path": [],
            "diretorios_sem_init": [],
            "importacoes_relativas": [],
            "importacoes_src": [],
            "pontos_entrada": [],
            "setup_py_analise": {},
            "entry_points_problemas": [],
            "comandos_globais": [],
            "estrutura_build": {},
            "resumo_estatisticas": {}
        }
    
    def validar_estrutura(self) -> bool:
        """Valida se a estrutura do projeto existe."""
        if not os.path.isdir(self.caminho_projeto):
            print(f"❌ ERRO: O diretório do projeto '{self.caminho_projeto}' não foi encontrado.")
            print(f"   Certifique-se de que o script está no diretório correto.")
            return False
        
        print(f"✅ Projeto encontrado: {self.caminho_projeto}")
        return True
    
    def analisar_setup_py(self):
        """Analisa o arquivo setup.py para validar configurações de build."""
        setup_path = os.path.join(self.caminho_projeto, "setup.py")
        
        if not os.path.exists(setup_path):
            self.relatorio["setup_py_analise"] = {
                "existe": False,
                "problemas": ["Arquivo setup.py não encontrado - necessário para instalação via pip"]
            }
            return
        
        try:
            with open(setup_path, 'r', encoding='utf-8') as f:
                conteudo = f.read()
            
            # Parse do AST para extrair informações
            tree = ast.parse(conteudo)
            
            setup_info = {
                "existe": True,
                "entry_points": [],
                "py_modules": [],
                "packages": [],
                "problemas": [],
                "comandos_globais": []
            }
            
            # Procurar pela chamada setup()
            for node in ast.walk(tree):
                if isinstance(node, ast.Call) and hasattr(node.func, 'id') and node.func.id == 'setup':
                    for keyword in node.keywords:
                        if keyword.arg == 'entry_points':
                            # Extrair entry points
                            if isinstance(keyword.value, ast.Dict):
                                for key, value in zip(keyword.value.keys, keyword.value.values):
                                    if hasattr(key, 's') and key.s == 'console_scripts':
                                        if isinstance(value, ast.List):
                                            for item in value.elts:
                                                if hasattr(item, 's'):
                                                    entry_point = item.s
                                                    setup_info["entry_points"].append(entry_point)
                                                    
                                                    # Extrair comando e módulo
                                                    if '=' in entry_point:
                                                        comando, modulo_func = entry_point.split('=', 1)
                                                        setup_info["comandos_globais"].append({
                                                            "comando": comando.strip(),
                                                            "modulo": modulo_func.strip(),
                                                            "valido": self._validar_entry_point(modulo_func.strip())
                                                        })
                        
                        elif keyword.arg == 'py_modules':
                            if isinstance(keyword.value, ast.List):
                                for item in keyword.value.elts:
                                    if hasattr(item, 's'):
                                        setup_info["py_modules"].append(item.s)
            
            # Validar entry points
            for entry_point in setup_info["entry_points"]:
                if '=' in entry_point:
                    comando, modulo_func = entry_point.split('=', 1)
                    modulo_func = modulo_func.strip()
                    
                    # Verificar se o módulo existe na nova estrutura
                    if modulo_func.startswith('main:') or modulo_func.startswith('cli:'):
                        modulo_nome = modulo_func.split(':')[0]
                        
                        # Na nova estrutura, main.py e cli.py estão em runner/
                        caminho_esperado = os.path.join(self.caminho_projeto, "runner", f"{modulo_nome}.py")
                        if not os.path.exists(caminho_esperado):
                            setup_info["problemas"].append(
                                f"Entry point '{entry_point}' aponta para '{modulo_nome}' que não existe na raiz. "
                                f"Deveria ser '{self.nome_pacote}.runner.{modulo_nome}:main'"
                            )
                        else:
                            setup_info["problemas"].append(
                                f"Entry point '{entry_point}' precisa ser atualizado para "
                                f"'{comando.strip()}={self.nome_pacote}.runner.{modulo_nome}:main'"
                            )
            
            self.relatorio["setup_py_analise"] = setup_info
            
        except Exception as e:
            self.relatorio["setup_py_analise"] = {
                "existe": True,
                "problemas": [f"Erro ao analisar setup.py: {e}"]
            }
    
    def _validar_entry_point(self, modulo_func: str) -> bool:
        """Valida se um entry point é válido na nova estrutura."""
        try:
            if ':' in modulo_func:
                modulo, funcao = modulo_func.split(':', 1)
                
                # Verificar se o módulo existe
                if modulo in ['main', 'cli']:
                    # Na nova estrutura, deveria estar em runner/
                    caminho_arquivo = os.path.join(self.caminho_projeto, "runner", f"{modulo}.py")
                    return os.path.exists(caminho_arquivo)
                
                # Para outros módulos, verificar se existem
                partes = modulo.split('.')
                caminho_arquivo = os.path.join(self.caminho_projeto, *partes) + ".py"
                return os.path.exists(caminho_arquivo)
            
            return False
        except:
            return False
    
    def analisar_estrutura_build(self):
        """Analisa a estrutura necessária para build do pacote."""
        estrutura = {
            "arquivos_essenciais": {},
            "diretorios_essenciais": {},
            "problemas": []
        }
        
        # Arquivos essenciais na raiz do pacote
        arquivos_essenciais = {
            "setup.py": "Necessário para instalação via pip",
            "__init__.py": "Marca o diretório como pacote Python",
        }
        
        for arquivo, descricao in arquivos_essenciais.items():
            caminho = os.path.join(self.caminho_projeto, arquivo)
            estrutura["arquivos_essenciais"][arquivo] = {
                "existe": os.path.exists(caminho),
                "descricao": descricao,
                "caminho": caminho
            }
            
            if not os.path.exists(caminho):
                estrutura["problemas"].append(f"Arquivo {arquivo} não encontrado: {descricao}")
        
        # Diretórios essenciais
        diretorios_essenciais = {
            "src": "Código fonte principal",
            "runner": "Scripts de entrada (main.py, cli.py)",
            "config": "Arquivos de configuração",
            "examples": "Exemplos de uso"
        }
        
        for diretorio, descricao in diretorios_essenciais.items():
            caminho = os.path.join(self.caminho_projeto, diretorio)
            estrutura["diretorios_essenciais"][diretorio] = {
                "existe": os.path.exists(caminho),
                "descricao": descricao,
                "caminho": caminho
            }
        
        self.relatorio["estrutura_build"] = estrutura
    
    def analisar_diretorios_sem_init(self):
        """Identifica diretórios que precisam de __init__.py."""
        for raiz, dirs, arquivos in os.walk(self.caminho_projeto):
            # Ignorar diretórios especiais
            dirs[:] = [d for d in dirs if not d.startswith('.') and d != '__pycache__']
            
            # Verificar se há arquivos Python no diretório
            tem_python = any(f.endswith('.py') for f in arquivos)
            tem_init = '__init__.py' in arquivos
            
            if tem_python and not tem_init:
                caminho_relativo = os.path.relpath(raiz, self.caminho_base)
                self.relatorio["diretorios_sem_init"].append(caminho_relativo)
    
    def analisar_arquivo_python(self, caminho_arquivo: str) -> Dict[str, Any]:
        """Analisa um arquivo Python específico."""
        caminho_relativo = os.path.relpath(caminho_arquivo, self.caminho_base)
        problemas = {
            "arquivo": caminho_relativo,
            "manipulacao_sys_path": [],
            "importacoes_src": [],
            "importacoes_relativas": [],
            "funcoes_main": [],
            "outros_problemas": []
        }
        
        try:
            with open(caminho_arquivo, 'r', encoding='utf-8') as f:
                linhas = f.readlines()
            
            for i, linha in enumerate(linhas, 1):
                linha_strip = linha.strip()
                
                # Detectar manipulação de sys.path
                if re.search(r'sys\.path\.(insert|append)', linha_strip):
                    problemas["manipulacao_sys_path"].append({
                        "linha": i,
                        "codigo": linha_strip,
                        "sugestao": "REMOVER - Use importações absolutas com o nome do pacote"
                    })
                
                # Detectar importações que começam com 'src.'
                if re.match(r'^\s*(from\s+src\.|import\s+src\.)', linha_strip):
                    nova_importacao = linha_strip.replace('src.', f'{self.nome_pacote}.src.')
                    problemas["importacoes_src"].append({
                        "linha": i,
                        "original": linha_strip,
                        "sugestao": nova_importacao
                    })
                
                # Detectar importações relativas
                if re.match(r'^\s*from\s+\.', linha_strip):
                    # Calcular o caminho absoluto baseado na localização do arquivo
                    dir_arquivo = os.path.dirname(caminho_relativo)
                    if dir_arquivo:
                        partes_caminho = dir_arquivo.replace(os.sep, '.')
                        nova_importacao = linha_strip.replace('from .', f'from {partes_caminho}.')
                    else:
                        nova_importacao = linha_strip.replace('from .', f'from {self.nome_pacote}.')
                    
                    problemas["importacoes_relativas"].append({
                        "linha": i,
                        "original": linha_strip,
                        "sugestao": nova_importacao
                    })
                
                # Detectar funções main
                if re.match(r'^\s*def\s+main\s*\(', linha_strip):
                    problemas["funcoes_main"].append({
                        "linha": i,
                        "funcao": linha_strip
                    })
                
                # Detectar pontos de entrada (if __name__ == '__main__')
                if '__name__' in linha_strip and '__main__' in linha_strip:
                    self.relatorio["pontos_entrada"].append({
                        "arquivo": caminho_relativo,
                        "linha": i,
                        "tem_funcao_main": len(problemas["funcoes_main"]) > 0
                    })
        
        except Exception as e:
            problemas["outros_problemas"].append(f"Erro ao ler arquivo: {e}")
        
        return problemas
    
    def analisar_todos_arquivos(self):
        """Analisa todos os arquivos Python do projeto."""
        total_arquivos = 0
        arquivos_com_problemas = 0
        
        for raiz, dirs, arquivos in os.walk(self.caminho_projeto):
            # Ignorar diretórios especiais
            dirs[:] = [d for d in dirs if not d.startswith('.') and d != '__pycache__']
            
            for arquivo in arquivos:
                if arquivo.endswith('.py'):
                    total_arquivos += 1
                    caminho_completo = os.path.join(raiz, arquivo)
                    problemas = self.analisar_arquivo_python(caminho_completo)
                    
                    # Verificar se há problemas
                    tem_problemas = any([
                        problemas["manipulacao_sys_path"],
                        problemas["importacoes_src"],
                        problemas["importacoes_relativas"],
                        problemas["outros_problemas"]
                    ])
                    
                    if tem_problemas:
                        arquivos_com_problemas += 1
                        self.relatorio["arquivos_com_problemas"].append(problemas)
        
        self.relatorio["resumo_estatisticas"] = {
            "total_arquivos": total_arquivos,
            "arquivos_com_problemas": arquivos_com_problemas,
            "arquivos_ok": total_arquivos - arquivos_com_problemas
        }
    
    def gerar_relatorio(self):
        """Gera o relatório final de análise."""
        print("\n" + "="*80)
        print("📋 RELATÓRIO COMPLETO DE ANÁLISE DE ESTRUTURA DO PROJETO")
        print("="*80)
        
        print(f"\n📁 Projeto: {self.nome_pacote}")
        print(f"📍 Localização: {self.caminho_projeto}")
        
        # Estatísticas gerais
        stats = self.relatorio["resumo_estatisticas"]
        print(f"\n📊 ESTATÍSTICAS:")
        print(f"   • Total de arquivos Python: {stats['total_arquivos']}")
        print(f"   • Arquivos com problemas: {stats['arquivos_com_problemas']}")
        print(f"   • Arquivos sem problemas: {stats['arquivos_ok']}")
        
        # Análise do setup.py
        setup_info = self.relatorio["setup_py_analise"]
        print(f"\n🔧 ANÁLISE DO SETUP.PY:")
        if setup_info.get("existe", False):
            print("   ✅ Arquivo setup.py encontrado")
            
            if setup_info.get("entry_points"):
                print("   📌 Entry Points encontrados:")
                for ep in setup_info["entry_points"]:
                    print(f"      • {ep}")
            
            if setup_info.get("comandos_globais"):
                print("   🌐 Comandos Globais configurados:")
                for cmd in setup_info["comandos_globais"]:
                    status = "✅" if cmd["valido"] else "❌"
                    print(f"      {status} {cmd['comando']} -> {cmd['modulo']}")
            
            if setup_info.get("problemas"):
                print("   🚨 Problemas no setup.py:")
                for problema in setup_info["problemas"]:
                    print(f"      • {problema}")
        else:
            print("   ❌ Arquivo setup.py não encontrado")
        
        # Estrutura de build
        estrutura = self.relatorio["estrutura_build"]
        print(f"\n🏗️  ESTRUTURA DE BUILD:")
        
        print("   📄 Arquivos essenciais:")
        for arquivo, info in estrutura.get("arquivos_essenciais", {}).items():
            status = "✅" if info["existe"] else "❌"
            print(f"      {status} {arquivo} - {info['descricao']}")
        
        print("   📁 Diretórios essenciais:")
        for diretorio, info in estrutura.get("diretorios_essenciais", {}).items():
            status = "✅" if info["existe"] else "❌"
            print(f"      {status} {diretorio}/ - {info['descricao']}")
        
        # Diretórios sem __init__.py
        if self.relatorio["diretorios_sem_init"]:
            print(f"\n🚨 AÇÃO NECESSÁRIA: Adicionar arquivos __init__.py")
            print("   Os seguintes diretórios precisam de um arquivo __init__.py:")
            for diretorio in self.relatorio["diretorios_sem_init"]:
                print(f"   📁 {diretorio}/__init__.py")
        
        # Pontos de entrada identificados
        if self.relatorio["pontos_entrada"]:
            print(f"\n🎯 PONTOS DE ENTRADA IDENTIFICADOS:")
            for ponto in self.relatorio["pontos_entrada"]:
                status = "✅" if ponto.get("tem_funcao_main", False) else "⚠️"
                print(f"   {status} {ponto['arquivo']} (linha {ponto['linha']})")
        
        # Problemas por arquivo (resumido)
        if self.relatorio["arquivos_com_problemas"]:
            print(f"\n🔧 RESUMO DE CORREÇÕES NECESSÁRIAS:")
            
            total_sys_path = sum(len(a["manipulacao_sys_path"]) for a in self.relatorio["arquivos_com_problemas"])
            total_src = sum(len(a["importacoes_src"]) for a in self.relatorio["arquivos_com_problemas"])
            total_relativas = sum(len(a["importacoes_relativas"]) for a in self.relatorio["arquivos_com_problemas"])
            
            print(f"   • {total_sys_path} linhas com manipulação de sys.path para remover")
            print(f"   • {total_src} importações 'src.*' para corrigir")
            print(f"   • {total_relativas} importações relativas para corrigir")
        
        # Instruções finais
        print(f"\n" + "="*80)
        print("📝 INSTRUÇÕES DE CORREÇÃO PRIORITÁRIAS:")
        print("="*80)
        
        print("\n1️⃣ CORRIGIR SETUP.PY (CRÍTICO PARA INSTALAÇÃO):")
        if setup_info.get("problemas"):
            for problema in setup_info["problemas"]:
                print(f"   • {problema}")
        
        print("\n2️⃣ CRIAR ARQUIVOS __init__.py:")
        print("   Execute os seguintes comandos:")
        for diretorio in self.relatorio["diretorios_sem_init"]:
            print(f"   touch {diretorio}/__init__.py")
        
        print("\n3️⃣ CORRIGIR IMPORTAÇÕES:")
        print("   • Remova todas as linhas com sys.path.insert() ou sys.path.append()")
        print(f"   • Substitua 'from src.' por 'from {self.nome_pacote}.src.'")
        print("   • Substitua importações relativas por absolutas conforme sugerido")
        
        print("\n4️⃣ TESTAR INSTALAÇÃO E COMANDOS GLOBAIS:")
        print("   Após as correções:")
        print(f"   cd {self.caminho_base}")
        print(f"   pip install -e ./{self.nome_pacote}/")
        print("   # Testar comandos globais:")
        if setup_info.get("comandos_globais"):
            for cmd in setup_info["comandos_globais"]:
                print(f"   {cmd['comando']} --help")
        
        print("\n5️⃣ EXECUTAR DIRETAMENTE (ALTERNATIVA):")
        print(f"   python -m {self.nome_pacote}.runner.main")
        print(f"   python -m {self.nome_pacote}.runner.cli")
        
        if not any([
            self.relatorio["diretorios_sem_init"],
            self.relatorio["arquivos_com_problemas"],
            setup_info.get("problemas", [])
        ]):
            print(f"\n🎉 PARABÉNS! Nenhum problema crítico encontrado!")
            print(f"   O projeto parece estar bem estruturado para a nova organização.")
    
    def executar_analise(self):
        """Executa a análise completa do projeto."""
        print("🔍 Iniciando análise completa do projeto COBOL_ANALYZER...")
        
        if not self.validar_estrutura():
            return False
        
        print("🔧 Analisando setup.py e configurações de build...")
        self.analisar_setup_py()
        
        print("🏗️  Analisando estrutura de build...")
        self.analisar_estrutura_build()
        
        print("📂 Analisando estrutura de diretórios...")
        self.analisar_diretorios_sem_init()
        
        print("📄 Analisando arquivos Python...")
        self.analisar_todos_arquivos()
        
        print("📋 Gerando relatório...")
        self.gerar_relatorio()
        
        return True

def main():
    """Função principal do analisador."""
    # --- CONFIGURAÇÃO ---
    # Modifique estas variáveis conforme sua estrutura:
    
    # Caminho para o diretório que CONTÉM a pasta do projeto
    # Use "." se este script estiver no mesmo nível que a pasta cobol_to_docs
    CAMINHO_BASE = "."
    
    # Nome da pasta que contém seu projeto (que se tornou um pacote)
    NOME_PACOTE_PROJETO = "cobol_to_docs"
    
    # --- EXECUÇÃO ---
    analisador = AnalisadorProjetoCobolCompleto(CAMINHO_BASE, NOME_PACOTE_PROJETO)
    sucesso = analisador.executar_analise()
    
    if not sucesso:
        print("\n❌ Análise não pôde ser concluída devido a erros.")
        sys.exit(1)
    
    print(f"\n✅ Análise completa concluída! Siga as instruções acima para corrigir o projeto.")

if __name__ == "__main__":
    main()
