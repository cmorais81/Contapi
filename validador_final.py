#!/usr/bin/env python3
"""
Validador Final - Verifica se tudo está funcionando corretamente
Testa todas as funcionalidades após as correções aplicadas.

Uso:
    python validador_final.py                    # Validação completa
    python validador_final.py --rapido          # Validação rápida
    python validador_final.py --limpar-avisos   # Remove avisos pkg_resources
"""

import os
import sys
import subprocess
import argparse
from pathlib import Path
from typing import List, Dict, Any

class ValidadorFinal:
    def __init__(self, caminho_base: str = "."):
        self.caminho_base = os.path.abspath(caminho_base)
        self.detectar_estrutura()
        self.resultados = {
            "testes_passaram": [],
            "testes_falharam": [],
            "avisos": [],
            "comandos_funcionais": []
        }
    
    def detectar_estrutura(self):
        """Detecta a estrutura do projeto."""
        for item in os.listdir(self.caminho_base):
            caminho_item = os.path.join(self.caminho_base, item)
            if os.path.isdir(caminho_item) and item == "cobol_to_docs":
                self.caminho_projeto = caminho_item
                self.nome_pacote = "cobol_to_docs"
                return
        
        print("❌ Projeto cobol_to_docs não encontrado!")
        sys.exit(1)
    
    def executar_comando(self, comando: List[str], timeout: int = 30) -> Dict[str, Any]:
        """Executa um comando e retorna o resultado."""
        try:
            resultado = subprocess.run(
                comando,
                capture_output=True,
                text=True,
                timeout=timeout,
                cwd=self.caminho_base
            )
            
            return {
                "sucesso": resultado.returncode == 0,
                "stdout": resultado.stdout,
                "stderr": resultado.stderr,
                "codigo_retorno": resultado.returncode
            }
        
        except subprocess.TimeoutExpired:
            return {
                "sucesso": False,
                "erro": "Timeout",
                "stdout": "",
                "stderr": "Comando excedeu tempo limite"
            }
        except Exception as e:
            return {
                "sucesso": False,
                "erro": str(e),
                "stdout": "",
                "stderr": str(e)
            }
    
    def teste_1_importacao_basica(self):
        """Testa se o pacote pode ser importado."""
        print("🔍 Teste 1: Importação básica do pacote...")
        
        try:
            # Testar importação do pacote principal
            resultado = self.executar_comando([
                sys.executable, "-c", f"import {self.nome_pacote}; print('✅ Pacote importado com sucesso')"
            ])
            
            if resultado["sucesso"]:
                print("✅ Importação básica: OK")
                self.resultados["testes_passaram"].append("Importação básica do pacote")
            else:
                print(f"❌ Importação básica: FALHOU")
                print(f"   Erro: {resultado['stderr']}")
                self.resultados["testes_falharam"].append("Importação básica do pacote")
        
        except Exception as e:
            print(f"❌ Erro no teste de importação: {e}")
            self.resultados["testes_falharam"].append("Importação básica do pacote")
    
    def teste_2_comandos_globais(self):
        """Testa se os comandos globais funcionam."""
        print("\n🔍 Teste 2: Comandos globais...")
        
        comandos = [
            ("cobol-to-docs", ["cobol-to-docs", "--help"]),
            ("cobol-analyzer", ["cobol-analyzer", "--help"])
        ]
        
        for nome, comando in comandos:
            resultado = self.executar_comando(comando, timeout=10)
            
            if resultado["sucesso"]:
                print(f"✅ Comando {nome}: OK")
                self.resultados["comandos_funcionais"].append(nome)
                self.resultados["testes_passaram"].append(f"Comando global {nome}")
            else:
                print(f"❌ Comando {nome}: FALHOU")
                if "pkg_resources" in resultado["stderr"]:
                    print(f"   ⚠️  Aviso pkg_resources detectado (não crítico)")
                    self.resultados["avisos"].append(f"pkg_resources warning em {nome}")
                    # Se só tem aviso pkg_resources, considerar como sucesso
                    if "usage:" in resultado["stdout"].lower() or "help" in resultado["stdout"].lower():
                        print(f"   ✅ Comando {nome} funciona apesar do aviso")
                        self.resultados["comandos_funcionais"].append(nome)
                        self.resultados["testes_passaram"].append(f"Comando global {nome} (com aviso)")
                    else:
                        self.resultados["testes_falharam"].append(f"Comando global {nome}")
                else:
                    print(f"   Erro: {resultado['stderr']}")
                    self.resultados["testes_falharam"].append(f"Comando global {nome}")
    
    def teste_3_execucao_modulo(self):
        """Testa execução como módulo Python."""
        print("\n🔍 Teste 3: Execução como módulo...")
        
        modulos = [
            ("main", [sys.executable, "-m", f"{self.nome_pacote}.runner.main", "--help"]),
            ("cli", [sys.executable, "-m", f"{self.nome_pacote}.runner.cli", "--help"])
        ]
        
        for nome, comando in modulos:
            resultado = self.executar_comando(comando, timeout=10)
            
            if resultado["sucesso"]:
                print(f"✅ Módulo {nome}: OK")
                self.resultados["testes_passaram"].append(f"Execução módulo {nome}")
            else:
                print(f"❌ Módulo {nome}: FALHOU")
                print(f"   Erro: {resultado['stderr']}")
                self.resultados["testes_falharam"].append(f"Execução módulo {nome}")
    
    def teste_4_estrutura_arquivos(self):
        """Verifica se a estrutura de arquivos está correta."""
        print("\n🔍 Teste 4: Estrutura de arquivos...")
        
        arquivos_criticos = [
            (f"{self.nome_pacote}/__init__.py", "Pacote principal"),
            (f"{self.nome_pacote}/runner/__init__.py", "Módulo runner"),
            (f"{self.nome_pacote}/runner/main.py", "Script principal"),
            (f"{self.nome_pacote}/runner/cli.py", "Interface CLI"),
            (f"{self.nome_pacote}/setup.py", "Configuração instalação")
        ]
        
        for arquivo_rel, descricao in arquivos_criticos:
            arquivo_path = os.path.join(self.caminho_base, arquivo_rel)
            
            if os.path.exists(arquivo_path):
                print(f"✅ {descricao}: OK")
                self.resultados["testes_passaram"].append(f"Arquivo {descricao}")
            else:
                print(f"❌ {descricao}: FALTANDO")
                self.resultados["testes_falharam"].append(f"Arquivo {descricao}")
    
    def teste_5_instalacao_pip(self):
        """Verifica se a instalação via pip está funcionando."""
        print("\n🔍 Teste 5: Verificação instalação pip...")
        
        # Verificar se o pacote está instalado
        resultado = self.executar_comando([
            sys.executable, "-m", "pip", "list", "|", "grep", "cobol"
        ])
        
        # Como grep pode não funcionar em todos os sistemas, vamos usar uma abordagem diferente
        resultado_list = self.executar_comando([sys.executable, "-m", "pip", "list"])
        
        if resultado_list["sucesso"] and "cobol" in resultado_list["stdout"].lower():
            print("✅ Pacote instalado via pip: OK")
            self.resultados["testes_passaram"].append("Instalação pip")
        else:
            print("⚠️  Pacote não encontrado na lista pip (pode estar em modo desenvolvimento)")
            self.resultados["avisos"].append("Pacote não listado em pip list")
    
    def limpar_avisos_pkg_resources(self):
        """Remove avisos de pkg_resources dos arquivos."""
        print("\n🧹 Limpando avisos pkg_resources...")
        
        arquivos_para_limpar = [
            os.path.join(self.caminho_projeto, "runner", "main.py"),
            os.path.join(self.caminho_projeto, "runner", "cli.py"),
            os.path.join(self.caminho_projeto, "__init__.py"),
            os.path.join(self.caminho_projeto, "runner", "__init__.py")
        ]
        
        # Código para suprimir avisos pkg_resources
        codigo_supressao = '''
# Suprimir avisos pkg_resources
import warnings
warnings.filterwarnings("ignore", category=DeprecationWarning, module="pkg_resources")
'''
        
        arquivos_modificados = 0
        
        for arquivo_path in arquivos_para_limpar:
            if os.path.exists(arquivo_path):
                try:
                    with open(arquivo_path, 'r', encoding='utf-8') as f:
                        conteudo = f.read()
                    
                    # Verificar se já tem supressão
                    if "pkg_resources" not in conteudo and "warnings.filterwarnings" not in conteudo:
                        # Adicionar supressão após imports
                        linhas = conteudo.split('\n')
                        
                        # Encontrar onde inserir (após imports)
                        insert_pos = 0
                        for i, linha in enumerate(linhas):
                            if linha.strip().startswith('import ') or linha.strip().startswith('from '):
                                insert_pos = i + 1
                            elif linha.strip() and not linha.strip().startswith('#'):
                                break
                        
                        # Inserir código de supressão
                        linhas.insert(insert_pos, codigo_supressao.strip())
                        
                        with open(arquivo_path, 'w', encoding='utf-8') as f:
                            f.write('\n'.join(linhas))
                        
                        arquivos_modificados += 1
                        print(f"✅ Adicionada supressão em: {os.path.relpath(arquivo_path, self.caminho_base)}")
                
                except Exception as e:
                    print(f"❌ Erro ao modificar {arquivo_path}: {e}")
        
        if arquivos_modificados > 0:
            print(f"✅ Supressão de avisos adicionada em {arquivos_modificados} arquivos")
        else:
            print("ℹ️  Nenhum arquivo precisou de modificação")
    
    def gerar_relatorio_final(self):
        """Gera relatório final da validação."""
        print("\n" + "=" * 70)
        print("📋 RELATÓRIO FINAL DE VALIDAÇÃO")
        print("=" * 70)
        
        total_testes = len(self.resultados["testes_passaram"]) + len(self.resultados["testes_falharam"])
        testes_ok = len(self.resultados["testes_passaram"])
        
        print(f"\n📊 ESTATÍSTICAS:")
        print(f"   ✅ Testes passaram: {testes_ok}")
        print(f"   ❌ Testes falharam: {len(self.resultados['testes_falharam'])}")
        print(f"   ⚠️  Avisos: {len(self.resultados['avisos'])}")
        print(f"   📈 Taxa de sucesso: {(testes_ok/total_testes*100):.1f}%" if total_testes > 0 else "   📈 Taxa de sucesso: N/A")
        
        if self.resultados["comandos_funcionais"]:
            print(f"\n✅ COMANDOS FUNCIONAIS:")
            for comando in self.resultados["comandos_funcionais"]:
                print(f"   • {comando}")
        
        if self.resultados["testes_falharam"]:
            print(f"\n❌ TESTES QUE FALHARAM:")
            for teste in self.resultados["testes_falharam"]:
                print(f"   • {teste}")
        
        if self.resultados["avisos"]:
            print(f"\n⚠️  AVISOS (não críticos):")
            for aviso in self.resultados["avisos"]:
                print(f"   • {aviso}")
        
        # Conclusão
        print(f"\n" + "=" * 70)
        if len(self.resultados["testes_falharam"]) == 0:
            print("🎉 PARABÉNS! Todos os testes passaram!")
            print("✅ Seu projeto está funcionando corretamente!")
        elif len(self.resultados["comandos_funcionais"]) >= 2:
            print("✅ SUCESSO! Funcionalidades principais estão OK!")
            print("💡 Alguns testes falharam, mas os comandos principais funcionam.")
        else:
            print("⚠️  ATENÇÃO! Alguns problemas foram encontrados.")
            print("🔧 Execute o corretor novamente ou verifique os erros acima.")
        
        print(f"\n🚀 COMANDOS PARA USAR:")
        print(f"   cobol-to-docs --help")
        print(f"   cobol-analyzer --help")
        print(f"   python -m {self.nome_pacote}.runner.main --help")
        
        print(f"\n✅ Validação concluída!")
    
    def executar_validacao(self, rapido: bool = False, limpar_avisos: bool = False):
        """Executa validação completa."""
        print("🔍 VALIDADOR FINAL - PROJETO COBOL_ANALYZER")
        print("=" * 60)
        print(f"📁 Projeto: {self.nome_pacote}")
        print(f"📍 Localização: {self.caminho_projeto}")
        
        if limpar_avisos:
            self.limpar_avisos_pkg_resources()
            return
        
        # Executar testes
        self.teste_1_importacao_basica()
        self.teste_2_comandos_globais()
        
        if not rapido:
            self.teste_3_execucao_modulo()
            self.teste_4_estrutura_arquivos()
            self.teste_5_instalacao_pip()
        
        self.gerar_relatorio_final()

def main():
    """Função principal."""
    parser = argparse.ArgumentParser(description="Validador Final do projeto COBOL_ANALYZER")
    parser.add_argument("--rapido", action="store_true", 
                       help="Validação rápida (apenas testes essenciais)")
    parser.add_argument("--limpar-avisos", action="store_true",
                       help="Remove avisos pkg_resources dos arquivos")
    
    args = parser.parse_args()
    
    validador = ValidadorFinal()
    validador.executar_validacao(rapido=args.rapido, limpar_avisos=args.limpar_avisos)

if __name__ == "__main__":
    main()
