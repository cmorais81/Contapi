# Guia Completo de Reestruturação do Projeto COBOL_ANALYZER

## Visão Geral

Este guia fornece um processo completo para reestruturar o projeto **COBOL_ANALYZER** quando ele precisa ser movido para uma nova estrutura de diretórios, mantendo todas as funcionalidades incluindo:

- ✅ Execução via linha de comando (`main.py`, `cli.py`)
- ✅ Instalação como pacote Python (`pip install`)
- ✅ Comandos globais do sistema (`cobol-to-docs`, `cobol-analyzer`)
- ✅ Importações e dependências internas
- ✅ Estrutura de build e distribuição

## Estrutura Original vs Nova Estrutura

### Estrutura Original
```
projeto_original/
├── main.py                    # Ponto de entrada principal
├── cli.py                     # Interface de linha de comando
├── setup.py                   # Configuração de instalação
├── src/                       # Código fonte
│   ├── core/
│   ├── analyzers/
│   ├── providers/
│   └── ...
├── config/
├── examples/
└── docs/
```

### Nova Estrutura (Após Reestruturação)
```
meu_ambiente_trabalho/
├── cobol_to_docs/             # Projeto encapsulado
│   ├── __init__.py           # ← NOVO: Marca como pacote
│   ├── runner/               # ← NOVO: Scripts movidos
│   │   ├── __init__.py       # ← NOVO
│   │   ├── main.py           # ← MOVIDO
│   │   └── cli.py            # ← MOVIDO
│   ├── setup.py              # ← MODIFICADO: Entry points
│   ├── src/                  # Código fonte (inalterado)
│   │   ├── __init__.py       # ← VERIFICAR
│   │   ├── core/
│   │   ├── analyzers/
│   │   └── ...
│   ├── config/
│   ├── examples/
│   └── docs/
└── outros_projetos/
```

## Ferramentas Fornecidas

### 1. Analisador Completo (`analisador_projeto_cobol_completo.py`)

**Função**: Identifica todos os problemas na estrutura atual e gera relatório detalhado.

**Características**:
- ✅ Analisa importações quebradas
- ✅ Verifica estrutura de build (`setup.py`)
- ✅ Valida entry points para comandos globais
- ✅ Identifica arquivos `__init__.py` faltantes
- ✅ Detecta manipulação inadequada de `sys.path`
- ✅ Mapeia pontos de entrada da aplicação

**Uso**:
```bash
# Colocar o script na pasta que contém 'cobol_to_docs'
python analisador_projeto_cobol_completo.py
```

### 2. Corretor Automático (`corretor_automatico.py`)

**Função**: Aplica automaticamente as correções mais comuns identificadas.

**Características**:
- ✅ Cria arquivos `__init__.py` necessários
- ✅ Corrige importações `src.*` para `cobol_to_docs.src.*`
- ✅ Remove manipulação de `sys.path`
- ✅ Atualiza entry points no `setup.py`
- ✅ Cria backup automático antes das modificações
- ✅ Modo dry-run para visualizar mudanças

**Uso**:
```bash
# Visualizar o que seria feito
python corretor_automatico.py --dry-run

# Aplicar correções
python corretor_automatico.py
```

## Processo de Reestruturação Passo a Passo

### Passo 1: Preparação
1. **Faça backup** do projeto original
2. **Mova** `main.py` e `cli.py` para `cobol_to_docs/runner/`
3. **Coloque** o projeto dentro da nova estrutura de trabalho

### Passo 2: Análise
```bash
# Execute o analisador para identificar problemas
python analisador_projeto_cobol_completo.py
```

**Saída esperada**:
- Lista de arquivos com problemas de importação
- Problemas no `setup.py`
- Diretórios que precisam de `__init__.py`
- Comandos globais que precisam ser atualizados

### Passo 3: Correção Automática
```bash
# Primeiro, veja o que seria feito
python corretor_automatico.py --dry-run

# Se estiver satisfeito, aplique as correções
python corretor_automatico.py
```

### Passo 4: Correções Manuais (se necessário)

#### 4.1 Corrigir `setup.py`
**Problema**: Entry points apontam para módulos na raiz
```python
# ANTES (incorreto)
entry_points={
    "console_scripts": [
        "cobol-to-docs=main:main",
        "cobol-analyzer=cli:main",
    ],
}
```

**Solução**: Atualizar para nova estrutura
```python
# DEPOIS (correto)
entry_points={
    "console_scripts": [
        "cobol-to-docs=cobol_to_docs.runner.main:main",
        "cobol-analyzer=cobol_to_docs.runner.cli:main",
    ],
}
```

#### 4.2 Corrigir Importações
**Problema**: Importações relativas e `src.*`
```python
# ANTES (incorreto)
sys.path.insert(0, os.path.join(os.path.dirname(__file__), 'src'))
from src.core.config import ConfigManager
from .utils import helper_function
```

**Solução**: Usar importações absolutas
```python
# DEPOIS (correto)
from cobol_to_docs.src.core.config import ConfigManager
from cobol_to_docs.src.utils import helper_function
```

### Passo 5: Teste e Validação

#### 5.1 Teste de Instalação
```bash
# Instalar em modo desenvolvimento
cd /caminho/para/pasta/que/contem/cobol_to_docs
pip install -e ./cobol_to_docs/

# Verificar se comandos globais funcionam
cobol-to-docs --help
cobol-analyzer --help
```

#### 5.2 Teste de Execução Direta
```bash
# Executar como módulo Python
python -m cobol_to_docs.runner.main --help
python -m cobol_to_docs.runner.cli --help
```

#### 5.3 Teste de Funcionalidade
```bash
# Testar análise de um arquivo COBOL
cobol-to-docs /caminho/para/arquivo.cbl

# Ou usando execução direta
python -m cobol_to_docs.runner.main /caminho/para/arquivo.cbl
```

## Problemas Comuns e Soluções

### Problema 1: "ModuleNotFoundError: No module named 'src'"
**Causa**: Importações ainda usando `from src.` em vez de `from cobol_to_docs.src.`
**Solução**: Execute o corretor automático ou corrija manualmente

### Problema 2: "Command 'cobol-to-docs' not found"
**Causa**: Entry points no `setup.py` não foram atualizados
**Solução**: Corrigir `setup.py` e reinstalar com `pip install -e ./cobol_to_docs/`

### Problema 3: "ImportError: attempted relative import with no known parent package"
**Causa**: Importações relativas em arquivos executados diretamente
**Solução**: Converter para importações absolutas usando o nome do pacote

### Problema 4: "No module named 'cobol_to_docs'"
**Causa**: Falta arquivo `__init__.py` na raiz do pacote
**Solução**: Criar `cobol_to_docs/__init__.py`

## Validação Final

Após completar todos os passos, execute novamente o analisador:

```bash
python analisador_projeto_cobol_completo.py
```

**Resultado esperado**:
- ✅ Nenhum problema crítico encontrado
- ✅ Todos os entry points válidos
- ✅ Estrutura de build correta
- ✅ Comandos globais funcionando

## Comandos de Teste Final

```bash
# 1. Teste de instalação
pip install -e ./cobol_to_docs/

# 2. Teste de comandos globais
cobol-to-docs --version
cobol-analyzer --help

# 3. Teste de execução direta
python -m cobol_to_docs.runner.main --help
python -m cobol_to_docs.runner.cli --help

# 4. Teste de funcionalidade (se tiver arquivo COBOL)
cobol-to-docs exemplo.cbl --output ./output/
```

## Arquivos de Configuração

### Configuração Mínima do `__init__.py`
```python
# -*- coding: utf-8 -*-
"""
COBOL to Docs - Ferramenta de análise de código COBOL com IA
"""

__version__ = "3.1.0"
__author__ = "COBOL Analyzer Team"
```

### Configuração do `setup.py` Corrigida
```python
from setuptools import setup, find_packages

setup(
    name="cobol-to-docs",
    version="3.1.0",
    packages=find_packages(),
    entry_points={
        "console_scripts": [
            "cobol-to-docs=cobol_to_docs.runner.main:main",
            "cobol-analyzer=cobol_to_docs.runner.cli:main",
        ],
    },
    # ... outras configurações
)
```

## Conclusão

Seguindo este guia e utilizando as ferramentas fornecidas, você conseguirá reestruturar completamente o projeto COBOL_ANALYZER mantendo todas as funcionalidades:

- ✅ **Execução via CLI**: `python -m cobol_to_docs.runner.main`
- ✅ **Comandos globais**: `cobol-to-docs`, `cobol-analyzer`
- ✅ **Instalação via pip**: `pip install -e ./cobol_to_docs/`
- ✅ **Importações funcionais**: Todas as dependências internas resolvidas
- ✅ **Estrutura de build**: Pronta para distribuição

As ferramentas automatizam a maior parte do processo, mas sempre revise as mudanças e teste completamente antes de usar em produção.
