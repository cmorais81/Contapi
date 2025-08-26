"""
Guia de Uso em Produção - Sincronização Delta Lake para PostgreSQL
Solução otimizada para volumes de 150GB+ com checkpoint/resume
"""

import logging
from pyspark.sql import SparkSession
from compare_data_production_optimized import CompareDataProductionOptimized


def exemplo_uso_basico():
    """Exemplo básico de uso da solução otimizada"""
    
    # Configurar logging
    logging.basicConfig(
        level=logging.INFO,
        format='%(asctime)s - %(levelname)s - %(message)s'
    )
    logger = logging.getLogger(__name__)
    
    # Obter sessão Spark ativa
    spark = SparkSession.getActiveSession()
    
    # Inicializar classe otimizada
    compare_data = CompareDataProductionOptimized(
        spark=spark,
        logger=logger,
        checkpoint_dir="/dbfs/tmp/sync_checkpoints"  # Usar DBFS para persistência
    )
    
    # Configurar conexão PostgreSQL
    compare_data.configure_postgres_connection(
        host="seu-host-postgres.com",
        port=5432,
        database="sua_database",
        user="seu_usuario",
        password="sua_senha"
    )
    
    # Executar sincronização com checkpoint
    result = compare_data.sync_with_checkpoint(
        delta_table_name="seu_schema.dados_cadastrais",
        postgres_table_name="dados_cadastrais_postgres",
        key_columns=["penumper"],
        compare_columns=None,  # None = todas as colunas
        chunk_size=1000000,    # 1M registros por chunk
        mark_for_deletion=True,
        job_id="sync_dados_cadastrais_prod",
        auto_resume=True
    )
    
    # Exibir resultados
    logger.info(f"Sincronização concluída:")
    logger.info(f"- Registros processados: {result['total_records_processed']:,}")
    logger.info(f"- Tempo de execução: {result['execution_time_minutes']:.1f} minutos")
    logger.info(f"- Throughput: {result['throughput_per_second']:,.0f} registros/segundo")
    
    return result


def exemplo_uso_notebook_databricks():
    """Código otimizado para uso em notebook Databricks"""
    
    codigo_notebook = '''
# Importar bibliotecas
import logging
from compare_data_production_optimized import CompareDataProductionOptimized

# Configurar logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

# Inicializar classe com checkpoint
compare_data = CompareDataProductionOptimized(
    spark=spark,
    logger=logger,
    checkpoint_dir="/dbfs/tmp/sync_checkpoints"
)

# Configurar PostgreSQL (substituir pelos seus dados)
compare_data.configure_postgres_connection(
    host="seu-host-postgres.com",
    port=5432,
    database="sua_database",
    user="seu_usuario",
    password="sua_senha"
)

# Executar sincronização (resistente a falhas)
try:
    result = compare_data.sync_with_checkpoint(
        delta_table_name="seu_schema.dados_cadastrais",
        postgres_table_name="dados_cadastrais_postgres",
        key_columns=["penumper"],
        chunk_size=1000000,
        mark_for_deletion=True,
        job_id="sync_dados_cadastrais_20241226",
        auto_resume=True
    )
    
    print(f"SUCESSO: {result['total_records_processed']:,} registros processados")
    print(f"Tempo: {result['execution_time_minutes']:.1f} minutos")
    print(f"Throughput: {result['throughput_per_second']:,.0f} rec/s")
    
except Exception as e:
    print(f"ERRO: {e}")
    print("Checkpoint salvo - execute novamente para retomar")

# Para monitorar progresso, verificar arquivos em /dbfs/tmp/sync_checkpoints/
'''
    
    return codigo_notebook


def exemplo_configuracoes_avancadas():
    """Exemplo com configurações avançadas para diferentes cenários"""
    
    # Configurações para diferentes volumes de dados
    configuracoes = {
        'pequeno_volume': {
            'chunk_size': 500000,      # 500K registros
            'descricao': 'Para tabelas < 10M registros'
        },
        'medio_volume': {
            'chunk_size': 1000000,     # 1M registros
            'descricao': 'Para tabelas 10M-50M registros'
        },
        'grande_volume': {
            'chunk_size': 2000000,     # 2M registros
            'descricao': 'Para tabelas > 50M registros (150GB+)'
        }
    }
    
    return configuracoes


def exemplo_monitoramento_progresso():
    """Exemplo de como monitorar progresso da sincronização"""
    
    codigo_monitoramento = '''
import json
import time
from datetime import datetime

def monitorar_sincronizacao(checkpoint_dir, job_id):
    """Monitorar progresso da sincronização em tempo real"""
    
    checkpoint_file = f"{checkpoint_dir}/{job_id}.json"
    
    while True:
        try:
            with open(checkpoint_file, 'r') as f:
                checkpoint = json.load(f)
            
            completed = len(checkpoint.get('completed_chunks', []))
            total = checkpoint.get('total_chunks', 0)
            status = checkpoint.get('status', 'UNKNOWN')
            
            if total > 0:
                progress_pct = (completed / total) * 100
                
                print(f"[{datetime.now().strftime('%H:%M:%S')}] "
                      f"Progresso: {completed}/{total} chunks ({progress_pct:.1f}%) - "
                      f"Status: {status}")
                
                # Verificar se concluído
                if status in ['COMPLETED', 'FAILED']:
                    print(f"Sincronização finalizada com status: {status}")
                    break
            
            time.sleep(30)  # Verificar a cada 30 segundos
            
        except FileNotFoundError:
            print("Aguardando início da sincronização...")
            time.sleep(10)
        except Exception as e:
            print(f"Erro no monitoramento: {e}")
            time.sleep(10)

# Usar assim:
# monitorar_sincronizacao("/dbfs/tmp/sync_checkpoints", "sync_dados_cadastrais_20241226")
'''
    
    return codigo_monitoramento


def exemplo_tratamento_erros():
    """Exemplo de tratamento robusto de erros"""
    
    codigo_tratamento = '''
def executar_sincronizacao_robusta():
    """Executar sincronização com tratamento robusto de erros"""
    
    max_tentativas = 3
    tentativa = 0
    
    while tentativa < max_tentativas:
        try:
            tentativa += 1
            print(f"Tentativa {tentativa}/{max_tentativas}")
            
            # Executar sincronização
            result = compare_data.sync_with_checkpoint(
                delta_table_name="seu_schema.dados_cadastrais",
                postgres_table_name="dados_cadastrais_postgres",
                key_columns=["penumper"],
                chunk_size=1000000,
                mark_for_deletion=True,
                job_id="sync_dados_cadastrais_prod",
                auto_resume=True
            )
            
            print("Sincronização concluída com sucesso!")
            return result
            
        except Exception as e:
            print(f"Erro na tentativa {tentativa}: {e}")
            
            if tentativa < max_tentativas:
                print(f"Aguardando 60 segundos antes da próxima tentativa...")
                time.sleep(60)
            else:
                print("Todas as tentativas falharam")
                raise
    
    return None

# Executar
resultado = executar_sincronizacao_robusta()
'''
    
    return codigo_tratamento


def exemplo_validacao_resultados():
    """Exemplo de validação dos resultados da sincronização"""
    
    codigo_validacao = '''
def validar_sincronizacao(compare_data, delta_table, postgres_table):
    """Validar resultados da sincronização"""
    
    print("Validando resultados da sincronização...")
    
    # Contar registros no Delta Lake
    df_delta = spark.table(delta_table)
    count_delta = df_delta.count()
    
    # Obter estatísticas do PostgreSQL
    stats_postgres = compare_data.get_sync_statistics(postgres_table)
    count_postgres_ativo = stats_postgres.get('active_records', 0)
    count_postgres_total = stats_postgres.get('total_records', 0)
    
    # Validações
    validacoes = {
        'contagem_coincide': count_delta == count_postgres_ativo,
        'sem_registros_perdidos': count_postgres_total >= count_delta,
        'dados_recentes': stats_postgres.get('last_update') is not None
    }
    
    # Exibir resultados
    print(f"Registros Delta Lake: {count_delta:,}")
    print(f"Registros PostgreSQL (ativos): {count_postgres_ativo:,}")
    print(f"Registros PostgreSQL (total): {count_postgres_total:,}")
    print(f"Última atualização: {stats_postgres.get('last_update')}")
    
    # Verificar validações
    todas_validacoes_ok = all(validacoes.values())
    
    if todas_validacoes_ok:
        print("VALIDAÇÃO PASSOU: Sincronização bem-sucedida")
    else:
        print("VALIDAÇÃO FALHOU:")
        for validacao, resultado in validacoes.items():
            if not resultado:
                print(f"- {validacao}: FALHOU")
    
    return validacoes

# Executar validação
validacao = validar_sincronizacao(
    compare_data, 
    "seu_schema.dados_cadastrais", 
    "dados_cadastrais_postgres"
)
'''
    
    return codigo_validacao


def exemplo_configuracao_cluster():
    """Configurações recomendadas de cluster para diferentes volumes"""
    
    configuracoes_cluster = {
        'desenvolvimento': {
            'driver': 'Standard_D8s_v3 (8 cores, 32GB)',
            'workers': '4x Standard_D8s_v3',
            'volume_max': '10M registros',
            'tempo_estimado': '15-30 minutos'
        },
        'homologacao': {
            'driver': 'Standard_D16s_v3 (16 cores, 64GB)',
            'workers': '8x Standard_D16s_v3',
            'volume_max': '50M registros',
            'tempo_estimado': '30-60 minutos'
        },
        'producao_150gb': {
            'driver': 'Standard_D32s_v3 (32 cores, 128GB)',
            'workers': '25-30x Standard_D16s_v3',
            'volume_max': '100M+ registros (150GB)',
            'tempo_estimado': '45-75 minutos'
        }
    }
    
    return configuracoes_cluster


def exemplo_otimizacoes_postgresql():
    """Configurações PostgreSQL recomendadas para ETL"""
    
    configuracoes_postgresql = '''
-- Configurações PostgreSQL para otimizar ETL de grandes volumes

-- Configurações de memória
SET work_mem = '256MB';
SET maintenance_work_mem = '1GB';
SET shared_buffers = '25% da RAM';

-- Configurações de checkpoint
SET checkpoint_completion_target = 0.9;
SET wal_buffers = '16MB';
SET checkpoint_timeout = '15min';

-- Configurações para ETL (temporárias)
SET synchronous_commit = off;
SET fsync = off;  -- CUIDADO: usar apenas durante ETL
SET full_page_writes = off;  -- CUIDADO: usar apenas durante ETL

-- Configurações de autovacuum (ajustar durante ETL)
SET autovacuum = off;  -- Desabilitar durante ETL massivo

-- Após ETL, restaurar configurações de segurança:
-- SET synchronous_commit = on;
-- SET fsync = on;
-- SET full_page_writes = on;
-- SET autovacuum = on;
-- VACUUM ANALYZE tabela_principal;
'''
    
    return configuracoes_postgresql


def main():
    """Função principal com exemplos de uso"""
    
    print("Guia de Uso em Produção - Sincronização Delta Lake para PostgreSQL")
    print("="*80)
    
    exemplos = {
        'Uso Básico': exemplo_uso_basico,
        'Notebook Databricks': exemplo_uso_notebook_databricks,
        'Configurações Avançadas': exemplo_configuracoes_avancadas,
        'Monitoramento': exemplo_monitoramento_progresso,
        'Tratamento de Erros': exemplo_tratamento_erros,
        'Validação': exemplo_validacao_resultados,
        'Configuração Cluster': exemplo_configuracao_cluster,
        'Otimizações PostgreSQL': exemplo_otimizacoes_postgresql
    }
    
    for nome, exemplo_func in exemplos.items():
        print(f"\n{nome}:")
        print("-" * 40)
        
        try:
            resultado = exemplo_func()
            if isinstance(resultado, str):
                print(resultado)
            elif isinstance(resultado, dict):
                for key, value in resultado.items():
                    print(f"{key}: {value}")
        except Exception as e:
            print(f"Erro ao executar exemplo: {e}")
    
    print("\n" + "="*80)
    print("Resumo das Principais Características:")
    print("- Checkpoint automático a cada chunk processado")
    print("- Resume automático em caso de falha")
    print("- Estratégia COPY + MERGE otimizada para PostgreSQL")
    print("- Configurações Spark otimizadas para Runtime 13/14")
    print("- Suporte a volumes de 150GB+ com performance garantida")
    print("- Monitoramento de progresso em tempo real")
    print("- Validação automática de resultados")


if __name__ == "__main__":
    main()

