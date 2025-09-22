# Guia de Uso - COBOL AI Engine v2.0.0

## Configuração Inicial

O COBOL AI Engine v2.0.0 oferece duas interfaces: linha de comando (main.py) e interface interativa (cli_interactive.py). A configuração requer apenas duas variáveis de ambiente para integração com a API LuzIA.

### Variáveis de Ambiente

Configure as credenciais da API LuzIA em seu ambiente:

```bash
export LUZIA_CLIENT_ID="seu_client_id_aqui"
export LUZIA_CLIENT_SECRET="seu_client_secret_aqui"
```

### Estrutura de Arquivos

Prepare seus arquivos de entrada no formato esperado:

**Arquivo de fontes** (`fontes.txt`): Lista os programas COBOL a serem analisados, um por linha, no formato `NOME_PROGRAMA:caminho/para/arquivo.cbl`

**Arquivo de books** (`books.txt`): Lista os copybooks disponíveis, um por linha, no mesmo formato

## Interface de Linha de Comando (main.py)

### Comando Principal

Execute a análise usando o comando unificado:

```bash
python main.py --fontes examples/fontes.txt --books examples/BOOKS.txt --output minha_analise
```

### Parâmetros Disponíveis

O sistema aceita os seguintes parâmetros:

- `--fontes`: Arquivo contendo lista de programas COBOL para análise (obrigatório)
- `--books`: Arquivo contendo lista de copybooks (opcional)
- `--output`: Diretório de saída para os relatórios (padrão: "output")
- `--models`: Modelo específico a usar (opcional, usa configuração padrão se não especificado)
- `--pdf`: Gera relatórios HTML otimizados para conversão PDF
- `--status`: Verifica status e conectividade dos provedores

### Exemplo Completo

```bash
# Configurar ambiente
export LUZIA_CLIENT_ID="abc123"
export LUZIA_CLIENT_SECRET="xyz789"

# Executar análise
python main.py \
  --fontes /caminho/para/fontes.txt \
  --books /caminho/para/books.txt \
  --output /caminho/para/saida \
  --pdf
```

## Interface Interativa (cli_interactive.py)

### Iniciando o CLI

Execute o CLI interativo:

```bash
python cli_interactive.py
```

### Menu Principal

O CLI oferece as seguintes opções:

1. **Analisar código COBOL (digitar/colar)** - Para testes rápidos com código pequeno
2. **Analisar arquivo COBOL** - Para análise de arquivo individual
3. **Analisar múltiplos arquivos** - Para processar vários arquivos em lote
4. **Ver status dos provedores** - Verificar conectividade dos provedores de IA
5. **Configurar provedor de IA** - Alterar provedor ativo
6. **Ajuda e exemplos** - Documentação e exemplos de uso

### Funcionalidades do CLI

#### Análise de Código Digitado
- Digite ou cole código COBOL diretamente
- Finalize com "END" em uma linha separada
- Ideal para testes rápidos e prototipagem

#### Análise de Arquivo Individual
- Forneça o caminho completo do arquivo
- Processamento automático com geração de relatório
- Feedback em tempo real do progresso

#### Análise em Lote
- Liste múltiplos arquivos para processamento
- Relatório de progresso para cada arquivo
- Resumo final com estatísticas de sucesso/falha

#### Configuração de Provedor
- Visualize provedores disponíveis
- Altere o provedor ativo dinamicamente
- Verificação de status em tempo real

## Saídas Geradas

### Relatórios Funcionais

Para cada programa analisado, o sistema gera um relatório em Markdown com o nome `PROGRAMA_analise_funcional.md`. Este relatório contém:

**Análise Detalhada**: Resposta estruturada da IA cobrindo contexto, regras de negócio, arquitetura técnica e recomendações

**Seção de Transparência**: Informações sobre prompts utilizados, metodologia aplicada e limitações da análise

### Estrutura de Saída

#### Interface de Linha de Comando
```
output/
├── PROGRAMA1_analise_funcional.md
├── PROGRAMA2_analise_funcional.md
├── ai_responses/
│   ├── PROGRAMA1_ai_response.json
│   └── PROGRAMA2_ai_response.json
├── ai_requests/
│   ├── PROGRAMA1_ai_request.json
│   └── PROGRAMA2_ai_request.json
└── logs/
    └── cobol_ai_engine_YYYYMMDD_HHMMSS.log
```

#### Interface Interativa
```
output_cli/
├── PROGRAMA_CLI_analise_funcional.md
├── ARQUIVO_analise_funcional.md
├── ai_responses/
└── ai_requests/
```

## Qualidade das Análises

### Metodologia em Duas Etapas

O sistema v2.0.0 utiliza uma abordagem aprimorada onde a IA primeiro realiza uma análise geral como especialista em COBOL, depois responde questões específicas estruturadas. Esta metodologia garante maior profundidade e precisão nas análises.

### Questões Estruturadas

Cada análise cobre sistematicamente nove áreas principais: contexto e objetivo, visão de alto nível, regras de negócio com rastreabilidade, casos de uso, exceções, estruturas de dados, integrações, métricas sugeridas e pontos para validação com área de negócio.

### Rastreabilidade

As análises incluem referências específicas a linhas de código sempre que possível, facilitando a validação e manutenção posterior dos programas.

## Resolução de Problemas

### Token Expirado

O sistema v2.0.0 inclui renovação automática de tokens. Se você ver mensagens sobre token expirado nos logs, isso é normal - o sistema automaticamente renova e continua a execução.

### Erro de Configuração

Verifique se as variáveis de ambiente estão configuradas corretamente:

```bash
echo $LUZIA_CLIENT_ID
echo $LUZIA_CLIENT_SECRET
```

### Verificar Status dos Provedores

#### Via Linha de Comando
```bash
python main.py --status
```

#### Via CLI Interativo
Execute `python cli_interactive.py` e escolha a opção 4.

### Logs Detalhados

Consulte os arquivos de log na pasta `logs/` para informações detalhadas sobre a execução e possíveis problemas.

## Geração de PDF

### Via Linha de Comando
```bash
python main.py --fontes fontes.txt --books books.txt --output saida --pdf
```

### Via CLI Interativo
Os relatórios gerados pelo CLI podem ser convertidos manualmente:
1. Abra o arquivo .md no navegador (ou use um visualizador Markdown)
2. Use Ctrl+P → "Salvar como PDF"

### Conversão Automática
Para conversão automática via linha de comando, use o parâmetro `--pdf` que gera arquivos HTML otimizados.

## Migração da Versão Anterior

Se você estava usando scripts como `main_detailed.py` ou `main_demo.py`, simplesmente substitua por:

- **Linha de comando**: `main.py` com os mesmos parâmetros
- **Interativo**: `cli_interactive.py` para interface amigável

A funcionalidade foi consolidada e melhorada nos scripts principais.

## Escolhendo a Interface

### Use main.py quando:
- Processar múltiplos programas em lote
- Integrar com scripts automatizados
- Gerar relatórios para produção
- Precisar de saída em PDF

### Use cli_interactive.py quando:
- Testar código COBOL rapidamente
- Analisar arquivos individuais
- Explorar funcionalidades do sistema
- Configurar provedores interativamente
- Aprender a usar o sistema

---

Para suporte adicional, consulte os logs de execução ou entre em contato com a equipe de desenvolvimento.
