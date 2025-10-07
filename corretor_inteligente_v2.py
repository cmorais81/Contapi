#!/usr/bin/env python3
"""
Corretor Inteligente V2 - Resolve problemas de instalação pip
Corrige especificamente o erro "pyproject.toml not found" e problemas de setup.py

Uso:
    python corretor_inteligente_v2.py                    # Correção interativa
    python corretor_inteligente_v2.py --auto             # Correção automática
    python corretor_inteligente_v2.py --apenas-analise   # Só análise
"""

import os
import sys
import re
import shutil
import argparse
from pathlib import Path
from typing import List, Dict, Any
from datetime import datetime

class CorretorInteligenteV2:
    def __init__(self, caminho_base: str = ".", modo_auto: bool = False):
        self.caminho_base = os.path.abspath(caminho_base)
        self.modo_auto = modo_auto
        
        # Detectar estrutura
        self.detectar_estrutura()
        
        self.problemas_encontrados = []
        self.correcoes_aplicadas = []
        self.backup_criado = False
    
    def detectar_estrutura(self):
        """Detecta automaticamente a estrutura do projeto."""
        # Procurar pela pasta cobol_to_docs
        for item in os.listdir(self.caminho_base):
            caminho_item = os.path.join(self.caminho_base, item)
            if os.path.isdir(caminho_item) and item == "cobol_to_docs":
                self.caminho_projeto = caminho_item
                self.nome_pacote = "cobol_to_docs"
                return
        
        # Se não encontrar, procurar por qualquer pasta que contenha runner/
        for item in os.listdir(self.caminho_base):
            caminho_item = os.path.join(self.caminho_base, item)
            if os.path.isdir(caminho_item):
                runner_path = os.path.join(caminho_item, "runner")
                if os.path.isdir(runner_path):
                    self.caminho_projeto = caminho_item
                    self.nome_pacote = item
                    return
        
        print("❌ Não foi possível encontrar a estrutura do projeto!")
        sys.exit(1)
    
    def criar_backup(self):
        """Cria backup do projeto."""
        if self.backup_criado:
            return True
        
        timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
        backup_dir = f"{self.caminho_projeto}_backup_{timestamp}"
        
        try:
            shutil.copytree(self.caminho_projeto, backup_dir)
            print(f"✅ Backup criado: {os.path.basename(backup_dir)}")
            self.backup_criado = True
            return True
        except Exception as e:
            print(f"❌ Erro ao criar backup: {e}")
            return False
    
    def perguntar_usuario(self, pergunta: str, default: str = "s") -> bool:
        """Pergunta algo ao usuário se não estiver em modo automático."""
        if self.modo_auto:
            return True
        
        resposta = input(f"{pergunta} [{default}/n]: ").strip().lower()
        return resposta in ['', 's', 'sim', 'y', 'yes']
    
    def problema_1_setup_py_correto(self):
        """Cria ou corrige o setup.py principal para instalação pip."""
        print("\n🔍 Verificando configuração do setup.py para instalação pip...")
        
        setup_principal = os.path.join(self.caminho_projeto, "setup.py")
        setup_runner = os.path.join(self.caminho_projeto, "runner", "setup.py")
        
        # Verificar se existe setup.py problemático em runner/
        if os.path.exists(setup_runner):
            print("⚠️  Encontrado setup.py em runner/ - isso pode causar conflitos")
            if self.perguntar_usuario("Remover setup.py da pasta runner?"):
                if not self.criar_backup():
                    return
                try:
                    os.remove(setup_runner)
                    print("✅ Removido setup.py da pasta runner")
                    self.correcoes_aplicadas.append("Removido setup.py conflitante da pasta runner")
                except Exception as e:
                    print(f"❌ Erro ao remover setup.py: {e}")
        
        # Criar ou corrigir setup.py principal
        setup_correto = self.gerar_setup_py_correto()
        
        if os.path.exists(setup_principal):
            # Verificar se precisa de correção
            with open(setup_principal, 'r', encoding='utf-8') as f:
                conteudo_atual = f.read()
            
            precisa_correcao = any([
                'py_modules=' in conteudo_atual,  # Uso incorreto de py_modules
                'main:main' in conteudo_atual,    # Entry points incorretos
                'find_packages()' not in conteudo_atual,  # Falta find_packages
                f'{self.nome_pacote}.runner.main:main' not in conteudo_atual  # Entry points não corrigidos
            ])
            
            if precisa_correcao:
                print("📋 setup.py precisa de correções para instalação pip")
                if self.perguntar_usuario("Corrigir setup.py?"):
                    if not self.criar_backup():
                        return
                    
                    with open(setup_principal, 'w', encoding='utf-8') as f:
                        f.write(setup_correto)
                    
                    print("✅ setup.py corrigido")
                    self.correcoes_aplicadas.append("setup.py corrigido para instalação pip")
            else:
                print("✅ setup.py já está correto")
        else:
            print("📋 setup.py não encontrado - criando novo")
            if self.perguntar_usuario("Criar setup.py correto?"):
                if not self.criar_backup():
                    return
                
                with open(setup_principal, 'w', encoding='utf-8') as f:
                    f.write(setup_correto)
                
                print("✅ setup.py criado")
                self.correcoes_aplicadas.append("setup.py criado para instalação pip")
    
    def gerar_setup_py_correto(self) -> str:
        """Gera conteúdo correto para setup.py."""
        return f'''#!/usr/bin/env python3
"""
Setup script para {self.nome_pacote}
Configurado para instalação via pip install -e
"""

from setuptools import setup, find_packages
import os

# Ler README se existir
long_description = "Ferramenta de análise de código COBOL com tecnologia de IA"
readme_path = os.path.join(os.path.dirname(__file__), "README.md")
if os.path.exists(readme_path):
    try:
        with open(readme_path, "r", encoding="utf-8") as fh:
            long_description = fh.read()
    except:
        pass

setup(
    name="cobol-to-docs",
    version="3.1.0",
    author="COBOL Analyzer Team",
    description="Ferramenta de análise de código COBOL com tecnologia de IA",
    long_description=long_description,
    long_description_content_type="text/markdown",
    
    # IMPORTANTE: Usar find_packages() para detectar automaticamente
    packages=find_packages(),
    
    # Entry points corrigidos para nova estrutura
    entry_points={{
        "console_scripts": [
            "cobol-to-docs={self.nome_pacote}.runner.main:main",
            "cobol-analyzer={self.nome_pacote}.runner.cli:main",
        ],
    }},
    
    # Incluir todos os arquivos necessários
    include_package_data=True,
    package_data={{
        "": ["*.txt", "*.md", "*.yml", "*.yaml", "*.json", "*.cfg"],
    }},
    
    # Dependências essenciais
    install_requires=[
        "pyyaml>=6.0",
        "requests>=2.28.0",
        "numpy>=1.21.0",
        "scikit-learn>=1.0.0",
        "jinja2>=3.0.0",
        "markdown>=3.3.0",
    ],
    
    # Metadados
    classifiers=[
        "Development Status :: 4 - Beta",
        "Intended Audience :: Developers",
        "Programming Language :: Python :: 3",
        "Programming Language :: Python :: 3.8",
        "Programming Language :: Python :: 3.9",
        "Programming Language :: Python :: 3.10",
        "Programming Language :: Python :: 3.11",
    ],
    python_requires=">=3.8",
    zip_safe=False,
)
'''
    
    def problema_2_arquivos_init(self):
        """Verifica e corrige arquivos __init__.py faltantes."""
        print("\n🔍 Verificando arquivos __init__.py...")
        
        arquivos_para_criar = []
        
        # __init__.py na raiz do pacote (CRÍTICO para pip install)
        init_raiz = os.path.join(self.caminho_projeto, "__init__.py")
        if not os.path.exists(init_raiz):
            arquivos_para_criar.append({
                "caminho": init_raiz,
                "relativo": f"{self.nome_pacote}/__init__.py",
                "conteudo": f'''# -*- coding: utf-8 -*-
"""
{self.nome_pacote} - Ferramenta de análise COBOL com IA
"""

__version__ = "3.1.0"
__author__ = "COBOL Analyzer Team"
__description__ = "Ferramenta de análise de código COBOL com tecnologia de IA"

# Importações principais para facilitar uso
try:
    from .runner.main import main as main_function
    from .runner.cli import main as cli_function
except ImportError:
    # Fallback se houver problemas de importação
    main_function = None
    cli_function = None

__all__ = ["__version__", "__author__", "__description__", "main_function", "cli_function"]
''',
                "prioridade": "CRÍTICA"
            })
        
        # __init__.py na pasta runner (IMPORTANTE para entry points)
        runner_init = os.path.join(self.caminho_projeto, "runner", "__init__.py")
        if not os.path.exists(runner_init):
            arquivos_para_criar.append({
                "caminho": runner_init,
                "relativo": f"{self.nome_pacote}/runner/__init__.py",
                "conteudo": '''# -*- coding: utf-8 -*-
"""
Runner module - Entry points para comandos globais
"""

# Importações dos pontos de entrada
try:
    from .main import main as main_entry
    from .cli import main as cli_entry
except ImportError as e:
    print(f"Aviso: Erro ao importar entry points: {e}")
    main_entry = None
    cli_entry = None

__all__ = ["main_entry", "cli_entry"]
''',
                "prioridade": "ALTA"
            })
        
        # __init__.py em src (se existir)
        src_init = os.path.join(self.caminho_projeto, "src", "__init__.py")
        if os.path.isdir(os.path.join(self.caminho_projeto, "src")) and not os.path.exists(src_init):
            arquivos_para_criar.append({
                "caminho": src_init,
                "relativo": f"{self.nome_pacote}/src/__init__.py",
                "conteudo": '# -*- coding: utf-8 -*-\n"""Código fonte principal"""\n',
                "prioridade": "MÉDIA"
            })
        
        # __init__.py em subdiretórios de src
        src_path = os.path.join(self.caminho_projeto, "src")
        if os.path.isdir(src_path):
            for raiz, dirs, arquivos in os.walk(src_path):
                dirs[:] = [d for d in dirs if not d.startswith('.') and d != '__pycache__']
                
                tem_python = any(f.endswith('.py') for f in arquivos)
                tem_init = '__init__.py' in arquivos
                
                if tem_python and not tem_init and raiz != src_path:  # Pular src/ já tratado acima
                    init_path = os.path.join(raiz, "__init__.py")
                    nome_modulo = os.path.basename(raiz)
                    arquivos_para_criar.append({
                        "caminho": init_path,
                        "relativo": os.path.relpath(init_path, self.caminho_base),
                        "conteudo": f'# -*- coding: utf-8 -*-\n"""{nome_modulo} module"""\n',
                        "prioridade": "BAIXA"
                    })
        
        if not arquivos_para_criar:
            print("✅ Todos os arquivos __init__.py necessários já existem")
            return
        
        print(f"📋 Encontrados {len(arquivos_para_criar)} arquivos __init__.py faltantes:")
        for arquivo in arquivos_para_criar:
            print(f"   {arquivo['prioridade']}: {arquivo['relativo']}")
        
        if self.perguntar_usuario("Criar todos os arquivos __init__.py?"):
            if not self.criar_backup():
                return
            
            for arquivo in arquivos_para_criar:
                try:
                    os.makedirs(os.path.dirname(arquivo["caminho"]), exist_ok=True)
                    with open(arquivo["caminho"], 'w', encoding='utf-8') as f:
                        f.write(arquivo["conteudo"])
                    
                    print(f"✅ Criado: {arquivo['relativo']}")
                    self.correcoes_aplicadas.append(f"Criado {arquivo['relativo']}")
                
                except Exception as e:
                    print(f"❌ Erro ao criar {arquivo['relativo']}: {e}")
    
    def problema_3_importacoes_principais(self):
        """Corrige importações nos arquivos principais."""
        print("\n🔍 Verificando importações nos arquivos principais...")
        
        arquivos_principais = [
            os.path.join(self.caminho_projeto, "runner", "main.py"),
            os.path.join(self.caminho_projeto, "runner", "cli.py"),
        ]
        
        arquivos_com_problemas = []
        
        for arquivo_path in arquivos_principais:
            if os.path.exists(arquivo_path):
                problemas = self.analisar_importacoes_arquivo(arquivo_path)
                if problemas["tem_problemas"]:
                    arquivos_com_problemas.append(problemas)
        
        if not arquivos_com_problemas:
            print("✅ Importações nos arquivos principais estão corretas")
            return
        
        print(f"📋 Encontrados problemas em {len(arquivos_com_problemas)} arquivos:")
        for arquivo in arquivos_com_problemas:
            print(f"   📄 {arquivo['arquivo']}")
            if arquivo.get("sys_path_issues"):
                print(f"      🚫 {len(arquivo['sys_path_issues'])} linhas sys.path")
            if arquivo.get("import_src_issues"):
                print(f"      🔄 {len(arquivo['import_src_issues'])} importações src.*")
        
        if self.perguntar_usuario("Corrigir importações nos arquivos principais?"):
            if not self.criar_backup():
                return
            
            for arquivo in arquivos_com_problemas:
                self.corrigir_importacoes_arquivo(arquivo)
    
    def analisar_importacoes_arquivo(self, caminho_arquivo: str) -> Dict[str, Any]:
        """Analisa importações de um arquivo específico."""
        resultado = {
            "arquivo": os.path.relpath(caminho_arquivo, self.caminho_base),
            "caminho": caminho_arquivo,
            "tem_problemas": False,
            "sys_path_issues": [],
            "import_src_issues": []
        }
        
        try:
            with open(caminho_arquivo, 'r', encoding='utf-8') as f:
                linhas = f.readlines()
            
            for i, linha in enumerate(linhas):
                linha_strip = linha.strip()
                
                # sys.path issues (crítico para pip install)
                if re.search(r'sys\.path\.(insert|append)', linha_strip):
                    resultado["sys_path_issues"].append({
                        "linha": i,
                        "conteudo": linha,
                        "conteudo_strip": linha_strip
                    })
                    resultado["tem_problemas"] = True
                
                # src.* imports (precisa corrigir para nova estrutura)
                if re.match(r'^\s*(from\s+src\.|import\s+src\.)', linha_strip):
                    nova_linha = linha.replace('src.', f'{self.nome_pacote}.src.')
                    resultado["import_src_issues"].append({
                        "linha": i,
                        "original": linha,
                        "corrigido": nova_linha
                    })
                    resultado["tem_problemas"] = True
        
        except Exception as e:
            resultado["erro"] = str(e)
            resultado["tem_problemas"] = True
        
        return resultado
    
    def corrigir_importacoes_arquivo(self, arquivo_info: Dict[str, Any]):
        """Corrige importações de um arquivo."""
        try:
            with open(arquivo_info["caminho"], 'r', encoding='utf-8') as f:
                linhas = f.readlines()
            
            linhas_corrigidas = linhas.copy()
            modificacoes = 0
            
            # Corrigir sys.path issues (REMOVER completamente)
            for issue in reversed(arquivo_info["sys_path_issues"]):  # Reverso para não afetar índices
                linha_idx = issue["linha"]
                # Comentar a linha problemática
                linhas_corrigidas[linha_idx] = f"# REMOVIDO: {linhas_corrigidas[linha_idx].strip()}\n"
                modificacoes += 1
            
            # Corrigir src.* imports
            for issue in arquivo_info["import_src_issues"]:
                linha_idx = issue["linha"]
                linhas_corrigidas[linha_idx] = issue["corrigido"]
                modificacoes += 1
            
            if modificacoes > 0:
                with open(arquivo_info["caminho"], 'w', encoding='utf-8') as f:
                    f.writelines(linhas_corrigidas)
                
                print(f"✅ Corrigido: {arquivo_info['arquivo']} ({modificacoes} modificações)")
                self.correcoes_aplicadas.append(f"Corrigidas {modificacoes} importações em {arquivo_info['arquivo']}")
        
        except Exception as e:
            print(f"❌ Erro ao corrigir {arquivo_info['arquivo']}: {e}")
    
    def problema_4_testar_instalacao(self):
        """Testa se a instalação pip funcionará."""
        print("\n🧪 Testando configuração para instalação pip...")
        
        # Verificar se setup.py existe e está correto
        setup_path = os.path.join(self.caminho_projeto, "setup.py")
        if not os.path.exists(setup_path):
            print("❌ setup.py não encontrado")
            return
        
        # Verificar se __init__.py principal existe
        init_path = os.path.join(self.caminho_projeto, "__init__.py")
        if not os.path.exists(init_path):
            print("❌ __init__.py principal não encontrado")
            return
        
        # Verificar se find_packages funcionará
        try:
            from setuptools import find_packages
            
            # Simular find_packages no diretório do projeto
            old_cwd = os.getcwd()
            os.chdir(self.caminho_projeto)
            
            packages = find_packages()
            os.chdir(old_cwd)
            
            if packages:
                print(f"✅ find_packages() encontrou {len(packages)} pacotes:")
                for pkg in packages[:5]:  # Mostrar apenas os primeiros 5
                    print(f"   • {pkg}")
                if len(packages) > 5:
                    print(f"   ... e mais {len(packages) - 5} pacotes")
            else:
                print("⚠️  find_packages() não encontrou pacotes")
        
        except Exception as e:
            print(f"❌ Erro ao testar find_packages(): {e}")
        
        print("\n💡 COMANDOS DE TESTE RECOMENDADOS:")
        print(f"   1. cd {self.caminho_base}")
        print(f"   2. pip install -e ./{self.nome_pacote}/")
        print(f"   3. python -c \"import {self.nome_pacote}; print('OK')\"")
        print(f"   4. cobol-to-docs --help")
        print(f"   5. cobol-analyzer --help")
    
    def executar_correcoes(self, apenas_analise: bool = False):
        """Executa todas as correções."""
        print("🔧 CORRETOR INTELIGENTE V2 - FOCO EM INSTALAÇÃO PIP")
        print("=" * 65)
        print(f"📁 Projeto detectado: {self.nome_pacote}")
        print(f"📍 Localização: {self.caminho_projeto}")
        
        if apenas_analise:
            print("🔍 MODO: Apenas análise (sem correções)")
        elif self.modo_auto:
            print("🤖 MODO: Correção automática")
        else:
            print("🤝 MODO: Correção interativa")
        
        print("\n🎯 FOCO: Resolver erro 'pyproject.toml not found' e problemas de pip install")
        
        # Executar correções na ordem de prioridade
        if not apenas_analise:
            self.problema_1_setup_py_correto()  # MAIS IMPORTANTE
            self.problema_2_arquivos_init()     # CRÍTICO para pacotes
            self.problema_3_importacoes_principais()  # Necessário para funcionamento
        
        self.problema_4_testar_instalacao()  # Sempre executar teste
        
        # Relatório final
        print("\n" + "=" * 65)
        print("📋 RESUMO DAS CORREÇÕES")
        print("=" * 65)
        
        if self.correcoes_aplicadas:
            print(f"✅ {len(self.correcoes_aplicadas)} correções aplicadas:")
            for correcao in self.correcoes_aplicadas:
                print(f"   • {correcao}")
        else:
            if apenas_analise:
                print("ℹ️  Modo análise - nenhuma correção aplicada")
            else:
                print("ℹ️  Nenhuma correção foi necessária")
        
        if self.backup_criado:
            print(f"\n💾 Backup criado para segurança")
        
        print(f"\n🚀 PRÓXIMO PASSO:")
        print(f"   Execute: pip install -e ./{self.nome_pacote}/")
        print(f"   Se der erro, execute este script novamente")
        
        print(f"\n✅ Processo concluído!")

def main():
    """Função principal."""
    parser = argparse.ArgumentParser(description="Corretor Inteligente V2 - Foco em instalação pip")
    parser.add_argument("--auto", action="store_true", 
                       help="Modo automático (aplica todas as correções sem perguntar)")
    parser.add_argument("--apenas-analise", action="store_true",
                       help="Apenas análise, sem aplicar correções")
    
    args = parser.parse_args()
    
    corretor = CorretorInteligenteV2(modo_auto=args.auto)
    corretor.executar_correcoes(apenas_analise=args.apenas_analise)

if __name__ == "__main__":
    main()
