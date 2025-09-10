# COBOL AI Engine v2.7.0 - Release Notes

**Data de Lançamento**: 2025-09-10

Esta versão introduz suporte a **Databricks** e **AWS Bedrock**, expandindo significativamente as opções de provedores de IA disponíveis. Agora o sistema suporta 6 provedores diferentes, oferecendo máxima flexibilidade para análise de código COBOL.

## 🆕 Novas Funcionalidades

### 🚀 Provedor Databricks
- **Integração Completa**: Suporte a Databricks Model Serving
- **Foundation Models**: Llama 3.1 405B, 70B, 8B Instruct e outros
- **Autenticação**: Personal Access Token
- **Configuração**: `config_databricks.yaml`

### ☁️ Provedor AWS Bedrock
- **Integração Completa**: Suporte a Amazon Bedrock
- **Foundation Models**: Claude 3 Sonnet, Haiku, Llama 3, Titan e outros
- **Autenticação**: AWS Credentials (Access Key + Secret Key)
- **Configuração**: `config_bedrock.yaml`

### 🔧 Sistema de Provedores Expandido
- **6 Provedores Disponíveis**: LuzIA Real, Databricks, Bedrock, Enhanced Mock, Basic, LuzIA Mock
- **Configuração Modular**: Cada provedor pode ser habilitado/desabilitado independentemente
- **Fallback Robusto**: Sistema de fallback aprimorado com múltiplos provedores

## 📋 Configurações Adicionadas

### config_databricks.yaml
```yaml
ai:
  primary_provider: "databricks"
  providers:
    databricks:
      enabled: true
      workspace_url: "${DATABRICKS_WORKSPACE_URL}"
      access_token: "${DATABRICKS_ACCESS_TOKEN}"
      model_endpoint: "databricks-meta-llama-3-1-405b-instruct"
      model: "llama-3.1-405b-instruct"
```

### config_bedrock.yaml
```yaml
ai:
  primary_provider: "bedrock"
  providers:
    bedrock:
      enabled: true
      region: "${AWS_REGION:-us-east-1}"
      model_id: "anthropic.claude-3-sonnet-20240229-v1:0"
      model: "claude-3-sonnet"
```

### config_complete.yaml
- Configuração com todos os 6 provedores disponíveis
- Ideal para customização avançada
- Provedores desabilitados por padrão (exceto Enhanced Mock + Basic)

## 🔄 Melhorias no Sistema

### Autenticação Flexível
- **Databricks**: Personal Access Token via variáveis de ambiente
- **AWS Bedrock**: AWS Credentials (Access Key, Secret Key, Session Token)
- **LuzIA Real**: OAuth2 Client Credentials (ambiente corporativo)
- **Mock Providers**: Sem autenticação necessária

### Fallback Aprimorado
```yaml
ai:
  primary_provider: "databricks"
  fallback_providers: 
    - "bedrock"
    - "luzia_real"
    - "enhanced_mock"
    - "basic"
```

### Controle de Tokens
- Limites por requisição, hora e dia para cada provedor
- Monitoramento de uso por provedor
- Estimativa de tokens para provedores sem métricas nativas

## 🎯 Casos de Uso

### Análise com Foundation Models Avançados
```bash
# Databricks com Llama 3.1 405B
python main.py --config config/config_databricks.yaml --fontes examples/fontes.txt --output resultado

# AWS Bedrock com Claude 3 Sonnet
python main.py --config config/config_bedrock.yaml --fontes examples/fontes.txt --output resultado
```

### Ambiente Corporativo
```bash
# LuzIA Real (Santander)
python main.py --config config/config_luzia_real.yaml --fontes examples/fontes.txt --output resultado
```

### Desenvolvimento e Testes
```bash
# Configuração segura (sempre funciona)
python main.py --config config/config_safe.yaml --fontes examples/fontes.txt --output resultado
```

## 📦 Dependências Adicionadas

### Para Databricks
```bash
pip install databricks-sdk>=0.18.0
```

### Para AWS Bedrock
```bash
pip install boto3>=1.34.0
pip install botocore>=1.34.0
```

## 🔧 Configuração de Credenciais

### Databricks
```bash
export DATABRICKS_WORKSPACE_URL="https://seu-workspace.cloud.databricks.com"
export DATABRICKS_ACCESS_TOKEN="seu_personal_access_token"
```

### AWS Bedrock
```bash
export AWS_REGION="us-east-1"
export AWS_ACCESS_KEY_ID="seu_access_key"
export AWS_SECRET_ACCESS_KEY="seu_secret_key"
# Opcional para sessões temporárias
export AWS_SESSION_TOKEN="seu_session_token"
```

### LuzIA Real (Santander)
```bash
export LUZIA_CLIENT_ID="seu_client_id"
export LUZIA_CLIENT_SECRET="seu_client_secret"
```

## 📚 Documentação Atualizada

### Novos Manuais
- **docs/MANUAL_PROVEDORES.md**: Manual completo dos 6 provedores
- **GUIA_INICIO_RAPIDO.md**: Atualizado com todos os provedores
- **README.md**: Atualizado para v2.7.0

### Manuais Existentes Atualizados
- **docs/MANUAL_USUARIO.md**: Incluindo novos provedores
- **docs/MANUAL_CONFIGURACAO.md**: Configurações expandidas
- **CHANGELOG.md**: Histórico completo de mudanças

## 🧪 Validação e Testes

### Comandos Testados
```bash
# Verificar versão
python main.py --version  # v2.7.0

# Status com todos os provedores
python main.py --config config/config_complete.yaml --status

# Análise funcional
python main.py --config config/config_safe.yaml --fontes examples/fontes.txt --output teste
```

### Compatibilidade
- ✅ **Python 3.8+**: Totalmente compatível
- ✅ **Múltiplos OS**: Windows, Linux, macOS
- ✅ **Fallback Garantido**: Sistema nunca falha
- ✅ **Retrocompatibilidade**: Configurações v2.6.x funcionam

## 🔄 Migração da v2.6.x

### Compatibilidade Total
- Todas as configurações v2.6.x continuam funcionando
- Novos provedores são opcionais
- Sistema mantém fallback para Enhanced Mock + Basic

### Para Usar Novos Provedores
1. **Instalar dependências**: `pip install -r requirements.txt`
2. **Configurar credenciais**: Variáveis de ambiente específicas
3. **Usar configurações específicas**: `config_databricks.yaml` ou `config_bedrock.yaml`

## 📊 Comparação de Provedores

| Provedor | Tipo | Modelos | Autenticação | Uso Recomendado |
|----------|------|---------|--------------|-----------------|
| **Databricks** | Cloud | Llama 3.1, Foundation Models | Personal Access Token | Análise Avançada |
| **AWS Bedrock** | Cloud | Claude, Llama, Titan | AWS Credentials | Foundation Models |
| **LuzIA Real** | Corporativo | GPT-4o, Azure OpenAI | OAuth2 | Ambiente Santander |
| **Enhanced Mock** | Simulado | Mock GPT-4 | Nenhuma | Desenvolvimento |
| **Basic** | Fallback | Básico | Nenhuma | Fallback Final |
| **LuzIA Mock** | Simulado | Mock LuzIA | Nenhuma | Testes LuzIA |

## 🎯 Próximos Passos

### Funcionalidades Futuras
- Suporte a mais modelos Foundation
- Integração com Azure OpenAI
- Métricas avançadas de performance
- Interface web para configuração

### Otimizações Planejadas
- Cache de respostas
- Processamento paralelo
- Análise incremental
- Relatórios avançados

## 📞 Suporte

### Documentação
- `GUIA_INICIO_RAPIDO.md`: Início em 3 passos
- `docs/MANUAL_PROVEDORES.md`: Manual completo dos provedores
- `docs/MANUAL_USUARIO.md`: Manual completo do usuário

### Troubleshooting
- Use sempre `config_safe.yaml` para testes iniciais
- Verifique credenciais com `--status`
- Consulte logs detalhados com `--log-level DEBUG`

**Esta versão oferece máxima flexibilidade com 6 provedores de IA diferentes!**

