#!/usr/bin/env python3
"""
Corretor de Inicialização - Corrige problemas com comando --init
Resolve problemas de caminhos, estrutura de pastas e uso de arquivos originais.

Uso:
    python corretor_inicializacao.py                    # Análise e correção interativa
    python corretor_inicializacao.py --auto             # Correção automática
    python corretor_inicializacao.py --analisar         # Apenas análise
"""

import os
import sys
import re
import shutil
import argparse
from pathlib import Path
from typing import List, Dict, Any
from datetime import datetime

class CorretorInicializacao:
    def __init__(self, caminho_base: str = ".", modo_auto: bool = False):
        self.caminho_base = os.path.abspath(caminho_base)
        self.modo_auto = modo_auto
        
        # Detectar estrutura
        self.detectar_estrutura()
        
        self.problemas_encontrados = []
        self.correcoes_aplicadas = []
        self.backup_criado = False
    
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
    
    def criar_backup(self):
        """Cria backup do projeto."""
        if self.backup_criado:
            return True
        
        timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
        backup_dir = f"{self.caminho_projeto}_backup_init_{timestamp}"
        
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
    
    def problema_1_analisar_comando_init(self):
        """Analisa o comando --init nos arquivos principais."""
        print("\n🔍 Analisando implementação do comando --init...")
        
        arquivos_para_analisar = [
            os.path.join(self.caminho_projeto, "runner", "main.py"),
            os.path.join(self.caminho_projeto, "runner", "cli.py"),
        ]
        
        problemas_init = []
        
        for arquivo_path in arquivos_para_analisar:
            if os.path.exists(arquivo_path):
                problemas = self.analisar_init_arquivo(arquivo_path)
                if problemas:
                    problemas_init.extend(problemas)
        
        if problemas_init:
            print(f"📋 Encontrados {len(problemas_init)} problemas com --init:")
            for problema in problemas_init:
                print(f"   ❌ {problema['arquivo']}: {problema['descricao']}")
            
            return problemas_init
        else:
            print("✅ Implementação do --init parece estar correta")
            return []
    
    def analisar_init_arquivo(self, arquivo_path: str) -> List[Dict[str, Any]]:
        """Analisa problemas de inicialização em um arquivo."""
        problemas = []
        
        try:
            with open(arquivo_path, 'r', encoding='utf-8') as f:
                conteudo = f.read()
            
            arquivo_rel = os.path.relpath(arquivo_path, self.caminho_base)
            
            # Procurar por lógica de inicialização
            if '--init' in conteudo or 'init' in conteudo.lower():
                
                # Problema 1: Criação de pasta cobol_to_docs duplicada
                if re.search(r'os\.makedirs.*cobol_to_docs', conteudo):
                    problemas.append({
                        "arquivo": arquivo_rel,
                        "tipo": "pasta_duplicada",
                        "descricao": "Criando pasta cobol_to_docs duplicada",
                        "linha_exemplo": self.encontrar_linha_problema(conteudo, r'os\.makedirs.*cobol_to_docs')
                    })
                
                # Problema 2: Não usando arquivos originais de config/data
                if not re.search(r'(config|data).*original|original.*(config|data)', conteudo):
                    if 'config' in conteudo or 'data' in conteudo:
                        problemas.append({
                            "arquivo": arquivo_rel,
                            "tipo": "arquivos_originais",
                            "descricao": "Não está copiando arquivos originais de config/data",
                            "linha_exemplo": self.encontrar_linha_problema(conteudo, r'(config|data)')
                        })
                
                # Problema 3: Caminhos absolutos em vez de relativos
                if re.search(r'os\.path\.join.*cobol_to_docs.*cobol_to_docs', conteudo):
                    problemas.append({
                        "arquivo": arquivo_rel,
                        "tipo": "caminhos_duplicados",
                        "descricao": "Caminhos com cobol_to_docs duplicado",
                        "linha_exemplo": self.encontrar_linha_problema(conteudo, r'os\.path\.join.*cobol_to_docs.*cobol_to_docs')
                    })
                
                # Problema 4: Não verificando se já existe estrutura
                if 'makedirs' in conteudo and 'exist_ok' not in conteudo:
                    problemas.append({
                        "arquivo": arquivo_rel,
                        "tipo": "sobrescrever_estrutura",
                        "descricao": "Pode sobrescrever estrutura existente",
                        "linha_exemplo": self.encontrar_linha_problema(conteudo, r'makedirs')
                    })
        
        except Exception as e:
            problemas.append({
                "arquivo": arquivo_rel,
                "tipo": "erro_leitura",
                "descricao": f"Erro ao ler arquivo: {e}",
                "linha_exemplo": None
            })
        
        return problemas
    
    def encontrar_linha_problema(self, conteudo: str, pattern: str) -> str:
        """Encontra linha que contém o padrão problemático."""
        try:
            match = re.search(pattern, conteudo)
            if match:
                linhas = conteudo[:match.start()].split('\n')
                linha_num = len(linhas)
                linha_conteudo = conteudo.split('\n')[linha_num - 1] if linha_num <= len(conteudo.split('\n')) else ""
                return f"Linha {linha_num}: {linha_conteudo.strip()}"
        except:
            pass
        return "Linha não identificada"
    
    def problema_2_corrigir_logica_init(self):
        """Corrige a lógica de inicialização."""
        print("\n🔍 Corrigindo lógica de inicialização...")
        
        arquivos_principais = [
            os.path.join(self.caminho_projeto, "runner", "main.py"),
            os.path.join(self.caminho_projeto, "runner", "cli.py"),
        ]
        
        for arquivo_path in arquivos_principais:
            if os.path.exists(arquivo_path):
                if self.corrigir_init_arquivo(arquivo_path):
                    arquivo_rel = os.path.relpath(arquivo_path, self.caminho_base)
                    print(f"✅ Corrigido: {arquivo_rel}")
                    self.correcoes_aplicadas.append(f"Lógica --init corrigida em {arquivo_rel}")
    
    def corrigir_init_arquivo(self, arquivo_path: str) -> bool:
        """Corrige lógica de inicialização em um arquivo."""
        try:
            with open(arquivo_path, 'r', encoding='utf-8') as f:
                conteudo = f.read()
            
            conteudo_original = conteudo
            
            # Correção 1: Função de inicialização correta
            funcao_init_correta = self.gerar_funcao_init_correta()
            
            # Procurar e substituir função de inicialização existente
            # Padrão para encontrar função init
            pattern_init = r'def\s+.*init.*\([^)]*\):.*?(?=def\s+|\Z)'
            
            if re.search(pattern_init, conteudo, re.DOTALL):
                # Substituir função existente
                conteudo = re.sub(pattern_init, funcao_init_correta, conteudo, flags=re.DOTALL)
            else:
                # Adicionar função se não existir
                # Encontrar local para inserir (antes da função main)
                if 'def main(' in conteudo:
                    conteudo = conteudo.replace('def main(', f'{funcao_init_correta}\n\ndef main(')
                else:
                    # Adicionar no final
                    conteudo += f'\n\n{funcao_init_correta}'
            
            # Correção 2: Atualizar chamada da função init no argparse
            conteudo = self.corrigir_argparse_init(conteudo)
            
            if conteudo != conteudo_original:
                if not self.criar_backup():
                    return False
                
                with open(arquivo_path, 'w', encoding='utf-8') as f:
                    f.write(conteudo)
                
                return True
            
            return False
        
        except Exception as e:
            print(f"❌ Erro ao corrigir {arquivo_path}: {e}")
            return False
    
    def gerar_funcao_init_correta(self) -> str:
        """Gera função de inicialização correta."""
        return f'''def inicializar_ambiente(diretorio_trabalho="."):
    """
    Inicializa ambiente de trabalho para análise COBOL.
    
    Args:
        diretorio_trabalho (str): Diretório onde criar a estrutura de trabalho
    
    Returns:
        bool: True se inicialização foi bem-sucedida
    """
    import os
    import shutil
    from pathlib import Path
    
    # Detectar localização do pacote instalado
    try:
        import {self.nome_pacote}
        pacote_path = Path({self.nome_pacote}.__file__).parent
    except ImportError:
        print("❌ Pacote {self.nome_pacote} não encontrado. Execute: pip install -e ./cobol_to_docs/")
        return False
    
    diretorio_trabalho = Path(diretorio_trabalho).resolve()
    
    print(f"🔧 Inicializando ambiente em: {{diretorio_trabalho}}")
    
    # Estrutura de diretórios para criar no diretório de trabalho
    estrutura_diretorios = [
        "config",
        "data",
        "data/embeddings", 
        "data/knowledge_base",
        "data/sessions",
        "logs",
        "examples",
        "output"
    ]
    
    # Criar estrutura de diretórios
    for diretorio in estrutura_diretorios:
        dir_path = diretorio_trabalho / diretorio
        dir_path.mkdir(parents=True, exist_ok=True)
        print(f"✅ Diretório criado: {{diretorio}}")
    
    # Copiar arquivos de configuração originais
    arquivos_para_copiar = [
        ("config", "config.yaml"),
        ("data", "cobol_knowledge_base.json"),
        ("data", "cobol_knowledge_base_consolidated.json"),
        ("examples", "*.cbl"),
        ("examples", "*.cob"),
    ]
    
    for pasta_origem, arquivo_pattern in arquivos_para_copiar:
        origem_dir = pacote_path / pasta_origem
        destino_dir = diretorio_trabalho / pasta_origem
        
        if origem_dir.exists():
            if "*" in arquivo_pattern:
                # Copiar arquivos com padrão
                import glob
                pattern_path = str(origem_dir / arquivo_pattern)
                arquivos_encontrados = glob.glob(pattern_path)
                
                for arquivo_origem in arquivos_encontrados:
                    arquivo_nome = Path(arquivo_origem).name
                    arquivo_destino = destino_dir / arquivo_nome
                    
                    try:
                        shutil.copy2(arquivo_origem, arquivo_destino)
                        print(f"✅ Copiado: {{pasta_origem}}/{{arquivo_nome}}")
                    except Exception as e:
                        print(f"⚠️  Erro ao copiar {{arquivo_origem}}: {{e}}")
            else:
                # Copiar arquivo específico
                arquivo_origem = origem_dir / arquivo_pattern
                arquivo_destino = destino_dir / arquivo_pattern
                
                if arquivo_origem.exists():
                    try:
                        shutil.copy2(arquivo_origem, arquivo_destino)
                        print(f"✅ Copiado: {{pasta_origem}}/{{arquivo_pattern}}")
                    except Exception as e:
                        print(f"⚠️  Erro ao copiar {{arquivo_origem}}: {{e}}")
                else:
                    print(f"⚠️  Arquivo original não encontrado: {{arquivo_origem}}")
        else:
            print(f"⚠️  Pasta original não encontrada: {{origem_dir}}")
    
    # Criar arquivo de configuração local se não existir
    config_local = diretorio_trabalho / "config" / "config.yaml"
    if not config_local.exists():
        config_conteudo = '''# Configuração local do COBOL Analyzer
# Este arquivo foi criado automaticamente

# Configurações de análise
analysis:
  output_format: "markdown"
  include_comments: true
  generate_diagrams: true

# Configurações de caminhos
paths:
  input_dir: "./input"
  output_dir: "./output"
  logs_dir: "./logs"

# Configurações de IA
ai:
  model: "default"
  temperature: 0.7
  max_tokens: 2000

# Configurações de documentação
documentation:
  language: "pt-BR"
  include_examples: true
  generate_index: true
'''
        
        try:
            with open(config_local, 'w', encoding='utf-8') as f:
                f.write(config_conteudo)
            print(f"✅ Configuração criada: config/config.yaml")
        except Exception as e:
            print(f"⚠️  Erro ao criar configuração: {{e}}")
    
    # Criar arquivo .cobol_analyzer_init para marcar inicialização
    marker_file = diretorio_trabalho / ".cobol_analyzer_init"
    try:
        with open(marker_file, 'w', encoding='utf-8') as f:
            f.write(f"Ambiente inicializado em: {{datetime.now().isoformat()}}\\n")
            f.write(f"Pacote: {self.nome_pacote}\\n")
            f.write(f"Versão: 3.1.0\\n")
        print(f"✅ Marcador criado: .cobol_analyzer_init")
    except Exception as e:
        print(f"⚠️  Erro ao criar marcador: {{e}}")
    
    print(f"\\n🎉 Ambiente inicializado com sucesso!")
    print(f"📁 Diretório de trabalho: {{diretorio_trabalho}}")
    print(f"\\n🚀 Próximos passos:")
    print(f"   1. Coloque seus arquivos COBOL na pasta 'input' (ou crie uma)")
    print(f"   2. Execute: cobol-to-docs --analyze ./input")
    print(f"   3. Verifique os resultados na pasta 'output'")
    
    return True'''
    
    def corrigir_argparse_init(self, conteudo: str) -> str:
        """Corrige a configuração do argparse para --init."""
        
        # Procurar por add_argument para --init
        pattern_init_arg = r'parser\.add_argument\(["\']--init["\'][^)]*\)'
        
        # Substituir por versão correta
        init_arg_correto = '''parser.add_argument(
        "--init", 
        action="store_true",
        help="Inicializa ambiente de trabalho com estrutura de pastas e arquivos de configuração"
    )'''
        
        if re.search(pattern_init_arg, conteudo):
            conteudo = re.sub(pattern_init_arg, init_arg_correto, conteudo)
        
        # Procurar por tratamento do argumento --init
        pattern_init_handler = r'if\s+args\.init\s*:.*?(?=if\s+|$)'
        
        # Substituir por versão correta
        init_handler_correto = '''if args.init:
        sucesso = inicializar_ambiente()
        if sucesso:
            print("✅ Inicialização concluída com sucesso!")
            sys.exit(0)
        else:
            print("❌ Erro na inicialização!")
            sys.exit(1)'''
        
        if re.search(pattern_init_handler, conteudo, re.DOTALL):
            conteudo = re.sub(pattern_init_handler, init_handler_correto, conteudo, flags=re.DOTALL)
        else:
            # Adicionar handler se não existir
            if 'if __name__ == "__main__":' in conteudo:
                # Adicionar antes do main
                conteudo = conteudo.replace(
                    'if __name__ == "__main__":',
                    f'{init_handler_correto}\n\nif __name__ == "__main__":'
                )
        
        return conteudo
    
    def problema_3_testar_init(self):
        """Testa o comando --init."""
        print("\n🧪 Testando comando --init...")
        
        # Criar diretório de teste
        test_dir = os.path.join(self.caminho_base, "teste_init")
        if os.path.exists(test_dir):
            shutil.rmtree(test_dir)
        
        os.makedirs(test_dir, exist_ok=True)
        
        print(f"   Testando em: {test_dir}")
        
        # Testar comando
        import subprocess
        
        try:
            resultado = subprocess.run([
                sys.executable, "-m", f"{self.nome_pacote}.runner.main", "--init"
            ], 
            cwd=test_dir,
            capture_output=True,
            text=True,
            timeout=30
            )
            
            if resultado.returncode == 0:
                print("✅ Comando --init executou sem erros")
                
                # Verificar estrutura criada
                estrutura_esperada = ["config", "data", "logs", "examples"]
                estrutura_ok = True
                
                for pasta in estrutura_esperada:
                    pasta_path = os.path.join(test_dir, pasta)
                    if os.path.exists(pasta_path):
                        print(f"   ✅ Pasta criada: {pasta}")
                    else:
                        print(f"   ❌ Pasta faltando: {pasta}")
                        estrutura_ok = False
                
                # Verificar se não criou pasta duplicada
                pasta_duplicada = os.path.join(test_dir, "cobol_to_docs")
                if os.path.exists(pasta_duplicada):
                    print("   ❌ Pasta cobol_to_docs duplicada foi criada (PROBLEMA)")
                    estrutura_ok = False
                else:
                    print("   ✅ Não criou pasta duplicada")
                
                if estrutura_ok:
                    print("🎉 Teste do --init passou!")
                    return True
                else:
                    print("⚠️  Teste do --init teve problemas na estrutura")
                    return False
            else:
                print("❌ Comando --init falhou:")
                print(f"   Erro: {resultado.stderr}")
                return False
        
        except Exception as e:
            print(f"❌ Erro ao testar --init: {e}")
            return False
        
        finally:
            # Limpar diretório de teste
            if os.path.exists(test_dir):
                shutil.rmtree(test_dir)
    
    def executar_correcoes(self, apenas_analisar: bool = False):
        """Executa correções de inicialização."""
        print("🔧 CORRETOR DE INICIALIZAÇÃO - COMANDO --init")
        print("=" * 60)
        print(f"📁 Projeto: {self.nome_pacote}")
        print(f"📍 Localização: {self.caminho_projeto}")
        
        if apenas_analisar:
            print("🔍 MODO: Apenas análise")
        elif self.modo_auto:
            print("🤖 MODO: Correção automática")
        else:
            print("🤝 MODO: Correção interativa")
        
        # Análise
        problemas = self.problema_1_analisar_comando_init()
        
        if not apenas_analisar and problemas:
            if self.perguntar_usuario("Corrigir problemas encontrados?"):
                self.problema_2_corrigir_logica_init()
        
        # Teste
        if not apenas_analisar:
            print("\n" + "="*60)
            if self.perguntar_usuario("Testar comando --init após correções?"):
                sucesso_teste = self.problema_3_testar_init()
                
                if sucesso_teste:
                    self.correcoes_aplicadas.append("Teste do --init passou")
                else:
                    print("⚠️  O teste falhou. Pode ser necessário mais correções.")
        
        # Relatório final
        print("\n" + "=" * 60)
        print("📋 RESUMO")
        print("=" * 60)
        
        if self.correcoes_aplicadas:
            print(f"✅ {len(self.correcoes_aplicadas)} correções aplicadas:")
            for correcao in self.correcoes_aplicadas:
                print(f"   • {correcao}")
        else:
            if apenas_analisar:
                print("ℹ️  Modo análise - nenhuma correção aplicada")
            else:
                print("ℹ️  Nenhuma correção foi necessária")
        
        print(f"\n🚀 TESTE MANUAL:")
        print(f"   mkdir teste_manual && cd teste_manual")
        print(f"   cobol-to-docs --init")
        print(f"   ls -la  # Verificar estrutura criada")
        
        print(f"\n✅ Processo concluído!")

def main():
    """Função principal."""
    parser = argparse.ArgumentParser(description="Corretor de Inicialização - Comando --init")
    parser.add_argument("--auto", action="store_true", 
                       help="Modo automático")
    parser.add_argument("--analisar", action="store_true",
                       help="Apenas analisar problemas")
    
    args = parser.parse_args()
    
    corretor = CorretorInicializacao(modo_auto=args.auto)
    corretor.executar_correcoes(apenas_analisar=args.analisar)

if __name__ == "__main__":
    main()
