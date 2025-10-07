#!/usr/bin/env python3
"""
Analisador Personalizado para a Estrutura Atual do Projeto
Baseado na estrutura real vista na imagem fornecida pelo usuário.

Estrutura identificada:
- sbr-thpf-cobol-to-docs/ (projeto principal)
  - cobol_to_docs/ (pacote)
    - runner/
      - cli.py
      - cobol_to_docs.py  
      - main.py
      - setup.py
    - config/
    - data/
    - examples/
    - logs/
    - shell/
    - src/
    - teste_pacote/
    - tests/
  - setup.py (na raiz)

Uso:
    python analisador_estrutura_atual.py
"""

import os
import sys
import re
from pathlib import Path
from typing import List, Dict, Any

class AnalisadorEstruturaAtual:
    def __init__(self, caminho_base: str = "."):
        self.caminho_base = os.path.abspath(caminho_base)
        
        # Detectar automaticamente a estrutura
        self.detectar_estrutura()
        
        self.relatorio = {
            "estrutura_detectada": {},
            "problemas_criticos": [],
            "setup_py_analise": {},
            "arquivos_com_problemas": [],
            "diretorios_sem_init": [],
            "comandos_teste": [],
            "resumo_estatisticas": {}
        }
    
    def detectar_estrutura(self):
        """Detecta automaticamente a estrutura do projeto."""
        # Procurar pela pasta cobol_to_docs
        for item in os.listdir(self.caminho_base):
            caminho_item = os.path.join(self.caminho_base, item)
            if os.path.isdir(caminho_item) and item == "cobol_to_docs":
                self.caminho_projeto = caminho_item
                self.nome_pacote = "cobol_to_docs"
                break
        else:
            # Se não encontrar, procurar por qualquer pasta que contenha runner/
            for item in os.listdir(self.caminho_base):
                caminho_item = os.path.join(self.caminho_base, item)
                if os.path.isdir(caminho_item):
                    runner_path = os.path.join(caminho_item, "runner")
                    if os.path.isdir(runner_path):
                        self.caminho_projeto = caminho_item
                        self.nome_pacote = item
                        break
            else:
                self.caminho_projeto = None
                self.nome_pacote = None
    
    def analisar_estrutura_atual(self):
        """Analisa a estrutura atual baseada na imagem."""
        if not self.caminho_projeto:
            self.relatorio["problemas_criticos"].append(
                "❌ Não foi possível detectar a pasta do projeto cobol_to_docs"
            )
            return
        
        estrutura = {
            "projeto_encontrado": True,
            "caminho": self.caminho_projeto,
            "nome_pacote": self.nome_pacote,
            "diretorios_principais": {},
            "arquivos_principais": {},
            "setup_py_localizacoes": []
        }
        
        # Verificar diretórios principais
        diretorios_esperados = [
            "runner", "config", "data", "examples", "logs", "shell", "src", "tests"
        ]
        
        for diretorio in diretorios_esperados:
            caminho_dir = os.path.join(self.caminho_projeto, diretorio)
            estrutura["diretorios_principais"][diretorio] = {
                "existe": os.path.isdir(caminho_dir),
                "caminho": caminho_dir
            }
        
        # Verificar arquivos na pasta runner
        runner_path = os.path.join(self.caminho_projeto, "runner")
        if os.path.isdir(runner_path):
            arquivos_runner = ["main.py", "cli.py", "cobol_to_docs.py", "setup.py"]
            for arquivo in arquivos_runner:
                caminho_arquivo = os.path.join(runner_path, arquivo)
                estrutura["arquivos_principais"][f"runner/{arquivo}"] = {
                    "existe": os.path.exists(caminho_arquivo),
                    "caminho": caminho_arquivo
                }
        
        # Procurar por arquivos setup.py
        for raiz, dirs, arquivos in os.walk(self.caminho_projeto):
            if "setup.py" in arquivos:
                setup_path = os.path.join(raiz, "setup.py")
                estrutura["setup_py_localizacoes"].append({
                    "caminho": setup_path,
                    "relativo": os.path.relpath(setup_path, self.caminho_base),
                    "na_raiz_pacote": raiz == self.caminho_projeto
                })
        
        # Verificar setup.py na raiz do projeto principal
        setup_raiz = os.path.join(self.caminho_base, "setup.py")
        if os.path.exists(setup_raiz):
            estrutura["setup_py_localizacoes"].append({
                "caminho": setup_raiz,
                "relativo": "setup.py",
                "na_raiz_projeto": True
            })
        
        self.relatorio["estrutura_detectada"] = estrutura
    
    def analisar_setup_py_multiplos(self):
        """Analisa múltiplos arquivos setup.py encontrados."""
        setup_analises = []
        
        for setup_info in self.relatorio["estrutura_detectada"].get("setup_py_localizacoes", []):
            setup_path = setup_info["caminho"]
            
            try:
                with open(setup_path, 'r', encoding='utf-8') as f:
                    conteudo = f.read()
                
                analise = {
                    "arquivo": setup_info["relativo"],
                    "caminho": setup_path,
                    "entry_points": [],
                    "problemas": [],
                    "recomendacoes": []
                }
                
                # Procurar por entry_points
                if "entry_points" in conteudo:
                    # Extrair entry points usando regex
                    entry_pattern = r'"([^"]+)=([^"]+)"'
                    matches = re.findall(entry_pattern, conteudo)
                    
                    for comando, modulo_func in matches:
                        analise["entry_points"].append({
                            "comando": comando,
                            "modulo": modulo_func,
                            "linha_original": f'"{comando}={modulo_func}"'
                        })
                        
                        # Verificar se precisa de correção
                        if modulo_func in ["main:main", "cli:main"]:
                            analise["problemas"].append(
                                f"Entry point '{comando}' aponta para '{modulo_func}' "
                                f"mas deveria ser '{self.nome_pacote}.runner.{modulo_func}'"
                            )
                            analise["recomendacoes"].append(
                                f'"{comando}={self.nome_pacote}.runner.{modulo_func}"'
                            )
                
                # Verificar se é o setup.py principal (deve estar na raiz do pacote)
                if setup_info.get("na_raiz_pacote", False):
                    analise["e_principal"] = True
                    if not analise["entry_points"]:
                        analise["problemas"].append(
                            "Setup.py principal não tem entry_points definidos"
                        )
                elif setup_info.get("na_raiz_projeto", False):
                    analise["e_raiz_projeto"] = True
                    analise["problemas"].append(
                        "Setup.py na raiz do projeto pode causar conflitos. "
                        "Considere usar apenas o setup.py dentro do pacote cobol_to_docs"
                    )
                
                setup_analises.append(analise)
                
            except Exception as e:
                setup_analises.append({
                    "arquivo": setup_info["relativo"],
                    "erro": f"Erro ao analisar: {e}"
                })
        
        self.relatorio["setup_py_analise"] = {
            "total_encontrados": len(setup_analises),
            "analises": setup_analises
        }
    
    def verificar_arquivos_init(self):
        """Verifica arquivos __init__.py necessários."""
        diretorios_precisam_init = []
        
        # Verificar raiz do pacote
        init_raiz = os.path.join(self.caminho_projeto, "__init__.py")
        if not os.path.exists(init_raiz):
            diretorios_precisam_init.append({
                "diretorio": self.nome_pacote,
                "caminho": init_raiz,
                "prioridade": "CRÍTICA",
                "motivo": "Necessário para que o Python reconheça como pacote instalável"
            })
        
        # Verificar pasta runner
        runner_init = os.path.join(self.caminho_projeto, "runner", "__init__.py")
        if not os.path.exists(runner_init):
            diretorios_precisam_init.append({
                "diretorio": f"{self.nome_pacote}/runner",
                "caminho": runner_init,
                "prioridade": "ALTA",
                "motivo": "Necessário para importar main.py e cli.py como módulos"
            })
        
        # Verificar src e subdiretórios
        src_path = os.path.join(self.caminho_projeto, "src")
        if os.path.isdir(src_path):
            for raiz, dirs, arquivos in os.walk(src_path):
                dirs[:] = [d for d in dirs if not d.startswith('.') and d != '__pycache__']
                
                tem_python = any(f.endswith('.py') for f in arquivos)
                tem_init = '__init__.py' in arquivos
                
                if tem_python and not tem_init:
                    init_path = os.path.join(raiz, "__init__.py")
                    diretorios_precisam_init.append({
                        "diretorio": os.path.relpath(raiz, self.caminho_base),
                        "caminho": init_path,
                        "prioridade": "MÉDIA",
                        "motivo": "Necessário para importações internas funcionarem"
                    })
        
        self.relatorio["diretorios_sem_init"] = diretorios_precisam_init
    
    def analisar_arquivos_python_principais(self):
        """Analisa os arquivos Python principais."""
        arquivos_principais = [
            os.path.join(self.caminho_projeto, "runner", "main.py"),
            os.path.join(self.caminho_projeto, "runner", "cli.py"),
            os.path.join(self.caminho_projeto, "runner", "cobol_to_docs.py"),
        ]
        
        problemas_encontrados = []
        total_arquivos = 0
        
        for arquivo_path in arquivos_principais:
            if os.path.exists(arquivo_path):
                total_arquivos += 1
                problemas = self.analisar_arquivo_individual(arquivo_path)
                if problemas["tem_problemas"]:
                    problemas_encontrados.append(problemas)
        
        self.relatorio["arquivos_com_problemas"] = problemas_encontrados
        self.relatorio["resumo_estatisticas"] = {
            "arquivos_principais_analisados": total_arquivos,
            "arquivos_com_problemas": len(problemas_encontrados)
        }
    
    def analisar_arquivo_individual(self, caminho_arquivo: str) -> Dict[str, Any]:
        """Analisa um arquivo Python individual."""
        nome_arquivo = os.path.relpath(caminho_arquivo, self.caminho_base)
        
        resultado = {
            "arquivo": nome_arquivo,
            "tem_problemas": False,
            "sys_path_issues": [],
            "import_issues": [],
            "tem_funcao_main": False
        }
        
        try:
            with open(caminho_arquivo, 'r', encoding='utf-8') as f:
                linhas = f.readlines()
            
            for i, linha in enumerate(linhas, 1):
                linha_strip = linha.strip()
                
                # Detectar sys.path manipulation
                if re.search(r'sys\.path\.(insert|append)', linha_strip):
                    resultado["sys_path_issues"].append({
                        "linha": i,
                        "codigo": linha_strip
                    })
                    resultado["tem_problemas"] = True
                
                # Detectar importações problemáticas
                if re.match(r'^\s*(from\s+src\.|import\s+src\.)', linha_strip):
                    resultado["import_issues"].append({
                        "linha": i,
                        "tipo": "src_import",
                        "original": linha_strip,
                        "sugestao": linha_strip.replace('src.', f'{self.nome_pacote}.src.')
                    })
                    resultado["tem_problemas"] = True
                
                # Detectar importações relativas
                if re.match(r'^\s*from\s+\.', linha_strip):
                    resultado["import_issues"].append({
                        "linha": i,
                        "tipo": "relative_import",
                        "original": linha_strip,
                        "sugestao": f"Converter para importação absoluta usando {self.nome_pacote}"
                    })
                    resultado["tem_problemas"] = True
                
                # Detectar função main
                if re.match(r'^\s*def\s+main\s*\(', linha_strip):
                    resultado["tem_funcao_main"] = True
        
        except Exception as e:
            resultado["erro"] = f"Erro ao ler arquivo: {e}"
            resultado["tem_problemas"] = True
        
        return resultado
    
    def gerar_comandos_teste(self):
        """Gera comandos de teste específicos para a estrutura atual."""
        comandos = []
        
        # Comandos de instalação
        comandos.append({
            "categoria": "Instalação",
            "comandos": [
                f"cd {self.caminho_base}",
                f"pip install -e ./{self.nome_pacote}/",
                "# Verificar se a instalação funcionou:",
                "pip list | grep cobol"
            ]
        })
        
        # Comandos de teste direto
        comandos.append({
            "categoria": "Execução Direta",
            "comandos": [
                f"python -m {self.nome_pacote}.runner.main --help",
                f"python -m {self.nome_pacote}.runner.cli --help"
            ]
        })
        
        # Comandos globais (se entry points estiverem corretos)
        setup_analise = self.relatorio.get("setup_py_analise", {})
        if setup_analise.get("analises"):
            for analise in setup_analise["analises"]:
                if analise.get("entry_points"):
                    comandos.append({
                        "categoria": "Comandos Globais",
                        "comandos": [f"{ep['comando']} --help" for ep in analise["entry_points"]]
                    })
                    break
        
        self.relatorio["comandos_teste"] = comandos
    
    def gerar_relatorio_completo(self):
        """Gera relatório completo da análise."""
        print("=" * 80)
        print("📋 ANÁLISE DA ESTRUTURA ATUAL DO PROJETO")
        print("=" * 80)
        
        # Estrutura detectada
        estrutura = self.relatorio["estrutura_detectada"]
        if estrutura.get("projeto_encontrado"):
            print(f"\n✅ Projeto detectado: {estrutura['nome_pacote']}")
            print(f"📍 Localização: {estrutura['caminho']}")
            
            print(f"\n📁 ESTRUTURA DE DIRETÓRIOS:")
            for nome, info in estrutura["diretorios_principais"].items():
                status = "✅" if info["existe"] else "❌"
                print(f"   {status} {nome}/")
            
            print(f"\n📄 ARQUIVOS PRINCIPAIS:")
            for nome, info in estrutura["arquivos_principais"].items():
                status = "✅" if info["existe"] else "❌"
                print(f"   {status} {nome}")
        
        # Análise de setup.py
        setup_analise = self.relatorio["setup_py_analise"]
        print(f"\n🔧 ANÁLISE DE SETUP.PY ({setup_analise.get('total_encontrados', 0)} encontrados):")
        
        for analise in setup_analise.get("analises", []):
            print(f"\n   📄 {analise['arquivo']}:")
            
            if analise.get("entry_points"):
                print("      🎯 Entry Points:")
                for ep in analise["entry_points"]:
                    print(f"         • {ep['comando']} -> {ep['modulo']}")
            
            if analise.get("problemas"):
                print("      🚨 Problemas:")
                for problema in analise["problemas"]:
                    print(f"         • {problema}")
            
            if analise.get("recomendacoes"):
                print("      💡 Recomendações:")
                for rec in analise["recomendacoes"]:
                    print(f"         • {rec}")
        
        # Arquivos __init__.py
        init_issues = self.relatorio["diretorios_sem_init"]
        if init_issues:
            print(f"\n🚨 ARQUIVOS __init__.py NECESSÁRIOS ({len(init_issues)}):")
            for issue in init_issues:
                print(f"   {issue['prioridade']}: {issue['diretorio']}/__init__.py")
                print(f"      Motivo: {issue['motivo']}")
        
        # Problemas em arquivos Python
        problemas = self.relatorio["arquivos_com_problemas"]
        if problemas:
            print(f"\n🔧 PROBLEMAS EM ARQUIVOS PYTHON ({len(problemas)}):")
            for problema in problemas:
                print(f"\n   📄 {problema['arquivo']}:")
                
                if problema.get("sys_path_issues"):
                    print("      🚫 Manipulação de sys.path:")
                    for issue in problema["sys_path_issues"]:
                        print(f"         Linha {issue['linha']}: {issue['codigo']}")
                
                if problema.get("import_issues"):
                    print("      🔄 Problemas de importação:")
                    for issue in problema["import_issues"]:
                        print(f"         Linha {issue['linha']} ({issue['tipo']}):")
                        print(f"           ❌ {issue['original']}")
                        print(f"           ✅ {issue['sugestao']}")
        
        # Comandos de teste
        print(f"\n🧪 COMANDOS DE TESTE RECOMENDADOS:")
        for categoria in self.relatorio["comandos_teste"]:
            print(f"\n   {categoria['categoria']}:")
            for comando in categoria["comandos"]:
                if comando.startswith("#"):
                    print(f"   {comando}")
                else:
                    print(f"   $ {comando}")
        
        # Resumo e próximos passos
        print(f"\n" + "=" * 80)
        print("📝 PRÓXIMOS PASSOS RECOMENDADOS:")
        print("=" * 80)
        
        print("\n1️⃣ CRIAR ARQUIVOS __init__.py:")
        for issue in init_issues:
            print(f"   touch {issue['caminho']}")
        
        print("\n2️⃣ CORRIGIR SETUP.PY:")
        for analise in setup_analise.get("analises", []):
            if analise.get("recomendacoes"):
                print(f"   Arquivo: {analise['arquivo']}")
                for rec in analise["recomendacoes"]:
                    print(f"   Atualizar entry_point para: {rec}")
        
        print("\n3️⃣ CORRIGIR IMPORTAÇÕES:")
        print("   Use o corretor automático ou corrija manualmente:")
        print("   • Remover linhas sys.path.insert/append")
        print(f"   • Substituir 'from src.' por 'from {self.nome_pacote}.src.'")
        print("   • Converter importações relativas para absolutas")
        
        print("\n4️⃣ TESTAR:")
        print("   Execute os comandos de teste listados acima")
        
        if not any([init_issues, problemas, self.relatorio["problemas_criticos"]]):
            print(f"\n🎉 ESTRUTURA PARECE BOA!")
            print("   Poucos ou nenhum problema crítico encontrado.")
    
    def executar_analise(self):
        """Executa análise completa."""
        print("🔍 Analisando estrutura atual do projeto...")
        
        self.analisar_estrutura_atual()
        
        if self.relatorio["problemas_criticos"]:
            print("\n❌ PROBLEMAS CRÍTICOS ENCONTRADOS:")
            for problema in self.relatorio["problemas_criticos"]:
                print(f"   {problema}")
            return False
        
        print("🔧 Analisando arquivos setup.py...")
        self.analisar_setup_py_multiplos()
        
        print("📁 Verificando arquivos __init__.py...")
        self.verificar_arquivos_init()
        
        print("📄 Analisando arquivos Python principais...")
        self.analisar_arquivos_python_principais()
        
        print("🧪 Gerando comandos de teste...")
        self.gerar_comandos_teste()
        
        print("📋 Gerando relatório...")
        self.gerar_relatorio_completo()
        
        return True

def main():
    """Função principal."""
    print("🔍 Analisador de Estrutura Atual - Projeto COBOL_ANALYZER")
    print("Baseado na estrutura real vista na imagem fornecida")
    print("-" * 60)
    
    analisador = AnalisadorEstruturaAtual()
    sucesso = analisador.executar_analise()
    
    if not sucesso:
        print("\n❌ Análise não pôde ser concluída.")
        sys.exit(1)
    
    print(f"\n✅ Análise concluída!")

if __name__ == "__main__":
    main()
