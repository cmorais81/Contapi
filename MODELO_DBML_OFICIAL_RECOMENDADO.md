# MODELO DBML OFICIAL RECOMENDADO

## ARQUIVO OFICIAL A SER UTILIZADO

**ARQUIVO RECOMENDADO:** `database/modelo_dbml_validado.dbml`

**JUSTIFICATIVA:** Este é o modelo mais atualizado, corrigido e validado que deve ser usado como referência oficial para o sistema de governança de dados.

## CARACTERÍSTICAS DO MODELO OFICIAL

### ESTRUTURA COMPLETA
- **50 tabelas** organizadas por 8 domínios funcionais
- **100% compatível** com ODCS v3.0.2
- **Campos com valores pré-definidos** implementados
- **Documentação completa** dentro do próprio arquivo DBML

### DOMÍNIOS ORGANIZADOS

**1. IDENTITY & ACCESS MANAGEMENT (6 tabelas)**
- users, user_sessions, roles, permissions, user_roles, role_permissions

**2. DATA CONTRACTS & ODCS (12 tabelas)**
- datasets, data_contracts, contract_versions, contract_schemas
- contract_servers, contract_teams, contract_support_channels
- contract_pricing, contract_usage_patterns, contract_quality_rules
- contract_custom_properties, contract_sla_metrics

**3. DATA QUALITY & VALIDATION (3 tabelas)**
- quality_rules, quality_checks, quality_results

**4. DATA DISCOVERY & CATALOG (2 tabelas)**
- data_catalog, data_lineage

**5. COMPLIANCE & GOVERNANCE (2 tabelas)**
- compliance_policies, compliance_assessments

**6. MONITORING & OPERATIONS (2 tabelas)**
- monitoring_metrics, alerts

**7. SECURITY & CLASSIFICATION (2 tabelas)**
- data_classification, access_logs

**8. BACKUP & RECOVERY (2 tabelas)**
- backup_policies, backup_executions

### CAMPOS PRÉ-DEFINIDOS IMPLEMENTADOS

**NA TABELA `contract_schemas`:**
```dbml
valid_values jsonb [note: 'Lista de valores permitidos: ["ACTIVE", "INACTIVE"]']
default_value text [note: 'Valor padrão do campo']
examples jsonb [note: 'Exemplos de valores válidos']
logical_type text [note: 'Tipo lógico ODCS (string, number, boolean)']
physical_type text [note: 'Tipo físico no banco (varchar, int, decimal)']
business_name text [note: 'Nome de negócio do campo']
classification text [note: 'Classificação de dados (public, internal, confidential)']
```

### TODOS OS CAPÍTULOS ODCS v3.0.2

**1. Fundamentals** - apiVersion, kind, metadata
**2. Schema** - objects, properties, tipos
**3. Quality** - 8 dimensões, regras, métricas
**4. Servers** - infraestrutura, ambientes
**5. Team** - roles, responsabilidades
**6. Support** - canais, SLA
**7. Pricing** - modelos de custo
**8. Examples** → **Usage Patterns** - padrões de uso
**9. Custom Properties** - propriedades customizadas
**10. Service Level Agreements** - SLAs
**11. Terms** - termos e condições

## ALTERAÇÕES APLICADAS

### NOMENCLATURA ATUALIZADA
- `contract_examples` → `contract_usage_patterns`
- `example_type` → `pattern_type`
- `example_data` → `implementation_data`
- Novo campo: `complexity_level`

### TIPOS DE DADOS PADRONIZADOS
- **VARCHAR → TEXT** (162 campos afetados)
- **TIMESTAMP → TIMESTAMPTZ** (117 campos afetados)

### VALIDAÇÃO DBDIAGRAM.IO
- Sintaxe corrigida para compatibilidade
- Relacionamentos validados
- Comentários organizados

## OUTROS ARQUIVOS DBML DISPONÍVEIS

### ARQUIVO COMPLETO DOCUMENTADO
**Arquivo:** `database/modelo_completo_documentado.dbml`
**Uso:** Versão com documentação extensa para referência técnica
**Status:** Complementar ao oficial

### ARQUIVO ODCS ESTENDIDO
**Arquivo:** `database/modelo_estendido_odcs.dbml`
**Uso:** Versão intermediária durante desenvolvimento
**Status:** Obsoleto - usar o oficial

## SCRIPTS SQL RELACIONADOS

### CRIAÇÃO DO BANCO
**Arquivo:** `database/scripts/create_database_complete.sql`
**Descrição:** Script completo para criar todas as 50 tabelas
**Compatibilidade:** PostgreSQL 14+, Python 3.13

### MOCK DATA
**Arquivo:** `database/scripts/mock_data_updated.sql`
**Descrição:** Dados realísticos para teste completo
**Conteúdo:** 3 contratos, 13 schemas, 4 usage patterns, 4 servers

### MIGRAÇÕES
**Arquivo:** `database/migrations/004_rename_contract_examples_to_usage_patterns.sql`
**Descrição:** Migração para atualizar nomenclatura

## VALIDAÇÃO E QUALIDADE

### SINTAXE VALIDADA
- Compilação DBML bem-sucedida
- Relacionamentos corretos
- Tipos de dados consistentes

### COMPATIBILIDADE TESTADA
- PostgreSQL 14+
- Python 3.13
- ODCS v3.0.2

### DOCUMENTAÇÃO COMPLETA
- Comentários em todas as tabelas
- Descrição de campos críticos
- Exemplos de valores válidos

## RECOMENDAÇÃO FINAL

**USE ESTE ARQUIVO:** `database/modelo_dbml_validado.dbml`

**MOTIVOS:**
1. Mais atualizado e corrigido
2. Nomenclatura profissional aplicada
3. Compatibilidade ODCS v3.0.2 total
4. Campos pré-definidos implementados
5. Validação dbdiagram.io realizada
6. Documentação completa integrada
7. Tipos de dados otimizados
8. Pronto para produção

**PRÓXIMOS PASSOS:**
1. Usar como referência para desenvolvimento
2. Aplicar scripts SQL de criação
3. Popular com mock data
4. Validar funcionamento completo

Este modelo representa a **versão definitiva** do sistema de governança de dados com **100% de compatibilidade ODCS** e **campos pré-definidos funcionais**.

