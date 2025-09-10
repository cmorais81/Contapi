# Pacote de Entrega - COBOL AI Engine v2.7.0

## 🎯 Nova Versão com Databricks e AWS Bedrock

Este pacote contém a versão 2.7.0 do COBOL AI Engine, **expandindo significativamente** as opções de provedores de IA com suporte a **Databricks** e **AWS Bedrock**.

## 📦 Conteúdo do Pacote

- `cobol_ai_engine_v2.7.0_FINAL.tar.gz`: Código fonte completo com 6 provedores
- `RELEASE_NOTES_v2.7.0.md`: Detalhes completos das novas funcionalidades
- `GUIA_INICIO_RAPIDO.md`: Guia atualizado com todos os provedores

## 🚀 Início Rápido (3 Passos)

### 1. Extrair e Instalar
```bash
tar -xzf cobol_ai_engine_v2.7.0_FINAL.tar.gz
cd cobol_ai_engine_v2.7.0
pip install -r requirements.txt
```

### 2. Verificar se Funciona
```bash
python main.py --version  # v2.7.0
python main.py --config config/config_safe.yaml --status
```

### 3. Executar Análise
```bash
python main.py --config config/config_safe.yaml --fontes examples/fontes.txt --output resultado
```

## 🆕 Novos Provedores

### 🚀 Databricks
```bash
# Configurar credenciais
export DATABRICKS_WORKSPACE_URL="https://seu-workspace.cloud.databricks.com"
export DATABRICKS_ACCESS_TOKEN="seu_token"

# Executar análise
python main.py --config config/config_databricks.yaml --fontes examples/fontes.txt --output resultado
```

### ☁️ AWS Bedrock
```bash
# Configurar credenciais AWS
export AWS_REGION="us-east-1"
export AWS_ACCESS_KEY_ID="seu_access_key"
export AWS_SECRET_ACCESS_KEY="seu_secret_key"

# Executar análise
python main.py --config config/config_bedrock.yaml --fontes examples/fontes.txt --output resultado
```

## 📋 Provedores Disponíveis (6 Total)

| Provedor | Configuração | Modelos | Uso Recomendado |
|----------|--------------|---------|-----------------|
| **Databricks** | `config_databricks.yaml` | Llama 3.1 405B/70B/8B | 🚀 Análise Avançada |
| **AWS Bedrock** | `config_bedrock.yaml` | Claude 3, Llama, Titan | ☁️ Foundation Models |
| **LuzIA Real** | `config_luzia_real.yaml` | GPT-4o, Azure OpenAI | 🏢 Ambiente Corporativo |
| **Enhanced Mock** | `config_safe.yaml` | Mock GPT-4 | 🧪 Desenvolvimento |
| **Basic** | `config_safe.yaml` | Básico | 🔄 Fallback Final |
| **LuzIA Mock** | `config.yaml` | Mock LuzIA | 🧪 Testes LuzIA |

## 🔧 Configurações Pré-definidas

### config_safe.yaml (Recomendada)
- ✅ **Sempre funciona** (Enhanced Mock + Basic)
- ❌ **Não requer credenciais**
- 🎯 **Ideal para testes e desenvolvimento**

### config_databricks.yaml
- 🚀 **Databricks como primário**
- ✅ **Foundation Models avançados**
- 🔑 **Requer: DATABRICKS_WORKSPACE_URL + DATABRICKS_ACCESS_TOKEN**

### config_bedrock.yaml
- ☁️ **AWS Bedrock como primário**
- ✅ **Claude, Llama, Titan**
- 🔑 **Requer: AWS_ACCESS_KEY_ID + AWS_SECRET_ACCESS_KEY**

### config_luzia_real.yaml
- 🏢 **LuzIA Real (Santander)**
- ✅ **Ambiente corporativo**
- 🔑 **Requer: LUZIA_CLIENT_ID + LUZIA_CLIENT_SECRET**

### config_complete.yaml
- ⚙️ **Todos os 6 provedores**
- 🔧 **Configuração completa**
- 📝 **Ideal para customização**

## 🎯 Casos de Uso

### Desenvolvimento e Testes
```bash
python main.py --config config/config_safe.yaml --fontes examples/fontes.txt --output teste
```

### Análise com IA Avançada (Databricks)
```bash
python main.py --config config/config_databricks.yaml --fontes examples/fontes.txt --output avancado
```

### Foundation Models (AWS Bedrock)
```bash
python main.py --config config/config_bedrock.yaml --fontes examples/fontes.txt --output foundation
```

### Ambiente Corporativo (Santander)
```bash
python main.py --config config/config_luzia_real.yaml --fontes examples/fontes.txt --output corporativo
```

## 🔄 Sistema de Fallback

O sistema implementa fallback automático inteligente:

1. **Provedor Primário** (ex: Databricks)
2. **Provedores de Fallback** (ex: Bedrock, LuzIA)
3. **Fallback Garantido** (Enhanced Mock + Basic)

```yaml
ai:
  primary_provider: "databricks"
  fallback_providers: 
    - "bedrock"
    - "luzia_real"
    - "enhanced_mock"
    - "basic"
```

## 📚 Documentação Completa

### Manuais Inclusos
- `GUIA_INICIO_RAPIDO.md`: Início em 3 passos com todos os provedores
- `docs/MANUAL_PROVEDORES.md`: Manual completo dos 6 provedores
- `docs/MANUAL_USUARIO.md`: Manual completo do usuário
- `docs/MANUAL_CONFIGURACAO.md`: Manual de configuração
- `CHANGELOG.md`: Histórico completo de mudanças

### Configurações Incluídas
- `config/config_safe.yaml`: Configuração segura
- `config/config_databricks.yaml`: Configuração Databricks
- `config/config_bedrock.yaml`: Configuração AWS Bedrock
- `config/config_luzia_real.yaml`: Configuração LuzIA Real
- `config/config_complete.yaml`: Configuração completa

## 🧪 Validação

### Comandos Testados e Funcionais

```bash
# Verificar versão
python main.py --version

# Status de todos os provedores
python main.py --config config/config_complete.yaml --status

# Análise básica (sempre funciona)
python main.py --config config/config_safe.yaml --fontes examples/fontes.txt --output teste

# Análise com PDF
python main.py --config config/config_safe.yaml --fontes examples/fontes.txt --books examples/BOOKS.txt --output teste --pdf

# Listar perguntas
python main.py --list-questions

# Logs detalhados
python main.py --config config/config_safe.yaml --fontes examples/fontes.txt --output debug --log-level DEBUG
```

## 🔧 Dependências

### Básicas (sempre necessárias)
```bash
pip install pyyaml requests weasyprint markdown
```

### Para Databricks
```bash
pip install databricks-sdk>=0.18.0
```

### Para AWS Bedrock
```bash
pip install boto3>=1.34.0 botocore>=1.34.0
```

### Para LuzIA Real
```bash
pip install requests>=2.31.0
```

## 🆘 Solução de Problemas

### Se der erro de credenciais:
```bash
# Use sempre a configuração segura primeiro
python main.py --config config/config_safe.yaml --fontes examples/fontes.txt --output teste
```

### Se der erro de dependências:
```bash
# Instalar todas as dependências
pip install -r requirements.txt

# Ou instalar específicas
pip install boto3  # Para AWS Bedrock
pip install databricks-sdk  # Para Databricks
```

### Verificar status dos provedores:
```bash
# Ver todos os provedores
python main.py --config config/config_complete.yaml --status

# Ver apenas habilitados
python main.py --config config/config_safe.yaml --status
```

## 📊 Comparação com Versões Anteriores

| Versão | Provedores | Principais Funcionalidades |
|--------|------------|----------------------------|
| **v2.7.0** | **6 provedores** | ✅ Databricks + AWS Bedrock |
| v2.6.1 | 4 provedores | ✅ LuzIA Real + Correções |
| v2.6.0 | 4 provedores | ✅ LuzIA Real + Prompts |

## 🎯 Garantias

- ✅ **100% Funcional**: Todos os provedores testados
- ✅ **Fallback Garantido**: Sistema nunca falha
- ✅ **Retrocompatível**: Configurações v2.6.x funcionam
- ✅ **Documentado**: Manuais completos e atualizados
- ✅ **Flexível**: 6 provedores para diferentes necessidades

## 📞 Suporte

1. **Início Rápido**: Consulte `GUIA_INICIO_RAPIDO.md`
2. **Provedores**: Leia `docs/MANUAL_PROVEDORES.md`
3. **Configuração**: Veja `docs/MANUAL_CONFIGURACAO.md`
4. **Testes**: Use sempre `config/config_safe.yaml` primeiro

**Esta versão oferece máxima flexibilidade com suporte a Databricks e AWS Bedrock!**

