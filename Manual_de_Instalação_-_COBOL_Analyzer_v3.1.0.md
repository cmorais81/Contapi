# Manual de Instalação - COBOL Analyzer v3.1.0

## Guia Completo de Instalação e Configuração

### Requisitos do Sistema

#### Requisitos Mínimos
- **Sistema Operacional**: Windows 10+, Linux (Ubuntu 18.04+), macOS 10.15+
- **Python**: Versão 3.8 ou superior
- **Memória RAM**: 4GB mínimo
- **Espaço em Disco**: 500MB para instalação completa
- **Conexão com Internet**: Para download de dependências e uso de APIs de IA

#### Requisitos Recomendados
- **Memória RAM**: 8GB ou superior
- **Processador**: Multi-core para melhor performance
- **SSD**: Para acesso mais rápido aos arquivos

### Métodos de Instalação

## Método 1: Instalação Direta (Recomendado)

### Passo 1: Extrair o Pacote
```bash
# Extrair o arquivo
tar -xzf COBOL_ANALYZER_v3.1.0_FINAL.tar.gz

# Entrar no diretório
cd cobol_analyzer_EXCELENCIA
```

### Passo 2: Verificar Python
```bash
# Verificar versão do Python
python3 --version

# Deve mostrar Python 3.8 ou superior
# Se não tiver Python 3.8+, instale antes de continuar
```

### Passo 3: Instalar Dependências
```bash
# Instalar dependências básicas
pip3 install -r requirements.txt

# Ou usar pip se python3 não estiver disponível
pip install -r requirements.txt
```

### Passo 4: Testar Instalação
```bash
# Testar se a aplicação funciona
python3 main.py --help

# Verificar status dos provedores
python3 main.py --status
```

### Passo 5: Teste Básico
```bash
# Executar análise de teste
python3 main.py --fontes examples/fontes.txt --models enhanced_mock --output teste

# Verificar se os arquivos foram gerados
ls teste/
```

## Método 2: Instalação via pip

### Passo 1: Extrair e Instalar
```bash
# Extrair o pacote
tar -xzf COBOL_ANALYZER_v3.1.0_FINAL.tar.gz
cd cobol_analyzer_EXCELENCIA

# Instalar como pacote Python
pip3 install .
```

### Passo 2: Usar Comando Instalado
```bash
# Testar comando instalado
cobol-analyzer --help

# Executar análise
cobol-analyzer --fontes examples/fontes.txt --models enhanced_mock
```

## Método 3: Ambiente Virtual (Recomendado para Desenvolvimento)

### Passo 1: Criar Ambiente Virtual
```bash
# Criar ambiente virtual
python3 -m venv cobol_analyzer_env

# Ativar ambiente virtual
# No Linux/macOS:
source cobol_analyzer_env/bin/activate

# No Windows:
cobol_analyzer_env\Scripts\activate
```

### Passo 2: Instalar no Ambiente Virtual
```bash
# Extrair pacote
tar -xzf COBOL_ANALYZER_v3.1.0_FINAL.tar.gz
cd cobol_analyzer_EXCELENCIA

# Instalar dependências
pip install -r requirements.txt

# Testar instalação
python main.py --help
```

### Configuração de Provedores de IA

#### Configuração Básica (Usando Mock)
```bash
# Não requer configuração adicional
# O provider 'enhanced_mock' funciona sem chaves de API
python3 main.py --fontes examples/fontes.txt --models enhanced_mock
```

#### Configuração OpenAI
```bash
# Editar arquivo de configuração
cp config/config.yaml config/config_local.yaml

# Adicionar sua chave OpenAI no config_local.yaml:
# providers:
#   openai:
#     api_key: "sk-sua-chave-aqui"
```

#### Configuração AWS Bedrock
```yaml
# No config_local.yaml:
providers:
  aws_bedrock:
    region: "us-east-1"
    access_key: "sua_access_key"
    secret_key: "sua_secret_key"
```

#### Configuração Azure OpenAI
```yaml
# No config_local.yaml:
providers:
  azure:
    api_key: "sua_chave_azure"
    endpoint: "https://seu-endpoint.openai.azure.com/"
    api_version: "2024-02-15-preview"
```

### Verificação da Instalação

#### Teste Completo
```bash
# 1. Verificar help
python3 main.py --help

# 2. Verificar status dos provedores
python3 main.py --status

# 3. Teste com mock (sem necessidade de API)
python3 main.py --fontes examples/fontes.txt --models enhanced_mock

# 4. Teste CLI
python3 cli.py --help

# 5. Se instalado via pip
cobol-analyzer --help
```

#### Verificar Logs
```bash
# Verificar se logs são gerados
ls logs/

# Ver conteúdo do log mais recente
tail -f logs/cobol_to_docs_*.log
```

### Solução de Problemas Comuns

#### Erro: "ModuleNotFoundError"
```bash
# Solução 1: Adicionar src ao PYTHONPATH
export PYTHONPATH=$PYTHONPATH:$(pwd)/src
python3 main.py --help

# Solução 2: Reinstalar dependências
pip3 install -r requirements.txt --force-reinstall

# Solução 3: Usar ambiente virtual
python3 -m venv novo_env
source novo_env/bin/activate
pip install -r requirements.txt
```

#### Erro: "Permission denied"
```bash
# No Linux/macOS, dar permissão de execução
chmod +x main.py cli.py

# Ou executar com python explicitamente
python3 main.py --help
```

#### Erro: "No module named 'numpy'"
```bash
# Instalar dependências científicas
pip3 install numpy scikit-learn

# Ou instalar todas as dependências
pip3 install -r requirements.txt
```

#### Erro de Configuração de IA
```bash
# Usar modelo mock para testes
python3 main.py --fontes examples/fontes.txt --models enhanced_mock

# Verificar configuração
python3 main.py --status
```

### Configuração Avançada

#### Personalizar Diretórios
```bash
# Criar estrutura personalizada
mkdir -p ~/cobol_analyzer/{input,output,config}

# Copiar arquivos de configuração
cp config/* ~/cobol_analyzer/config/

# Usar configuração personalizada
python3 main.py --fontes ~/cobol_analyzer/input/programas.txt --output ~/cobol_analyzer/output
```

#### Configurar Logging
```bash
# Aumentar nível de log para depuração
python3 main.py --fontes examples/fontes.txt --log-level DEBUG

# Configurar log personalizado no config.yaml:
# logging:
#   level: INFO
#   file: logs/custom.log
```

#### Otimização de Performance
```bash
# Para sistemas com pouca memória
export PYTHONHASHSEED=0
python3 main.py --fontes examples/fontes.txt --models enhanced_mock

# Para processamento em lote
python3 main.py --fontes lista_grande.txt --models enhanced_mock --output batch_results
```

### Atualização

#### Atualizar para Nova Versão
```bash
# Fazer backup da configuração atual
cp config/config.yaml config/config_backup.yaml

# Extrair nova versão
tar -xzf COBOL_ANALYZER_v3.2.0_FINAL.tar.gz

# Restaurar configuração
cp config/config_backup.yaml cobol_analyzer_EXCELENCIA/config/config_local.yaml

# Reinstalar dependências
cd cobol_analyzer_EXCELENCIA
pip3 install -r requirements.txt --upgrade
```

### Desinstalação

#### Remover Instalação Direta
```bash
# Simplesmente remover o diretório
rm -rf cobol_analyzer_EXCELENCIA
```

#### Remover Instalação via pip
```bash
# Desinstalar pacote
pip3 uninstall cobol-analyzer

# Remover ambiente virtual (se usado)
rm -rf cobol_analyzer_env
```

### Suporte e Ajuda

#### Recursos de Ajuda
- **Help da aplicação**: `python3 main.py --help`
- **Status do sistema**: `python3 main.py --status`
- **Logs detalhados**: `--log-level DEBUG`
- **Documentação**: `README.md` e pasta `docs/`

#### Informações do Sistema
```bash
# Verificar versão Python
python3 --version

# Verificar pacotes instalados
pip3 list | grep -E "(pyyaml|requests|numpy|scikit-learn)"

# Verificar espaço em disco
df -h .

# Verificar memória
free -h  # Linux
# ou
vm_stat  # macOS
```

#### Contato para Suporte
- **Documentação**: Consulte README.md e docs/
- **Logs**: Verifique pasta logs/ para diagnóstico
- **Exemplos**: Use pasta examples/ como referência

---

**Instalação Concluída com Sucesso!**

Agora você pode usar o COBOL Analyzer para analisar seus programas COBOL e gerar documentação profissional automaticamente.
