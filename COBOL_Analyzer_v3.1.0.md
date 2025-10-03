# COBOL Analyzer v3.1.0

Uma ferramenta avançada de análise e documentação automatizada de programas COBOL usando tecnologia de Inteligência Artificial.

## Visão Geral

O COBOL Analyzer é uma solução completa para análise, documentação e modernização de sistemas COBOL legados. Utiliza múltiplos modelos de IA para gerar documentação técnica profissional, análises de negócio e recomendações de modernização.

## Principais Funcionalidades

### Análise de Código
- **Análise Individual**: Processamento de programas COBOL individuais
- **Análise Consolidada**: Análise sistêmica de múltiplos programas simultaneamente
- **Análise Especializada**: Análise técnica profunda com prompts especializados
- **Análise de Procedures**: Foco detalhado na PROCEDURE DIVISION
- **Análise de Negócio**: Extração de regras de negócio e fórmulas matemáticas

### Sistema RAG (Retrieval-Augmented Generation)
- **Auto-learning**: Aprendizado contínuo a partir das análises realizadas
- **Base de Conhecimento**: Armazenamento inteligente de informações COBOL
- **Enriquecimento de Contexto**: Melhoria da qualidade das análises com conhecimento acumulado
- **Busca Semântica**: Recuperação inteligente de informações relevantes

### Múltiplos Provedores de IA
- **OpenAI**: GPT-4, GPT-4 Turbo, GPT-3.5 Turbo
- **AWS Bedrock**: Claude 3.5 Sonnet, Claude 3.5 Haiku, Amazon Nova Pro
- **Azure**: GPT-4o Experimental
- **Databricks**: DBRX Instruct
- **Enhanced Mock**: Simulador para testes e desenvolvimento

### Geração de Documentação
- **Padrão DOC-LEGADO PRO**: Documentação técnica profissional
- **Relatórios HTML/PDF**: Saídas visuais profissionais
- **Análise Funcional**: Documentação orientada ao negócio
- **Relatórios Comparativos**: Análise entre múltiplos modelos
- **Relatórios de Custos**: Controle de gastos com APIs de IA

### Modernização e Migração
- **Análise de Modernização**: Identificação de oportunidades de atualização
- **Recomendações de Migração**: Sugestões para tecnologias modernas
- **Análise de Complexidade**: Avaliação da dificuldade de modernização
- **Mapeamento de Dependências**: Identificação de interdependências

## Formas de Uso

### 1. Uso Direto via main.py (Recomendado)

```bash
# Análise básica
python3 main.py --fontes examples/fontes.txt --models enhanced_mock

# Análise com copybooks
python3 main.py --fontes examples/fontes.txt --books examples/books.txt

# Análise consolidada
python3 main.py --fontes examples/fontes.txt --consolidado

# Análise especializada
python3 main.py --fontes examples/fontes.txt --analise-especialista

# Múltiplos modelos
python3 main.py --fontes examples/fontes.txt --models '["enhanced_mock", "aws-claude-3-5-sonnet"]'

# Análise avançada com HTML
python3 main.py --fontes examples/fontes.txt --advanced-analysis --pdf

# Modernização
python3 main.py --fontes examples/fontes.txt --modernizacao

# Status dos provedores
python3 main.py --status
```

### 2. Interface CLI

```bash
# Usar via CLI wrapper
python3 cli.py --fontes examples/fontes.txt --models enhanced_mock

# Todas as opções do main.py estão disponíveis
python3 cli.py --help
```

### 3. Instalação via pip

```bash
# Instalar o pacote
pip install .

# Usar comando instalado
cobol-analyzer --fontes examples/fontes.txt --models enhanced_mock

# Verificar instalação
cobol-analyzer --help
```

## Instalação e Configuração

### Requisitos do Sistema
- Python 3.8 ou superior
- Sistema operacional: Windows, Linux, macOS
- Memória RAM: Mínimo 4GB, recomendado 8GB
- Espaço em disco: 500MB para instalação completa

### Instalação Rápida

```bash
# 1. Extrair o pacote
tar -xzf COBOL_ANALYZER_v3.1.0_FINAL.tar.gz
cd cobol_analyzer_EXCELENCIA

# 2. Instalar dependências
pip install -r requirements.txt

# 3. Configurar (opcional)
cp config/config.yaml config/config_local.yaml
# Editar config_local.yaml com suas chaves de API

# 4. Testar instalação
python3 main.py --status
```

### Configuração de Provedores de IA

Edite o arquivo `config/config.yaml` ou crie `config/config_local.yaml`:

```yaml
providers:
  openai:
    api_key: "sua_chave_openai"
    base_url: "https://api.openai.com/v1"
  
  aws_bedrock:
    region: "us-east-1"
    access_key: "sua_chave_aws"
    secret_key: "sua_chave_secreta_aws"
  
  azure:
    api_key: "sua_chave_azure"
    endpoint: "https://seu-endpoint.openai.azure.com/"
```

## Estrutura de Arquivos

```
cobol_analyzer_EXCELENCIA/
├── main.py                 # Ponto de entrada principal
├── cli.py                  # Interface CLI alternativa
├── setup.py                # Configuração para instalação via pip
├── requirements.txt        # Dependências Python
├── README.md              # Esta documentação
├── config/
│   └── config.yaml        # Configurações principais
├── src/                   # Código-fonte da aplicação
│   ├── core/             # Componentes centrais
│   ├── providers/        # Provedores de IA
│   ├── analyzers/        # Analisadores COBOL
│   ├── generators/       # Geradores de documentação
│   ├── parsers/          # Parsers COBOL
│   ├── rag/              # Sistema RAG
│   └── utils/            # Utilitários
├── data/                 # Base de conhecimento RAG
├── examples/             # Exemplos de uso
├── docs/                 # Documentação adicional
└── logs/                 # Logs da aplicação
```

## Exemplos Práticos

### Análise Básica de um Programa

```bash
# Criar arquivo de fontes
echo "PROGRAMA1.cbl" > meus_programas.txt

# Executar análise
python3 main.py --fontes meus_programas.txt --models enhanced_mock --output resultado

# Verificar saída
ls resultado/
# PROGRAMA1_analise_funcional.md
# ai_requests/
# ai_responses/
# relatorio_custos.txt
```

### Análise Consolidada de Sistema

```bash
# Múltiplos programas
echo -e "PROGRAMA1.cbl\nPROGRAMA2.cbl\nPROGRAMA3.cbl" > sistema_completo.txt

# Análise consolidada
python3 main.py --fontes sistema_completo.txt --consolidado --models enhanced_mock

# Gera análise sistêmica de todos os programas juntos
```

### Análise com Copybooks

```bash
# Arquivo de copybooks
echo -e "COPY1.cpy\nCOPY2.cpy" > copybooks.txt

# Análise completa
python3 main.py --fontes programas.txt --books copybooks.txt --analise-especialista
```

### Comparação de Modelos

```bash
# Múltiplos modelos para comparação
python3 main.py --fontes programas.txt --models '["enhanced_mock", "gpt-4", "aws-claude-3-5-sonnet"]'

# Gera relatório comparativo entre os modelos
```

## Opções Avançadas

### Parâmetros de Linha de Comando

| Parâmetro | Descrição | Exemplo |
|-----------|-----------|---------|
| `--fontes` | Arquivo com lista de programas COBOL | `--fontes programas.txt` |
| `--books` | Arquivo com lista de copybooks | `--books copybooks.txt` |
| `--output` | Diretório de saída | `--output resultado` |
| `--models` | Modelos de IA a usar | `--models enhanced_mock` |
| `--prompt-set` | Conjunto de prompts | `--prompt-set especialista` |
| `--consolidado` | Análise consolidada sistêmica | `--consolidado` |
| `--analise-especialista` | Análise técnica profunda | `--analise-especialista` |
| `--procedure-detalhada` | Foco na PROCEDURE DIVISION | `--procedure-detalhada` |
| `--modernizacao` | Análise de modernização | `--modernizacao` |
| `--deep-analysis` | Análise detalhada de regras | `--deep-analysis` |
| `--extract-formulas` | Extração de fórmulas | `--extract-formulas` |
| `--advanced-analysis` | Relatório HTML profissional | `--advanced-analysis` |
| `--pdf` | Gerar relatórios PDF | `--pdf` |
| `--auto-model` | Seleção automática de modelo | `--auto-model` |
| `--model-comparison` | Comparação de modelos | `--model-comparison` |
| `--no-comments` | Remover comentários do código | `--no-comments` |
| `--status` | Verificar status dos provedores | `--status` |

### Configurações Avançadas

#### Sistema RAG
```yaml
rag:
  enabled: true
  knowledge_base_path: "data/cobol_knowledge_base.json"
  max_context_items: 10
  similarity_threshold: 0.7
  auto_learning: true
```

#### Modelos de IA
```yaml
models:
  default: "enhanced_mock"
  fallback: ["gpt-4", "aws-claude-3-5-sonnet"]
  temperature: 0.1
  max_tokens: 8000
```

#### Geração de Documentação
```yaml
documentation:
  format: "doc_legado_pro"
  include_code: true
  include_analysis: true
  generate_html: true
  generate_pdf: false
```

## Solução de Problemas

### Problemas Comuns

#### Erro de Importação
```bash
# Se encontrar erro "ModuleNotFoundError"
export PYTHONPATH=$PYTHONPATH:$(pwd)/src
python3 main.py --help
```

#### Problemas de Dependências
```bash
# Reinstalar dependências
pip install -r requirements.txt --force-reinstall
```

#### Erro de Configuração
```bash
# Verificar configuração
python3 main.py --status

# Usar modelo mock para testes
python3 main.py --fontes examples/fontes.txt --models enhanced_mock
```

### Logs e Depuração

```bash
# Aumentar nível de log
python3 main.py --fontes programas.txt --log-level DEBUG

# Verificar logs
tail -f logs/cobol_to_docs_*.log
```

## Desenvolvimento e Contribuição

### Estrutura do Código

O projeto segue uma arquitetura modular:

- **Core**: Componentes centrais (configuração, logging)
- **Providers**: Interfaces com APIs de IA
- **Analyzers**: Lógica de análise COBOL
- **Generators**: Geração de documentação
- **RAG**: Sistema de recuperação e geração aumentada
- **Utils**: Utilitários diversos

### Adicionando Novos Provedores

1. Criar classe em `src/providers/`
2. Herdar de `BaseProvider`
3. Implementar métodos obrigatórios
4. Registrar em `enhanced_provider_manager.py`

### Adicionando Novos Analisadores

1. Criar classe em `src/analyzers/`
2. Implementar interface de análise
3. Adicionar prompts em `config/`
4. Integrar no fluxo principal

## Licença e Suporte

### Licença
Este projeto está licenciado sob a Licença MIT. Veja o arquivo LICENSE para detalhes.

### Suporte
- **Documentação**: Consulte este README e a pasta `docs/`
- **Exemplos**: Veja a pasta `examples/`
- **Logs**: Verifique a pasta `logs/` para depuração

### Versão
- **Versão Atual**: 3.1.0
- **Data de Lançamento**: Outubro 2025
- **Compatibilidade**: Python 3.8+

---

**COBOL Analyzer** - Transformando sistemas legados em documentação moderna com o poder da Inteligência Artificial.
