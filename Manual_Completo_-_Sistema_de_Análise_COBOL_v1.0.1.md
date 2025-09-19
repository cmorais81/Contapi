# Manual Completo - Sistema de Análise COBOL v1.0.1

## Índice

1. [Visão Geral](#visão-geral)
2. [Instalação e Configuração](#instalação-e-configuração)
3. [Configuração de Provedores LLM](#configuração-de-provedores-llm)
4. [Configuração SSL](#configuração-ssl)
5. [Modos de Execução](#modos-de-execução)
6. [Opções de Linha de Comando](#opções-de-linha-de-comando)
7. [Exemplos de Uso](#exemplos-de-uso)
8. [Configuração Avançada](#configuração-avançada)
9. [Logging e Monitoramento](#logging-e-monitoramento)
10. [Solução de Problemas](#solução-de-problemas)
11. [Referência de Configuração](#referência-de-configuração)

## Visão Geral

O Sistema de Análise COBOL v1.0.1 é uma ferramenta avançada para análise automatizada de código COBOL, oferecendo múltiplas modalidades de análise e suporte a diversos provedores de LLM (Large Language Models).

### Principais Funcionalidades

- **Análise Multi-IA**: Utiliza múltiplos provedores LLM para análises cruzadas
- **Análise Tradicional**: Análise baseada em regras sem dependência de LLM
- **Análise Híbrida**: Combina extração de conteúdo com análise por LLM
- **Suporte a Múltiplos Provedores**: OpenAI, GitHub Copilot, LuzIA Corporativo
- **Fallback Automático**: Sistema de fallback entre provedores
- **Logging Detalhado**: Visualização completa dos prompts enviados aos LLMs
- **Configuração SSL**: Suporte a certificados SSL personalizados

### Arquivos Suportados

- Programas COBOL individuais (`.cbl`, `.cob`)
- Arquivos de múltiplos programas (formato VMEMBER)
- Copybooks COBOL
- Arquivos de texto com código COBOL

## Instalação e Configuração

### Pré-requisitos

```bash
# Python 3.8 ou superior
python3 --version

# Dependências Python
pip install pyyaml requests httpx asyncio python-dotenv
```

### Estrutura do Projeto

```
cobol_analysis_engine_v1.0.1/
├── main.py                    # Script principal
├── config/
│   ├── config.yaml           # Configuração principal
│   └── prompts.yaml          # Templates de prompts
├── src/
│   ├── core/                 # Componentes principais
│   ├── providers/            # Provedores LLM
│   ├── analyzers/            # Analisadores
│   ├── generators/           # Geradores de documentação
│   ├── extractors/           # Extratores de conteúdo
│   └── utils/                # Utilitários
├── examples/                 # Arquivos de exemplo
├── docs/                     # Documentação
└── analysis_results/         # Resultados de análise
```

### Configuração Inicial

1. **Extrair o pacote**:
```bash
tar -xzf cobol_analysis_engine_v1.0.1_FINAL.tar.gz
cd v1.0.1_clean
```

2. **Verificar status do sistema**:
```bash
python3 main.py --status
```

3. **Configurar variáveis de ambiente** (opcional):
```bash
export OPENAI_API_KEY="sua_chave_openai"
export GITHUB_TOKEN="seu_token_github"
export LUZIA_CLIENT_ID="seu_client_id_luzia"
export LUZIA_CLIENT_SECRET="seu_client_secret_luzia"
```

## Configuração de Provedores LLM

### OpenAI GPT-4

```yaml
# config/config.yaml
ai:
  providers:
    openai:
      enabled: true
      api_key: "${OPENAI_API_KEY}"
      model: "gpt-4"
      temperature: 0.1
      max_tokens: 8000
      timeout: 120
      base_url: "https://api.openai.com/v1"
```

**Configuração via variável de ambiente**:
```bash
export OPENAI_API_KEY="sk-proj-..."
```

### GitHub Copilot

```yaml
# config/config.yaml
ai:
  providers:
    copilot:
      enabled: true
      api_key: "${GITHUB_TOKEN}"
      model: "gpt-4"
      temperature: 0.1
      max_tokens: 8000
      timeout: 120
      base_url: "https://api.githubcopilot.com/chat/completions"
      headers:
        "Authorization": "Bearer ${GITHUB_TOKEN}"
        "Editor-Version": "vscode/1.83.0"
        "Editor-Plugin-Version": "copilot-chat/0.8.0"
        "User-Agent": "GitHubCopilotChat/0.8.0"
```

**Configuração via variável de ambiente**:
```bash
export GITHUB_TOKEN="ghp_..."
```

### LuzIA Corporativo

```yaml
# config/config.yaml
ai:
  providers:
    luzia:
      enabled: true
      client_id: '${LUZIA_CLIENT_ID:-7153e7d9-d0a9-42ac-8a1c-72bf903155fa}'
      client_secret: '${LUZIA_CLIENT_SECRET:-90A337BtXt9vH9zXAqc5500gNozjR7xJ}'
      auth_url: 'https://login.azure.paas.santanderbr.pre.corp/auth/realms/corp/protocol/openid-connect/token'
      api_url: 'https://gut-api-aws.santanderbr.dev.corp/genai_services/v1/'
      model: 'azure-gpt-4o-mini'
      temperature: 0.1
      max_tokens: 4000
      timeout: 180
      ssl_cert_path: null # Caminho para certificado SSL
      retry:
        max_attempts: 5
        base_delay: 2.0
        max_delay: 60.0
        backoff_multiplier: 2.0
        requests_per_minute: 8
```

**Configuração via variáveis de ambiente**:
```bash
export LUZIA_CLIENT_ID="7153e7d9-d0a9-42ac-8a1c-72bf903155fa"
export LUZIA_CLIENT_SECRET="90A337BtXt9vH9zXAqc5500gNozjR7xJ"
```

### Enhanced Mock (Sempre Disponível)

```yaml
# config/config.yaml
ai:
  providers:
    enhanced_mock:
      enabled: true
      model: "enhanced-mock-v1.0.0"
      temperature: 0.1
      max_tokens: 8000
      timeout: 30
      quality_level: "high"  # low, medium, high
      include_metrics: true
      realistic_responses: true
```

## Configuração SSL

### Configuração de Certificados SSL para LuzIA

Para ambientes corporativos que requerem certificados SSL específicos:

1. **Obter o certificado SSL**:
```bash
# Baixar certificado do servidor
openssl s_client -showcerts -connect gut-api-aws.santanderbr.dev.corp:443 < /dev/null 2>/dev/null | openssl x509 -outform PEM > santander_cert.pem
```

2. **Configurar no config.yaml**:
```yaml
ai:
  providers:
    luzia:
      ssl_cert_path: "/path/to/santander_cert.pem"
```

3. **Configurar via variável de ambiente**:
```bash
export LUZIA_SSL_CERT_PATH="/path/to/santander_cert.pem"
```

### Variáveis de Ambiente SSL

```bash
# Certificado SSL personalizado
export REQUESTS_CA_BUNDLE="/path/to/cert.pem"
export SSL_CERT_FILE="/path/to/cert.pem"
export SSL_CERT_DIR="/path/to/certs/"

# Desabilitar verificação SSL (não recomendado para produção)
export PYTHONHTTPSVERIFY=0
```

## Modos de Execução

### 1. Modo Multi-IA (Recomendado)

Utiliza múltiplos provedores LLM para análises cruzadas e validação.

```bash
python3 main.py programa.cbl --mode multi_ai --provider openai
```

**Características**:
- Análise paralela com múltiplos LLMs
- Validação cruzada de resultados
- Maior confiabilidade e precisão
- Requer pelo menos 1 provedor externo configurado

### 2. Modo Tradicional

Análise baseada em regras sem dependência de LLM.

```bash
python3 main.py programa.cbl --mode traditional
```

**Características**:
- Não requer configuração de LLM
- Análise rápida e determinística
- Baseada em padrões COBOL conhecidos
- Ideal para análises estruturais básicas

### 3. Modo Automático (Padrão)

Seleciona automaticamente o melhor modo baseado na disponibilidade de provedores.

```bash
python3 main.py programa.cbl --mode auto
```

**Lógica de seleção**:
1. Se provedores LLM disponíveis → Multi-IA
2. Se apenas extratores disponíveis → Híbrido
3. Caso contrário → Tradicional

## Opções de Linha de Comando

### Sintaxe Básica

```bash
python3 main.py [arquivos] [opções]
```

### Opções Principais

| Opção | Descrição | Exemplo |
|-------|-----------|---------|
| `--status` | Verifica status do sistema | `python3 main.py --status` |
| `--mode` | Define modo de análise | `--mode multi_ai` |
| `--provider` | Especifica provedor LLM | `--provider openai` |
| `--audience` | Define audiência do relatório | `--audience technical` |
| `--output` | Diretório de saída | `--output resultados` |
| `--copybooks` | Arquivo de copybooks | `--copybooks books.txt` |
| `--config` | Arquivo de configuração | `--config custom.yaml` |
| `--verbose` | Logging detalhado | `--verbose` |
| `--quiet` | Logging mínimo | `--quiet` |
| `--demo` | Modo demonstração | `--demo` |

### Modos de Análise

- `auto`: Seleção automática (padrão)
- `multi_ai`: Análise Multi-IA
- `traditional`: Análise tradicional

### Tipos de Audiência

- `executive`: Relatório executivo
- `technical`: Relatório técnico detalhado
- `business`: Foco em regras de negócio
- `implementation`: Guia de reimplementação
- `combined`: Relatório completo (padrão)

### Provedores Disponíveis

- `openai`: OpenAI GPT-4
- `copilot`: GitHub Copilot
- `luzia`: LuzIA Corporativo
- `enhanced_mock`: Mock avançado
- `mock`: Mock básico

## Exemplos de Uso

### 1. Análise Básica

```bash
# Análise de um programa individual
python3 main.py examples/LHAN0542_TESTE.cbl

# Análise com provedor específico
python3 main.py examples/LHAN0542_TESTE.cbl --provider openai

# Análise com saída personalizada
python3 main.py examples/LHAN0542_TESTE.cbl --output meus_resultados
```

### 2. Análise de Múltiplos Programas

```bash
# Análise de arquivo com múltiplos programas
python3 main.py examples/fontes.txt --mode multi_ai

# Análise com copybooks
python3 main.py examples/fontes.txt --copybooks examples/BOOKS.txt
```

### 3. Análise por Audiência

```bash
# Relatório executivo
python3 main.py programa.cbl --audience executive

# Relatório técnico detalhado
python3 main.py programa.cbl --audience technical

# Guia de reimplementação
python3 main.py programa.cbl --audience implementation
```

### 4. Análise com Logging Detalhado

```bash
# Ver prompts enviados aos LLMs
python3 main.py programa.cbl --verbose --provider openai

# Logging mínimo
python3 main.py programa.cbl --quiet
```

### 5. Verificação de Status

```bash
# Status completo do sistema
python3 main.py --status

# Verificar provedores configurados
python3 main.py --status | grep -A 10 "Providers LLM"
```

### 6. Modo Demonstração

```bash
# Executar demonstração completa
python3 main.py --demo

# Demonstração com provedor específico
python3 main.py --demo --provider enhanced_mock
```

## Configuração Avançada

### Configuração de Performance

```yaml
# config/config.yaml
performance:
  enable_cache: true
  cache_duration: 3600  # 1 hora
  cache_size_limit: "500MB"
  batch_size: 5
  max_concurrent_requests: 2
  request_timeout: 300
  optimize_prompts: true
  compress_responses: true
  lazy_loading: true
```

### Configuração de Segurança

```yaml
# config/config.yaml
security:
  sanitize_output: true
  mask_sensitive_data: true
  remove_sensitive_data: true
  audit_logging: true
  max_file_size: "100MB"
  max_analysis_time: 1800  # 30 minutos
  allowed_extensions: [".cbl", ".cob", ".txt", ".dat"]
  sensitive_patterns:
    - "PASSWORD"
    - "TOKEN"
    - "SECRET"
    - "KEY"
    - "CPF"
    - "CNPJ"
```

### Configuração de Análise

```yaml
# config/config.yaml
analysis:
  max_programs: 1000
  timeout_per_program: 300
  parallel_processing: false
  enhanced_analysis:
    enabled: true
    detailed_analysis: true
    business_context: true
    technical_depth: "maximum"
    include_complexity_metrics: true
    include_dependency_analysis: true
    include_security_analysis: true
```

### Configuração de Relatórios

```yaml
# config/config.yaml
reporting:
  formats: ["markdown", "json"]
  include_metrics: true
  include_statistics: true
  include_recommendations: true
  include_code_examples: true
  include_diagrams: true
  detailed_sections: true
  sections:
    executive_summary: true
    functional_analysis: true
    business_rules_detailed: true
    technical_analysis: true
    structure_analysis: true
    quality_assessment: true
    recommendations: true
    reimplementation_guide: true
```

## Logging e Monitoramento

### Configuração de Logging

```yaml
# config/config.yaml
logging:
  level: "INFO"  # DEBUG, INFO, WARNING, ERROR
  detailed_provider_logs: true
  include_token_usage: true
  include_response_times: true
  include_analysis_metrics: true
  format: "%(asctime)s - %(name)s - %(levelname)s - %(message)s"
  file: "cobol_analysis_engine_v1.0.1.log"
  max_file_size: "50MB"
  backup_count: 5
  file_logging:
    enabled: true
    max_size_mb: 50
    backup_count: 5
  console_logging:
    enabled: true
    colored_output: true
    show_progress: true
```

### Visualização de Prompts

O sistema v1.0.1 inclui logging detalhado dos prompts enviados aos LLMs:

```bash
# Executar com logging verbose para ver prompts
python3 main.py programa.cbl --verbose --provider openai
```

**Exemplo de saída de logging**:
```
================================================================================
PROMPT ENVIADO PARA OPENAI:
================================================================================
Modelo: gpt-4
Temperatura: 0.1
Max Tokens: 8000
Tamanho do system prompt: 1250 caracteres
Tamanho do user prompt: 2340 caracteres
--------------------------------------------------------------------------------
SYSTEM PROMPT:
--------------------------------------------------------------------------------
Você é um especialista em análise de código COBOL...
--------------------------------------------------------------------------------
USER PROMPT:
--------------------------------------------------------------------------------
Analise o seguinte programa COBOL...
================================================================================
```

### Monitoramento de Performance

```bash
# Verificar logs de performance
tail -f cobol_analysis_engine_v1.0.1.log | grep -E "(tempo|tokens|performance)"

# Verificar uso de tokens
grep "tokens_used" cobol_analysis_engine_v1.0.1.log

# Verificar tempos de resposta
grep "response_time" cobol_analysis_engine_v1.0.1.log
```

## Solução de Problemas

### Problemas Comuns

#### 1. Provedor LLM não configurado

**Erro**: `Provider 'openai' not configured`

**Solução**:
```bash
export OPENAI_API_KEY="sua_chave"
# ou editar config/config.yaml
```

#### 2. Erro de SSL/TLS

**Erro**: `SSL: CERTIFICATE_VERIFY_FAILED`

**Solução**:
```bash
# Configurar certificado
export REQUESTS_CA_BUNDLE="/path/to/cert.pem"

# Ou no config.yaml para LuzIA
ssl_cert_path: "/path/to/cert.pem"
```

#### 3. Timeout de conexão

**Erro**: `Connection timeout`

**Solução**:
```yaml
# Aumentar timeout no config.yaml
ai:
  providers:
    openai:
      timeout: 300  # 5 minutos
```

#### 4. Arquivo não encontrado

**Erro**: `File not found: programa.cbl`

**Solução**:
```bash
# Verificar caminho do arquivo
ls -la programa.cbl

# Usar caminho absoluto
python3 main.py /caminho/completo/programa.cbl
```

#### 5. Memória insuficiente

**Erro**: `MemoryError`

**Solução**:
```yaml
# Reduzir batch_size no config.yaml
performance:
  batch_size: 1
  max_concurrent_requests: 1
```

### Diagnóstico

#### Verificar Status do Sistema

```bash
python3 main.py --status
```

#### Verificar Configuração

```bash
# Verificar sintaxe do YAML
python3 -c "import yaml; yaml.safe_load(open('config/config.yaml'))"

# Verificar variáveis de ambiente
env | grep -E "(OPENAI|GITHUB|LUZIA)"
```

#### Teste de Conectividade

```bash
# Testar com mock (sempre funciona)
python3 main.py examples/LHAN0542_TESTE.cbl --provider enhanced_mock

# Testar provedor específico
python3 main.py examples/LHAN0542_TESTE.cbl --provider openai --verbose
```

### Logs de Debug

```bash
# Habilitar debug completo
export PYTHONPATH="."
python3 -c "
import logging
logging.basicConfig(level=logging.DEBUG)
from main import main
main()
" examples/LHAN0542_TESTE.cbl --verbose
```

## Referência de Configuração

### Estrutura Completa do config.yaml

```yaml
# Sistema de Análise COBOL v1.0.1 - Configuração Completa

# Configurações de IA
ai:
  primary_provider: "openai"
  fallback_providers: ["enhanced_mock", "copilot", "luzia"]
  global_max_tokens: 8000
  providers:
    timeout: 180
    
    openai:
      enabled: true
      api_key: "${OPENAI_API_KEY}"
      model: "gpt-4"
      temperature: 0.1
      max_tokens: 8000
      timeout: 120
      base_url: "https://api.openai.com/v1"
      
    copilot:
      enabled: true
      api_key: "${GITHUB_TOKEN}"
      model: "gpt-4"
      temperature: 0.1
      max_tokens: 8000
      timeout: 120
      base_url: "https://api.githubcopilot.com/chat/completions"
      headers:
        "Authorization": "Bearer ${GITHUB_TOKEN}"
        "Editor-Version": "vscode/1.83.0"
        "Editor-Plugin-Version": "copilot-chat/0.8.0"
        "User-Agent": "GitHubCopilotChat/0.8.0"
    
    luzia:
      enabled: true
      client_id: '${LUZIA_CLIENT_ID:-7153e7d9-d0a9-42ac-8a1c-72bf903155fa}'
      client_secret: '${LUZIA_CLIENT_SECRET:-90A337BtXt9vH9zXAqc5500gNozjR7xJ}'
      auth_url: 'https://login.azure.paas.santanderbr.pre.corp/auth/realms/corp/protocol/openid-connect/token'
      api_url: 'https://gut-api-aws.santanderbr.dev.corp/genai_services/v1/'
      model: 'azure-gpt-4o-mini'
      temperature: 0.1
      max_tokens: 4000
      timeout: 180
      ssl_cert_path: null
      retry:
        max_attempts: 5
        base_delay: 2.0
        max_delay: 60.0
        backoff_multiplier: 2.0
        requests_per_minute: 8
    
    enhanced_mock:
      enabled: true
      model: "enhanced-mock-v1.0.1"
      temperature: 0.1
      max_tokens: 8000
      timeout: 30
      quality_level: "high"
      include_metrics: true
      realistic_responses: true

# Configurações de análise
analysis:
  max_programs: 1000
  timeout_per_program: 300
  parallel_processing: false
  enhanced_analysis:
    enabled: true
    detailed_analysis: true
    business_context: true
    technical_depth: "maximum"
    include_complexity_metrics: true
    include_dependency_analysis: true
    include_security_analysis: true
  business_rules:
    extract_detailed_descriptions: true
    categorize_by_type: true
    include_regulatory_context: true
    generate_compliance_notes: true
    identify_critical_paths: true
    extract_decision_logic: true
    include_data_validation_rules: true
  structure_analysis:
    identify_copybooks: true
    map_data_structures: true
    analyze_file_operations: true
    identify_subroutines: true
    map_program_flow: true
    identify_error_handling: true
  code_quality:
    calculate_complexity_metrics: true
    identify_code_smells: true
    suggest_improvements: true
    assess_maintainability: true
  documentation:
    generate_executive_summary: true
    include_technical_diagrams: true
    detailed_code_analysis: true
    business_impact_assessment: true
    include_reimplementation_guide: true
    include_test_scenarios: true
    include_migration_notes: true

# Configurações de relatórios
reporting:
  formats: ["markdown", "json"]
  include_metrics: true
  include_statistics: true
  include_recommendations: true
  include_code_examples: true
  include_diagrams: true
  detailed_sections: true
  sections:
    executive_summary: true
    functional_analysis: true
    business_rules_detailed: true
    technical_analysis: true
    structure_analysis: true
    data_flow_analysis: true
    complexity_analysis: true
    quality_assessment: true
    security_analysis: true
    performance_analysis: true
    recommendations: true
    reimplementation_guide: true
    test_scenarios: true
    migration_notes: true
    regulatory_compliance: true
  quality_metrics:
    calculate_reimplementation_score: true
    include_confidence_levels: true
    provide_quality_gates: true
    include_risk_assessment: true

# Configurações de logging
logging:
  level: "INFO"
  detailed_provider_logs: true
  include_token_usage: true
  include_response_times: true
  include_analysis_metrics: true
  format: "%(asctime)s - %(name)s - %(levelname)s - %(message)s"
  file: "cobol_analysis_engine_v1.0.1.log"
  max_file_size: "50MB"
  backup_count: 5
  file_logging:
    enabled: true
    max_size_mb: 50
    backup_count: 5
  console_logging:
    enabled: true
    colored_output: true
    show_progress: true

# Configurações de saída
output:
  default_format: "markdown"
  include_timestamps: true
  include_version_info: true
  include_metadata: true
  include_statistics: true
  include_prompts: false
  enable_pdf: false
  reports:
    consolidate_results: true
    include_statistics: true
    include_recommendations: true
    include_executive_summary: true
    include_detailed_analysis: true
  default_sections:
    - "executive_summary"
    - "functional_analysis"
    - "technical_analysis"
    - "business_rules"
    - "structure_analysis"
    - "quality_assessment"
    - "recommendations"
    - "reimplementation_guide"

# Configurações de segurança
security:
  sanitize_output: true
  mask_sensitive_data: true
  remove_sensitive_data: true
  audit_logging: true
  max_file_size: "100MB"
  max_analysis_time: 1800
  allowed_extensions: [".cbl", ".cob", ".txt", ".dat"]
  sensitive_patterns:
    - "PASSWORD"
    - "TOKEN"
    - "SECRET"
    - "KEY"
    - "CPF"
    - "CNPJ"
    - "CREDIT"
    - "ACCOUNT"

# Configurações de performance
performance:
  enable_cache: true
  cache_duration: 3600
  cache_size_limit: "500MB"
  batch_size: 5
  max_concurrent_requests: 2
  request_timeout: 300
  optimize_prompts: true
  compress_responses: true
  lazy_loading: true

# Configurações de validação
validation:
  validate_cobol_syntax: true
  validate_file_structure: true
  validate_encoding: true
  min_reimplementation_score: 40
  min_confidence_level: 0.6
  require_business_rules: true
  validate_generated_docs: true
  check_completeness: true
  verify_consistency: true

# Perfis de análise
analysis_profiles:
  complete:
    depth: "maximum"
    include_all_sections: true
    detailed_business_rules: true
    technical_diagrams: true
  quick:
    depth: "standard"
    essential_sections_only: true
    basic_business_rules: true
    no_diagrams: true
  production:
    depth: "detailed"
    include_security_analysis: true
    include_performance_analysis: true
    include_compliance_check: true

# Configurações de compatibilidade
compatibility:
  cobol_versions: ["COBOL-85", "COBOL-2002", "COBOL-2014"]
  encoding_support: ["UTF-8", "ISO-8859-1", "CP1252"]
  platform_support: ["Linux", "Windows", "macOS"]

# Configurações experimentais
experimental:
  ai_assisted_refactoring: false
  automated_test_generation: false
  code_similarity_detection: false
  pattern_recognition: true

# Configurações de compatibilidade v1.0.0
providers:
  primary: "openai"
  fallback: "enhanced_mock"
```

### Variáveis de Ambiente Suportadas

| Variável | Descrição | Exemplo |
|----------|-----------|---------|
| `OPENAI_API_KEY` | Chave da API OpenAI | `sk-proj-...` |
| `GITHUB_TOKEN` | Token do GitHub | `ghp_...` |
| `LUZIA_CLIENT_ID` | Client ID do LuzIA | `7153e7d9-...` |
| `LUZIA_CLIENT_SECRET` | Client Secret do LuzIA | `90A337BtXt9v...` |
| `LUZIA_SSL_CERT_PATH` | Caminho do certificado SSL | `/path/to/cert.pem` |
| `REQUESTS_CA_BUNDLE` | Bundle de certificados CA | `/path/to/ca-bundle.crt` |
| `SSL_CERT_FILE` | Arquivo de certificado SSL | `/path/to/cert.pem` |
| `SSL_CERT_DIR` | Diretório de certificados | `/path/to/certs/` |
| `PYTHONHTTPSVERIFY` | Verificação HTTPS | `0` (desabilitar) |

## Conclusão

O Sistema de Análise COBOL v1.0.1 oferece uma solução completa e flexível para análise de código COBOL, com suporte a múltiplos provedores LLM, configuração SSL avançada, e logging detalhado dos prompts enviados aos modelos.

Para suporte adicional ou questões específicas, consulte os logs do sistema ou execute o comando `--status` para diagnóstico completo.

---

**Sistema de Análise COBOL v1.0.1**  
*Manual Completo - Atualizado em 19/09/2025*
