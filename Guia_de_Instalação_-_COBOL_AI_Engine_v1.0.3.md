# Guia de Instalação - COBOL AI Engine v1.0.3

## Instalação Rápida

### Pré-requisitos
- Python 3.11 ou superior
- pip (gerenciador de pacotes Python)
- Acesso à internet para APIs de IA

### Passos de Instalação

1. **Extrair o Pacote**
```bash
tar -xzf cobol_ai_engine_v1.0.3.tar.gz
cd cobol_ai_engine_v2.0.0/
```

2. **Instalar Dependências**
```bash
pip install -r requirements.txt
```

3. **Configurar Variáveis de Ambiente**
```bash
# LuzIA (recomendado)
export LUZIA_API_KEY="sua_chave_luzia_aqui"

# OpenAI (opcional)
export OPENAI_API_KEY="sua_chave_openai_aqui"
```

4. **Testar Instalação**
```bash
python main.py --fontes examples/fontes.txt --models "mock_enhanced"
```

## Configuração Detalhada

### Arquivo de Configuração Principal

Edite `config/config.yaml` para configurar os modelos padrão:

```yaml
ai:
  default_models:
    - "claude_3_5_sonnet"
    - "luzia_standard"

providers:
  luzia:
    enabled: true
    auth_url: "https://api.luzia.com/auth"
    endpoint: "https://api.luzia.com/v1/chat/completions"
    models:
      claude_3_5_sonnet:
        name: "claude-3-5-sonnet-20241022"
        max_tokens: 8192
        temperature: 0.1
```

### Configuração de Prompts

O arquivo `config/prompts.yaml` contém os prompts organizados por modelo. Normalmente não precisa ser alterado.

## Uso Básico

### Comando Padrão
```bash
# Usa modelos configurados em config.yaml
python main.py --fontes examples/fontes.txt
```

### Opções Disponíveis
```bash
python main.py --help
```

### Exemplos de Uso
```bash
# Análise com copybooks
python main.py --fontes examples/fontes.txt --books examples/BOOKS.txt

# Análise com HTML para PDF
python main.py --fontes examples/fontes.txt --pdf

# Análise completa
python main.py --fontes examples/fontes.txt --books examples/BOOKS.txt --output minha_analise --pdf
```

## Solução de Problemas

### Erro de Dependências
```bash
# Atualizar pip
pip install --upgrade pip

# Reinstalar dependências
pip install -r requirements.txt --force-reinstall
```

### Erro de Chave de API
```bash
# Verificar se a chave está configurada
echo $LUZIA_API_KEY

# Reconfigurar se necessário
export LUZIA_API_KEY="nova_chave"
```

### Erro de Arquivo Não Encontrado
```bash
# Verificar se o arquivo existe
ls -la examples/fontes.txt

# Usar caminho absoluto se necessário
python main.py --fontes /caminho/completo/para/fontes.txt
```

## Verificação da Instalação

### Teste Completo
```bash
# Teste com mock (não precisa de API)
python main.py --fontes examples/fontes.txt --models "mock_enhanced" --output teste_instalacao

# Verificar saída
ls -la teste_instalacao/
```

### Verificar Logs
```bash
# Logs são criados em logs/
ls -la logs/

# Ver último log
tail -f logs/cobol_ai_engine_*.log
```

## Configuração Avançada

### Múltiplos Modelos
Para usar múltiplos modelos por padrão, edite `config/config.yaml`:

```yaml
ai:
  default_models:
    - "claude_3_5_sonnet"
    - "luzia_standard"
    - "openai_gpt4"
```

### Configuração de Performance
```yaml
performance:
  timeout: 300
  memory:
    max_program_size: "5MB"
  processing:
    chunk_size: 4000
```

### Configuração de Logs
```yaml
logging:
  level: "INFO"
  file_rotation: true
  max_file_size: "10MB"
```

## Estrutura do Projeto

```
cobol_ai_engine_v2.0.0/
├── main.py                 # Script principal
├── config/                 # Configurações
│   ├── config.yaml        # Configuração principal
│   └── prompts.yaml       # Prompts por modelo
├── src/                   # Código fonte
├── examples/              # Arquivos de exemplo
├── docs/                  # Documentação
├── requirements.txt       # Dependências
├── README.md             # Guia principal
└── VERSION               # Versão atual
```

## Próximos Passos

1. **Configurar sua chave de API** (LuzIA recomendada)
2. **Testar com arquivos de exemplo**
3. **Configurar modelos padrão** em `config/config.yaml`
4. **Executar análise dos seus programas COBOL**
5. **Explorar relatórios gerados**

## Suporte

Para problemas de instalação:
1. Verifique os logs em `logs/`
2. Consulte a documentação em `docs/`
3. Teste com arquivos de exemplo
4. Verifique configuração em `config/`

---

**COBOL AI Engine v1.0.3 - Instalação Simples e Rápida**
