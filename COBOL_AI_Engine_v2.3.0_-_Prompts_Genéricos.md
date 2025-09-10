# COBOL AI Engine v2.3.0 - Prompts Genéricos

## ARQUIVO DE PROMPTS COMPLETAMENTE GENÉRICO

### ✅ PROBLEMA RESOLVIDO

Você estava certo! O arquivo anterior tinha referências específicas ao BACEN e programas LH. Agora criamos um arquivo **completamente genérico** que funciona com **qualquer tipo de programa COBOL**.

### 📁 ARQUIVO CRIADO

**`config/prompts_generic.yaml`** - Configuração genérica completa

### 🎯 CARACTERÍSTICAS GENÉRICAS

#### **1. PERGUNTAS UNIVERSAIS**
```yaml
analysis_questions:
  functional:
    question: "O que este programa faz funcionalmente?"
    priority: 1
    required: true
    
  technical:
    question: "Qual é a estrutura técnica e componentes principais?"
    priority: 2
    required: true
    
  business_rules:
    question: "Quais regras de negócio estão implementadas?"
    priority: 3
    required: true
```

#### **2. CONTEXTOS POR PADRÃO DE NOME**
```yaml
contextual_prompts:
  # Programas de processamento de dados
  data_processing:
    pattern: "^[A-Z]{2,4}[0-9]{4}$"
    context: "programa de processamento de dados corporativo"
    
  # Programas de relatórios
  report_programs:
    pattern: ".*REL.*|.*RPT.*|.*REP.*"
    context: "programa gerador de relatórios"
    
  # Programas batch
  batch_programs:
    pattern: ".*BATCH.*|.*BTH.*|.*JOB.*"
    context: "programa de processamento batch"
    
  # Padrão genérico para qualquer programa
  default:
    context: "programa COBOL corporativo"
    additional_questions:
      - "Qual é o propósito principal?"
      - "Como se integra ao sistema?"
      - "Que dados processa?"
```

#### **3. SEM REFERÊNCIAS ESPECÍFICAS**
- ❌ **Removido**: Referências ao BACEN
- ❌ **Removido**: Referências a programas LH específicos
- ❌ **Removido**: Contexto bancário específico
- ✅ **Adicionado**: Contextos genéricos por tipo
- ✅ **Adicionado**: Perguntas universais
- ✅ **Adicionado**: Padrões de detecção automática

### 🔧 TIPOS DE PROGRAMA SUPORTADOS

#### **Detecção Automática por Padrão**
1. **Processamento de Dados**: `^[A-Z]{2,4}[0-9]{4}$`
2. **Relatórios**: `.*REL.*|.*RPT.*|.*REP.*`
3. **Batch**: `.*BATCH.*|.*BTH.*|.*JOB.*`
4. **Online/Transacional**: `.*ONL.*|.*TXN.*|.*SCR.*`
5. **Interface**: `.*INT.*|.*IFC.*|.*API.*`
6. **Utilitários**: `.*UTL.*|.*UTIL.*|.*TOOL.*`
7. **Padrão Genérico**: Qualquer outro programa

#### **Perguntas Específicas por Tipo**
```yaml
# Exemplo para programas de relatório
report_programs:
  additional_questions:
    - "Que informações são apresentadas no relatório?"
    - "Qual é a periodicidade de execução?"
    - "Quem são os usuários finais do relatório?"
```

### 📊 FUNCIONALIDADES AVANÇADAS

#### **1. Detecção Automática**
```yaml
advanced:
  auto_detection:
    enabled: true
    use_filename_patterns: true
    use_code_analysis: true
    fallback_to_generic: true
```

#### **2. Adaptação Dinâmica**
```yaml
dynamic_adaptation:
  enabled: true
  adjust_based_on_size: true
  adjust_based_on_complexity: true
  adjust_based_on_context: true
```

#### **3. Controle de Qualidade**
```yaml
quality_control:
  min_response_length: 200
  require_functional_answer: true
  validate_technical_content: true
  check_business_relevance: true
```

### 🎯 COMO USAR

#### **1. Usar Configuração Genérica**
```bash
# Sistema usa automaticamente prompts genéricos
python main.py --fontes qualquer_programa.txt
```

#### **2. Customizar Pergunta Funcional**
```bash
# Personalizar para seu contexto
python main.py --update-question "Qual é a função deste programa no meu sistema?"
```

#### **3. Ver Perguntas Disponíveis**
```bash
python main.py --list-questions
```

### 📋 EXEMPLO DE SAÍDA

#### **Para Qualquer Programa COBOL**
```
=== PERGUNTAS CONFIGURADAS ===
1. O que este programa faz funcionalmente? (Obrigatória)
2. Qual é a estrutura técnica e componentes principais? (Obrigatória)
3. Quais regras de negócio estão implementadas? (Obrigatória)
4. Quais são os trechos de código mais relevantes? (Opcional)
5. Como este programa se relaciona com outros sistemas? (Opcional)
6. Quais são as considerações de performance e otimização? (Opcional)
7. Quais aspectos são importantes para manutenção? (Opcional)
```

### ✅ BENEFÍCIOS

#### **1. UNIVERSALIDADE**
- Funciona com qualquer programa COBOL
- Não depende de contexto específico
- Adaptável a qualquer domínio

#### **2. FLEXIBILIDADE**
- Detecção automática de tipo
- Perguntas específicas por padrão
- Customização total via YAML

#### **3. TRANSPARÊNCIA**
- Todos os prompts documentados
- Contexto aplicado visível
- Rastreabilidade completa

### 🎯 RESULTADO FINAL

**COBOL AI Engine v2.3.0 com Prompts Completamente Genéricos**

- ✅ **Sem referências específicas**: BACEN, LH, bancário removidos
- ✅ **Contextos universais**: Aplicável a qualquer domínio
- ✅ **Detecção automática**: Por padrão de nome do programa
- ✅ **Perguntas genéricas**: Funcionais para qualquer sistema
- ✅ **Customização total**: Via YAML e linha de comando
- ✅ **Transparência completa**: Prompts documentados

**AGORA FUNCIONA COM QUALQUER TIPO DE PROGRAMA COBOL!**

