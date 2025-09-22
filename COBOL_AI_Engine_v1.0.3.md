# COBOL AI Engine v1.0.3

Sistema completo de análise de programas COBOL utilizando Inteligência Artificial. Oferece análise técnica profunda, documentação automática e suporte a múltiplos modelos de IA.

## Características Principais

**Análise Inteligente de COBOL**: Interpretação automática de programas COBOL com identificação de regras de negócio, estruturas de dados e fluxos lógicos.

**Múltiplos Provedores de IA**: Suporte nativo para LuzIA, OpenAI e outros provedores configuráveis.

**Documentação Automática**: Geração de relatórios técnicos completos em Markdown e HTML.

**Transparência Total**: Todos os prompts utilizados são salvos nos relatórios para auditoria completa.

**Configuração Flexível**: Sistema totalmente configurável via arquivos YAML.

**Geração HTML para PDF**: Conversão para PDF via navegador, sem dependências externas.

## Instalação Rápida

```bash
# Extrair o pacote
tar -xzf cobol_ai_engine_v1.0.3.tar.gz
cd cobol_ai_engine_v2.0.0/

# Instalar dependências
pip install -r requirements.txt

# Configurar chave da API (LuzIA)
export LUZIA_API_KEY="sua_chave_luzia_aqui"
```

## Uso Básico

### Análise Padrão
```bash
# Usa modelos configurados em config/config.yaml
python main.py --fontes examples/fontes.txt
```

### Análise com Copybooks
```bash
python main.py --fontes examples/fontes.txt --books examples/BOOKS.txt
```

### Análise com HTML para PDF
```bash
python main.py --fontes examples/fontes.txt --pdf
```

### Análise Completa
```bash
python main.py --fontes examples/fontes.txt --books examples/BOOKS.txt --output minha_analise --pdf
```

## Configuração

### Arquivo Principal: config/config.yaml

```yaml
# Modelos padrão a serem utilizados
ai:
  default_models:
    - "claude_3_5_sonnet"
    - "luzia_standard"

# Configuração do provedor LuzIA
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

### Variáveis de Ambiente

```bash
# LuzIA (principal)
export LUZIA_API_KEY="sua_chave_luzia"

# OpenAI (opcional)
export OPENAI_API_KEY="sua_chave_openai"
```

## Estrutura de Saída

### Modelo Único
```
output/
├── PROGRAMA1.md          # Relatório markdown
├── PROGRAMA1.html        # Relatório HTML (se --pdf)
├── PROGRAMA2.md
├── PROGRAMA2.html
└── index.html           # Índice navegável
```

### Múltiplos Modelos
```
output/
├── model_claude_3_5_sonnet/
│   ├── PROGRAMA1.md
│   ├── PROGRAMA1.html
│   └── index.html
├── model_luzia_standard/
│   ├── PROGRAMA1.md
│   ├── PROGRAMA1.html
│   └── index.html
└── relatorio_comparativo_modelos.md
```

## Conversão para PDF

### Processo Simples
1. Execute com `--pdf` para gerar arquivos HTML
2. Abra qualquer arquivo `.html` no navegador
3. Pressione `Ctrl+P` (Windows/Linux) ou `Cmd+P` (Mac)
4. Selecione "Salvar como PDF"
5. Configure margens como "Mínimas"
6. Clique em "Salvar"

### Vantagens
- Sem dependências externas
- Funciona em qualquer navegador
- Formatação profissional garantida
- Controle total sobre qualidade

## Parâmetros de Linha de Comando

```
python main.py [opções]

Opções Obrigatórias:
  --fontes ARQUIVO         Arquivo de fontes COBOL (ex: fontes.txt)

Opções:
  --books ARQUIVO          Arquivo de copybooks (opcional)
  --output DIRETORIO       Diretório de saída (padrão: output)
  --config ARQUIVO         Arquivo de configuração (padrão: config/config.yaml)
  --models MODELOS         Sobrescrever modelos da configuração
  --pdf                    Gerar HTML para conversão PDF
  --log NIVEL              Nível de log (DEBUG, INFO, WARNING, ERROR)
```

## Modelos Suportados

### LuzIA (Recomendado)
- **claude_3_5_sonnet**: Análises técnicas profundas (200K tokens)
- **luzia_standard**: Análises balanceadas (32K tokens)

### OpenAI
- **openai_gpt4**: Análises alternativas (128K tokens)

### Mock (Desenvolvimento)
- **mock_enhanced**: Testes e desenvolvimento

## Exemplos Práticos

### Desenvolvimento
```bash
# Teste rápido com mock
python main.py --fontes meus_fontes.txt --models "mock_enhanced"
```

### Produção
```bash
# Análise completa configurada
python main.py --fontes fontes_producao.txt --books books_producao.txt --pdf
```

### Análise Comparativa
```bash
# Múltiplos modelos (sobrescreve configuração)
python main.py --fontes fontes.txt --models '["claude_3_5_sonnet","luzia_standard"]'
```

## Relatórios Gerados

### Conteúdo dos Relatórios
- **Resumo Executivo**: Visão geral do programa
- **Análise Técnica**: Estrutura e arquitetura
- **Regras de Negócio**: Lógica empresarial identificada
- **Estruturas de Dados**: Layouts e formatos
- **Interfaces**: Dependências e integrações
- **Recomendações**: Sugestões de melhoria
- **Transparência**: Prompts utilizados na análise

### Relatório Comparativo (Multi-Modelo)
- Estatísticas por modelo
- Análise comparativa por programa
- Consensos e divergências
- Recomendações de uso

## Solução de Problemas

### Erro de Autenticação
```bash
# Verificar chave
echo $LUZIA_API_KEY

# Reconfigurar
export LUZIA_API_KEY="nova_chave"
```

### Modelo Não Encontrado
```bash
# Verificar configuração
grep -A 5 "default_models" config/config.yaml

# Testar com mock
python main.py --fontes examples/fontes.txt --models "mock_enhanced"
```

### Arquivo Não Encontrado
```bash
# Verificar arquivo
ls -la examples/fontes.txt

# Usar caminho absoluto
python main.py --fontes /caminho/completo/fontes.txt
```

## Logs e Monitoramento

### Localização
```
logs/cobol_ai_engine_YYYYMMDD_HHMMSS.log
```

### Níveis Disponíveis
- **DEBUG**: Máximo detalhe
- **INFO**: Informações gerais (padrão)
- **WARNING**: Apenas avisos
- **ERROR**: Apenas erros

### Monitoramento em Tempo Real
```bash
tail -f logs/cobol_ai_engine_*.log
```

## Compatibilidade

### Requisitos
- **Python**: 3.11 ou superior
- **Sistemas**: Windows, Linux, macOS
- **Memória**: Mínimo 512MB RAM
- **Navegador**: Qualquer navegador moderno (para PDF)

### Dependências
- pyyaml >= 6.0
- requests >= 2.31.0
- python-dateutil >= 2.8.2

## Arquivos de Configuração

### config/config.yaml
Configuração principal do sistema incluindo provedores, modelos e parâmetros.

### config/prompts.yaml
Prompts organizados por modelo e tipo de análise.

### examples/
Arquivos de exemplo para teste e demonstração.

## Performance

### Métricas Típicas
- **Tempo por programa**: 0.5-2.0 segundos
- **Tokens por análise**: 2.000-8.000 tokens
- **Taxa de sucesso**: 99%+
- **Uso de memória**: Menos de 100MB

### Otimização
- Use modelos apropriados para cada cenário
- Configure timeouts adequados
- Monitore uso de tokens

## Segurança

### Boas Práticas
- Use variáveis de ambiente para credenciais
- Não armazene chaves em arquivos
- Valide entrada de dados
- Monitore logs regularmente

### Validação
- Verificação de encoding UTF-8
- Sanitização de conteúdo
- Validação de tamanho de arquivo
- Verificação SSL habilitada

## Documentação Adicional

- **INSTALACAO.md**: Guia de instalação detalhado
- **GUIA_REFERENCIA_RAPIDA.md**: Referência rápida
- **CHANGELOG.md**: Histórico de versões
- **docs/**: Documentação técnica adicional

## Suporte

Para problemas técnicos, consulte:
1. Logs do sistema em `logs/`
2. Documentação em `docs/`
3. Exemplos em `examples/`
4. Arquivo de configuração `config/config.yaml`

## Licença

Este software é fornecido "como está", sem garantias de qualquer tipo. Use por sua própria conta e risco.

---

**COBOL AI Engine v1.0.3 - Análise inteligente de programas COBOL**  
**Compatibilidade**: Python 3.11+ | **Última atualização**: 21 de Setembro de 2025
