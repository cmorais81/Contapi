#!/usr/bin/env python3
"""
Corretor Automático para Projeto COBOL_ANALYZER
Aplica automaticamente as correções mais comuns identificadas pelo analisador.

ATENÇÃO: Este script modifica arquivos. Faça backup antes de usar!

Uso:
    python corretor_automatico.py [--dry-run]
    
    --dry-run: Mostra o que seria feito sem modificar arquivos
"""

import os
import sys
import re
import shutil
from pathlib import Path
from typing import List, Dict, Any
import argparse

class CorretorAutomatico:
    def __init__(self, caminho_base: str, nome_pacote: str, dry_run: bool = False):
        self.caminho_base = os.path.abspath(caminho_base)
        self.nome_pacote = nome_pacote
        self.caminho_projeto = os.path.join(self.caminho_base, nome_pacote)
        self.dry_run = dry_run
        
        self.relatorio_correcoes = {
            "arquivos_init_criados": [],
            "arquivos_modificados": [],
            "setup_py_corrigido": False,
            "erros": []
        }
    
    def criar_backup(self):
        """Cria backup do projeto antes das modificações."""
        if self.dry_run:
            print("🔄 [DRY-RUN] Backup seria criado")
            return True
        
        backup_dir = f"{self.caminho_projeto}_backup_{int(time.time())}"
        try:
            shutil.copytree(self.caminho_projeto, backup_dir)
            print(f"✅ Backup criado em: {backup_dir}")
            return True
        except Exception as e:
            print(f"❌ Erro ao criar backup: {e}")
            return False
    
    def criar_arquivos_init(self):
        """Cria arquivos __init__.py necessários."""
        diretorios_para_init = [
            self.caminho_projeto,  # cobol_to_docs/__init__.py
            os.path.join(self.caminho_projeto, "runner"),  # cobol_to_docs/runner/__init__.py
        ]
        
        # Adicionar todos os diretórios src que contêm Python
        for raiz, dirs, arquivos in os.walk(os.path.join(self.caminho_projeto, "src")):
            dirs[:] = [d for d in dirs if not d.startswith('.') and d != '__pycache__']
            
            tem_python = any(f.endswith('.py') for f in arquivos)
            tem_init = '__init__.py' in arquivos
            
            if tem_python and not tem_init:
                diretorios_para_init.append(raiz)
        
        for diretorio in diretorios_para_init:
            init_path = os.path.join(diretorio, "__init__.py")
            
            if not os.path.exists(init_path):
                if self.dry_run:
                    print(f"🔄 [DRY-RUN] Criaria: {os.path.relpath(init_path, self.caminho_base)}")
                else:
                    try:
                        os.makedirs(diretorio, exist_ok=True)
                        with open(init_path, 'w', encoding='utf-8') as f:
                            f.write('# -*- coding: utf-8 -*-\n')
                            f.write(f'"""{os.path.basename(diretorio)} module"""\n')
                        
                        self.relatorio_correcoes["arquivos_init_criados"].append(
                            os.path.relpath(init_path, self.caminho_base)
                        )
                        print(f"✅ Criado: {os.path.relpath(init_path, self.caminho_base)}")
                    except Exception as e:
                        erro = f"Erro ao criar {init_path}: {e}"
                        self.relatorio_correcoes["erros"].append(erro)
                        print(f"❌ {erro}")
    
    def corrigir_setup_py(self):
        """Corrige os entry points no setup.py."""
        setup_path = os.path.join(self.caminho_projeto, "setup.py")
        
        if not os.path.exists(setup_path):
            print("⚠️  setup.py não encontrado")
            return
        
        try:
            with open(setup_path, 'r', encoding='utf-8') as f:
                conteudo = f.read()
            
            # Corrigir entry points
            conteudo_original = conteudo
            
            # Substituir entry points antigos pelos novos
            patterns = [
                (r'"cobol-to-docs=main:main"', f'"cobol-to-docs={self.nome_pacote}.runner.main:main"'),
                (r'"cobol-analyzer=cli:main"', f'"cobol-analyzer={self.nome_pacote}.runner.cli:main"'),
                (r"'cobol-to-docs=main:main'", f"'cobol-to-docs={self.nome_pacote}.runner.main:main'"),
                (r"'cobol-analyzer=cli:main'", f"'cobol-analyzer={self.nome_pacote}.runner.cli:main'"),
            ]
            
            for pattern, replacement in patterns:
                conteudo = re.sub(pattern, replacement, conteudo)
            
            # Corrigir py_modules para packages
            if 'py_modules=["main", "cli", "cobol_to_docs"]' in conteudo:
                conteudo = conteudo.replace(
                    'py_modules=["main", "cli", "cobol_to_docs"]',
                    f'packages=find_packages()'
                )
                
                # Adicionar import se necessário
                if 'from setuptools import setup, find_packages' not in conteudo:
                    conteudo = conteudo.replace(
                        'from setuptools import setup',
                        'from setuptools import setup, find_packages'
                    )
            
            if conteudo != conteudo_original:
                if self.dry_run:
                    print("🔄 [DRY-RUN] setup.py seria corrigido")
                    print("   Entry points seriam atualizados para usar a nova estrutura")
                else:
                    with open(setup_path, 'w', encoding='utf-8') as f:
                        f.write(conteudo)
                    
                    self.relatorio_correcoes["setup_py_corrigido"] = True
                    print("✅ setup.py corrigido")
            else:
                print("ℹ️  setup.py já está correto")
                
        except Exception as e:
            erro = f"Erro ao corrigir setup.py: {e}"
            self.relatorio_correcoes["erros"].append(erro)
            print(f"❌ {erro}")
    
    def corrigir_arquivo_python(self, caminho_arquivo: str):
        """Corrige importações em um arquivo Python específico."""
        try:
            with open(caminho_arquivo, 'r', encoding='utf-8') as f:
                linhas = f.readlines()
            
            linhas_modificadas = []
            modificado = False
            
            for linha in linhas:
                linha_original = linha
                
                # Remover manipulação de sys.path
                if re.search(r'sys\.path\.(insert|append)', linha):
                    # Comentar a linha em vez de remover
                    linha = f"# REMOVIDO: {linha.strip()}\n"
                    modificado = True
                
                # Corrigir importações src.*
                elif re.match(r'^\s*(from\s+src\.|import\s+src\.)', linha.strip()):
                    linha = linha.replace('src.', f'{self.nome_pacote}.src.')
                    modificado = True
                
                # Corrigir importações relativas (casos simples)
                elif re.match(r'^\s*from\s+\.', linha.strip()):
                    # Calcular caminho baseado na localização do arquivo
                    dir_arquivo = os.path.dirname(os.path.relpath(caminho_arquivo, self.caminho_base))
                    if dir_arquivo and dir_arquivo != '.':
                        partes_caminho = dir_arquivo.replace(os.sep, '.')
                        linha = linha.replace('from .', f'from {partes_caminho}.')
                        modificado = True
                
                linhas_modificadas.append(linha)
            
            if modificado:
                if self.dry_run:
                    caminho_relativo = os.path.relpath(caminho_arquivo, self.caminho_base)
                    print(f"🔄 [DRY-RUN] Seria modificado: {caminho_relativo}")
                else:
                    with open(caminho_arquivo, 'w', encoding='utf-8') as f:
                        f.writelines(linhas_modificadas)
                    
                    caminho_relativo = os.path.relpath(caminho_arquivo, self.caminho_base)
                    self.relatorio_correcoes["arquivos_modificados"].append(caminho_relativo)
                    print(f"✅ Corrigido: {caminho_relativo}")
        
        except Exception as e:
            erro = f"Erro ao corrigir {caminho_arquivo}: {e}"
            self.relatorio_correcoes["erros"].append(erro)
            print(f"❌ {erro}")
    
    def corrigir_todos_arquivos(self):
        """Corrige todos os arquivos Python do projeto."""
        print("📄 Corrigindo arquivos Python...")
        
        # Focar nos arquivos principais primeiro
        arquivos_prioritarios = [
            os.path.join(self.caminho_projeto, "runner", "main.py"),
            os.path.join(self.caminho_projeto, "runner", "cli.py"),
            os.path.join(self.caminho_projeto, "cobol_to_docs.py"),
        ]
        
        for arquivo in arquivos_prioritarios:
            if os.path.exists(arquivo):
                self.corrigir_arquivo_python(arquivo)
        
        # Depois corrigir outros arquivos
        for raiz, dirs, arquivos in os.walk(self.caminho_projeto):
            dirs[:] = [d for d in dirs if not d.startswith('.') and d != '__pycache__' and d != 'old']
            
            for arquivo in arquivos:
                if arquivo.endswith('.py'):
                    caminho_completo = os.path.join(raiz, arquivo)
                    
                    # Pular arquivos já processados
                    if caminho_completo not in arquivos_prioritarios:
                        self.corrigir_arquivo_python(caminho_completo)
    
    def gerar_relatorio_final(self):
        """Gera relatório final das correções aplicadas."""
        print("\n" + "="*70)
        print("📋 RELATÓRIO DE CORREÇÕES APLICADAS")
        print("="*70)
        
        if self.dry_run:
            print("🔄 MODO DRY-RUN - Nenhuma modificação foi feita")
        
        print(f"\n✅ Arquivos __init__.py criados: {len(self.relatorio_correcoes['arquivos_init_criados'])}")
        for arquivo in self.relatorio_correcoes["arquivos_init_criados"]:
            print(f"   • {arquivo}")
        
        print(f"\n✅ Arquivos Python corrigidos: {len(self.relatorio_correcoes['arquivos_modificados'])}")
        for arquivo in self.relatorio_correcoes["arquivos_modificados"][:10]:  # Mostrar apenas os primeiros 10
            print(f"   • {arquivo}")
        if len(self.relatorio_correcoes["arquivos_modificados"]) > 10:
            print(f"   ... e mais {len(self.relatorio_correcoes['arquivos_modificados']) - 10} arquivos")
        
        if self.relatorio_correcoes["setup_py_corrigido"]:
            print(f"\n✅ setup.py corrigido")
        
        if self.relatorio_correcoes["erros"]:
            print(f"\n❌ Erros encontrados: {len(self.relatorio_correcoes['erros'])}")
            for erro in self.relatorio_correcoes["erros"]:
                print(f"   • {erro}")
        
        print("\n" + "="*70)
        print("📝 PRÓXIMOS PASSOS:")
        print("="*70)
        
        if not self.dry_run:
            print("\n1️⃣ Testar a instalação:")
            print(f"   cd {self.caminho_base}")
            print(f"   pip install -e ./{self.nome_pacote}/")
            
            print("\n2️⃣ Testar comandos globais:")
            print("   cobol-to-docs --help")
            print("   cobol-analyzer --help")
            
            print("\n3️⃣ Testar execução direta:")
            print(f"   python -m {self.nome_pacote}.runner.main --help")
            print(f"   python -m {self.nome_pacote}.runner.cli --help")
            
            print("\n4️⃣ Se houver problemas:")
            print("   • Execute o analisador novamente para verificar problemas restantes")
            print("   • Verifique os logs de erro acima")
            print("   • Restaure do backup se necessário")
        else:
            print("\n1️⃣ Para aplicar as correções:")
            print("   python corretor_automatico.py")
            
            print("\n2️⃣ Para análise detalhada:")
            print("   python analisador_projeto_cobol_completo.py")
    
    def executar_correcoes(self):
        """Executa todas as correções."""
        print("🔧 Iniciando correções automáticas...")
        
        if not os.path.isdir(self.caminho_projeto):
            print(f"❌ Projeto não encontrado: {self.caminho_projeto}")
            return False
        
        if not self.dry_run:
            print("💾 Criando backup...")
            if not self.criar_backup():
                print("❌ Falha ao criar backup. Abortando.")
                return False
        
        print("📁 Criando arquivos __init__.py...")
        self.criar_arquivos_init()
        
        print("🔧 Corrigindo setup.py...")
        self.corrigir_setup_py()
        
        print("📄 Corrigindo importações...")
        self.corrigir_todos_arquivos()
        
        self.gerar_relatorio_final()
        
        return True

def main():
    """Função principal do corretor."""
    parser = argparse.ArgumentParser(description="Corretor automático para projeto COBOL_ANALYZER")
    parser.add_argument("--dry-run", action="store_true", 
                       help="Mostra o que seria feito sem modificar arquivos")
    
    args = parser.parse_args()
    
    # --- CONFIGURAÇÃO ---
    CAMINHO_BASE = "."
    NOME_PACOTE_PROJETO = "cobol_to_docs"
    
    # --- EXECUÇÃO ---
    import time  # Importar aqui para evitar erro se não usado
    
    corretor = CorretorAutomatico(CAMINHO_BASE, NOME_PACOTE_PROJETO, args.dry_run)
    sucesso = corretor.executar_correcoes()
    
    if not sucesso:
        print("\n❌ Correções não puderam ser aplicadas.")
        sys.exit(1)
    
    if args.dry_run:
        print(f"\n✅ Análise de correções concluída! Use sem --dry-run para aplicar.")
    else:
        print(f"\n✅ Correções aplicadas! Teste o projeto conforme instruções acima.")

if __name__ == "__main__":
    main()
