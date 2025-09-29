# CHANGELOG - COBOL to Docs v1.1

## Versão 1.1.0 - 29/09/2025

### Principais Melhorias

#### Algoritmo de Custo Aprimorado
- Implementado cálculo de custo baseado em tokens de entrada + saída
- Fórmula: custo = (tokens_entrada * preco_entrada) + (tokens_saida * preco_saida)
- Suporte a diferentes modelos de precificação por provider
- Relatórios de custo detalhados por modelo e requisição

#### Base de Conhecimento RAG Expandida
- Expandida de 15 para 77 itens especializados em sistemas CADOC
- 25 novos domínios bancários incluídos
- Conhecimento específico de processamento documental
- Padrões de sistemas core banking integrados

#### Seleção Inteligente de Modelos
- Análise automática de complexidade do código COBOL
- Recomendação do modelo LLM mais adequado
- Sistema de fallback inteligente
- Suporte a 14 modelos diferentes via LuzIA

#### Sistema de Prompts Adaptativos
- Templates especializados por domínio CADOC
- Prompts adaptativos baseados na complexidade
- Otimização específica por modelo LLM
- Estrutura de saída padronizada

#### Melhorias de Interface
- Remoção completa de ícones e emojis
- Interface profissional e limpa
- Documentação técnica aprimorada
- Logs estruturados e informativos

### Funcionalidades Técnicas

#### Integração LuzIA Aprimorada
- URLs corrigidas para ambiente Santander
- Autenticação OAuth2 corporativa
- Payload otimizado para melhor performance
- Sistema de retry e fallback robusto

#### Sistema RAG Inteligente
- Auto-learning com base nas análises realizadas
- Contexto especializado injetado automaticamente
- Rastreabilidade completa das operações
- Relatórios detalhados de uso

#### Análise de Qualidade Superior
- Extração profunda de regras de negócio
- Identificação de riscos técnicos
- Recomendações estratégicas específicas
- Mapeamento completo de integrações

### Compatibilidade e Instalação

#### Instalação Simplificada
- Script de instalação automatizada
- Suporte a pip install
- Dependências otimizadas
- Compatibilidade multiplataforma

#### Formas de Uso
- Linha de comando com argumentos flexíveis
- Análise de arquivos únicos ou lotes
- Múltiplos formatos de saída
- Integração com pipelines CI/CD

### Correções e Otimizações

#### Performance
- Tempo de resposta otimizado
- Uso eficiente de memória
- Cache inteligente de resultados
- Processamento paralelo quando possível

#### Estabilidade
- Tratamento robusto de erros
- Logs detalhados para debugging
- Fallbacks automáticos
- Validação de entrada aprimorada

### Arquivos Principais Modificados

- `src/utils/cost_calculator.py` - Algoritmo de custo aprimorado
- `src/core/intelligent_model_selector.py` - Seleção inteligente de modelos
- `src/core/adaptive_prompt_manager.py` - Sistema de prompts adaptativos
- `data/cobol_knowledge_base_cadoc_expanded.json` - Base expandida
- `config/prompts_cadoc_deep_analysis.yaml` - Prompts especializados

### Compatibilidade

- Python 3.8+
- Sistemas Unix/Linux/Windows
- Integração com LuzIA (Santander)
- Fallback para providers alternativos

### Próximas Versões

- Integração com mais providers LLM
- Interface web opcional
- API REST para integração
- Análise de performance avançada
