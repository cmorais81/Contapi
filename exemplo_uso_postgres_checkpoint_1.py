"""
Exemplo de Uso - Sincronização com Checkpoint em Tabela PostgreSQL
Solução otimizada para primeira execução com grandes volumes (150GB+)
"""

import logging
from pyspark.sql import SparkSession
from compare_data_postgres_checkpoint import CompareDataPostgresCheckpoint


def exemplo_primeira_execucao_150gb():
    """Exemplo para primeira execução com 150GB de dados"""
    
    # Configurar logging detalhado
    logging.basicConfig(
        level=logging.INFO,
        format='%(asctime)s - %(levelname)s - %(message)s'
    )
    logger = logging.getLogger(__name__)
    
    # Obter sessão Spark ativa
    spark = SparkSession.getActiveSession()
    
    # Inicializar classe com checkpoint PostgreSQL
    compare_data = CompareDataPostgresCheckpoint(
        spark=spark,
        logger=logger,
        control_schema="public"  # Schema para tabelas de controle
    )
    
    # Configurar conexão PostgreSQL
    compare_data.configure_postgres_connection(
        host="seu-host-postgres.com",
        port=5432,
        database="sua_database",
        user="seu_usuario",
        password="sua_senha"
    )
    
    # Executar sincronização com checkpoint PostgreSQL
    # Para primeira execução com 150GB, usar chunks de 1M
    result = compare_data.sync_with_checkpoint(
        delta_table_name="seu_schema.dados_cadastrais",
        postgres_table_name="dados_cadastrais_postgres",
        key_columns=["penumper"],
        compare_columns=None,  # Todas as colunas
        chunk_size=1000000,    # 1M registros por chunk
        mark_for_deletion=True,
        job_id="primeira_carga_dados_cadastrais_20241226",
        auto_resume=True
    )
    
    # Exibir resultados
    logger.info("Primeira execução concluída:")
    logger.info(f"- Registros processados: {result['total_records_processed']:,}")
    logger.info(f"- Tempo de execução: {result['execution_time_minutes']:.1f} minutos")
    logger.info(f"- Throughput: {result['throughput_per_second']:,.0f} registros/segundo")
    logger.info(f"- Chunks processados: {result['chunks_processed']}")
    
    return result


def exemplo_monitoramento_progresso():
    """Exemplo de monitoramento de progresso via tabela PostgreSQL"""
    
    codigo_monitoramento = '''
import time
from datetime import datetime

def monitorar_job_postgres(compare_data, job_id):
    """Monitorar progresso do job via tabela PostgreSQL"""
    
    print(f"Monitorando job: {job_id}")
    print("-" * 60)
    
    while True:
        try:
            # Obter progresso do job
            progress = compare_data.get_job_progress(job_id)
            
            if not progress:
                print("Job não encontrado ou ainda não iniciado")
                time.sleep(30)
                continue
            
            status = progress['status']
            progress_pct = progress['progress_percentage']
            completed = progress['completed_chunks']
            total = progress['total_chunks']
            throughput = progress['avg_throughput']
            
            print(f"[{datetime.now().strftime('%H:%M:%S')}] "
                  f"Status: {status} | "
                  f"Progresso: {completed}/{total} chunks ({progress_pct:.1f}%) | "
                  f"Throughput: {throughput:,.0f} rec/s")
            
            # Verificar se concluído
            if status in ['COMPLETED', 'FAILED', 'CANCELLED']:
                print(f"Job finalizado com status: {status}")
                break
            
            time.sleep(30)  # Verificar a cada 30 segundos
            
        except Exception as e:
            print(f"Erro no monitoramento: {e}")
            time.sleep(30)

# Usar assim no notebook:
# monitorar_job_postgres(compare_data, "primeira_carga_dados_cadastrais_20241226")
'''
    
    return codigo_monitoramento


def exemplo_retomada_apos_falha():
    """Exemplo de retomada após falha usando checkpoint PostgreSQL"""
    
    codigo_retomada = '''
# Cenário: Job falhou após processar 45 de 100 chunks
# Com checkpoint PostgreSQL, basta executar novamente

from compare_data_postgres_checkpoint import CompareDataPostgresCheckpoint

# Inicializar (mesmo código da primeira execução)
compare_data = CompareDataPostgresCheckpoint(spark, logger)
compare_data.configure_postgres_connection(...)

# Executar novamente com MESMO job_id
# O sistema detectará automaticamente o checkpoint e retomará do chunk 46
result = compare_data.sync_with_checkpoint(
    delta_table_name="seu_schema.dados_cadastrais",
    postgres_table_name="dados_cadastrais_postgres",
    key_columns=["penumper"],
    chunk_size=1000000,
    mark_for_deletion=True,
    job_id="primeira_carga_dados_cadastrais_20241226",  # MESMO job_id
    auto_resume=True  # Retomar automaticamente
)

print("Retomada concluída com sucesso!")
print(f"Chunks processados: {result['chunks_processed']}")
print(f"Tempo total: {result['execution_time_minutes']:.1f} minutos")
'''
    
    return codigo_retomada


def exemplo_consultas_controle():
    """Exemplos de consultas nas tabelas de controle"""
    
    consultas_sql = '''
-- Consultas úteis nas tabelas de controle PostgreSQL

-- 1. Listar todos os jobs de sincronização
SELECT 
    job_id,
    delta_table_name,
    postgres_table_name,
    status,
    total_records,
    total_chunks,
    start_time,
    end_time,
    EXTRACT(EPOCH FROM (COALESCE(end_time, NOW()) - start_time))/60 as duracao_minutos
FROM public.sync_job_control
ORDER BY start_time DESC;

-- 2. Progresso detalhado de um job específico
SELECT 
    j.job_id,
    j.status as job_status,
    j.total_chunks,
    COUNT(c.chunk_id) as chunks_iniciados,
    COUNT(c.chunk_id) FILTER (WHERE c.status = 'COMPLETED') as chunks_concluidos,
    COUNT(c.chunk_id) FILTER (WHERE c.status = 'FAILED') as chunks_falharam,
    ROUND(
        (COUNT(c.chunk_id) FILTER (WHERE c.status = 'COMPLETED')::DECIMAL / j.total_chunks) * 100, 
        2
    ) as progresso_pct
FROM public.sync_job_control j
LEFT JOIN public.sync_chunk_control c ON j.job_id = c.job_id
WHERE j.job_id = 'primeira_carga_dados_cadastrais_20241226'
GROUP BY j.job_id, j.status, j.total_chunks;

-- 3. Performance por chunk (identificar gargalos)
SELECT 
    chunk_id,
    status,
    records_processed,
    copy_time_seconds,
    merge_time_seconds,
    throughput_per_second,
    EXTRACT(EPOCH FROM (end_time - start_time)) as total_time_seconds
FROM public.sync_chunk_control
WHERE job_id = 'primeira_carga_dados_cadastrais_20241226'
ORDER BY chunk_id;

-- 4. Chunks que falharam (para análise)
SELECT 
    chunk_id,
    error_message,
    start_time,
    updated_at
FROM public.sync_chunk_control
WHERE job_id = 'primeira_carga_dados_cadastrais_20241226'
AND status = 'FAILED'
ORDER BY chunk_id;

-- 5. Estatísticas gerais de performance
SELECT 
    AVG(throughput_per_second) as throughput_medio,
    MIN(throughput_per_second) as throughput_minimo,
    MAX(throughput_per_second) as throughput_maximo,
    AVG(copy_time_seconds) as tempo_copy_medio,
    AVG(merge_time_seconds) as tempo_merge_medio
FROM public.sync_chunk_control
WHERE job_id = 'primeira_carga_dados_cadastrais_20241226'
AND status = 'COMPLETED';

-- 6. Limpeza de jobs antigos (executar periodicamente)
DELETE FROM public.sync_job_control 
WHERE status = 'COMPLETED' 
AND start_time < NOW() - INTERVAL '30 days';
'''
    
    return consultas_sql


def exemplo_configuracao_producao():
    """Configuração recomendada para produção com 150GB"""
    
    configuracao = {
        'cluster_databricks': {
            'driver': 'Standard_D32s_v3 (32 cores, 128GB RAM)',
            'workers': '25-30x Standard_D16s_v3 (16 cores, 64GB RAM cada)',
            'runtime': 'Databricks Runtime 13.3 LTS ou 14.3 LTS',
            'storage': 'Premium SSD com 256GB por worker'
        },
        'postgresql': {
            'instancia': 'Mínimo 16 cores, 64GB RAM',
            'storage': 'SSD com IOPS provisionado',
            'configuracoes': {
                'shared_buffers': '16GB',
                'work_mem': '256MB',
                'maintenance_work_mem': '2GB',
                'checkpoint_completion_target': '0.9',
                'wal_buffers': '16MB',
                'max_connections': '200'
            }
        },
        'parametros_sincronizacao': {
            'chunk_size': 1000000,  # 1M registros
            'control_schema': 'public',
            'job_id': 'primeira_carga_dados_cadastrais_YYYYMMDD',
            'auto_resume': True,
            'mark_for_deletion': True
        }
    }
    
    return configuracao


def exemplo_notebook_databricks():
    """Código completo para notebook Databricks"""
    
    codigo_notebook = '''
# Célula 1: Importações e configuração
import logging
from compare_data_postgres_checkpoint import CompareDataPostgresCheckpoint

# Configurar logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

print("Iniciando sincronização com checkpoint PostgreSQL")

# Célula 2: Inicialização
compare_data = CompareDataPostgresCheckpoint(
    spark=spark,
    logger=logger,
    control_schema="public"
)

# Configurar PostgreSQL (substituir pelos seus dados)
compare_data.configure_postgres_connection(
    host="seu-host-postgres.com",
    port=5432,
    database="sua_database",
    user="seu_usuario",
    password="sua_senha"
)

print("Conexão PostgreSQL configurada e tabelas de controle criadas")

# Célula 3: Execução da sincronização
try:
    result = compare_data.sync_with_checkpoint(
        delta_table_name="seu_schema.dados_cadastrais",
        postgres_table_name="dados_cadastrais_postgres",
        key_columns=["penumper"],
        chunk_size=1000000,
        mark_for_deletion=True,
        job_id="primeira_carga_dados_cadastrais_20241226",
        auto_resume=True
    )
    
    print("SUCESSO: Sincronização concluída")
    print(f"Registros processados: {result['total_records_processed']:,}")
    print(f"Tempo de execução: {result['execution_time_minutes']:.1f} minutos")
    print(f"Throughput médio: {result['throughput_per_second']:,.0f} rec/s")
    
except Exception as e:
    print(f"ERRO: {e}")
    print("Checkpoint salvo no PostgreSQL - execute novamente para retomar")

# Célula 4: Monitoramento (executar em paralelo se necessário)
def monitorar_progresso():
    import time
    from datetime import datetime
    
    job_id = "primeira_carga_dados_cadastrais_20241226"
    
    while True:
        progress = compare_data.get_job_progress(job_id)
        
        if progress:
            print(f"[{datetime.now().strftime('%H:%M:%S')}] "
                  f"Status: {progress['status']} | "
                  f"Progresso: {progress['completed_chunks']}/{progress['total_chunks']} "
                  f"({progress['progress_percentage']:.1f}%)")
            
            if progress['status'] in ['COMPLETED', 'FAILED']:
                break
        
        time.sleep(60)  # Verificar a cada minuto

# Descomente para monitorar:
# monitorar_progresso()

# Célula 5: Validação dos resultados
stats = compare_data.get_sync_statistics("dados_cadastrais_postgres")
print(f"Estatísticas finais:")
print(f"- Total de registros: {stats['total_records']:,}")
print(f"- Registros ativos: {stats['active_records']:,}")
print(f"- Registros excluídos: {stats['deleted_records']:,}")
print(f"- Última atualização: {stats['last_update']}")
'''
    
    return codigo_notebook


def main():
    """Função principal com exemplos de uso"""
    
    print("Exemplos de Uso - Checkpoint PostgreSQL para 150GB")
    print("=" * 60)
    
    exemplos = {
        'Primeira Execução 150GB': exemplo_primeira_execucao_150gb,
        'Monitoramento Progresso': exemplo_monitoramento_progresso,
        'Retomada Após Falha': exemplo_retomada_apos_falha,
        'Consultas Controle': exemplo_consultas_controle,
        'Configuração Produção': exemplo_configuracao_producao,
        'Notebook Databricks': exemplo_notebook_databricks
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
    
    print("\n" + "=" * 60)
    print("Vantagens do Checkpoint PostgreSQL:")
    print("- Checkpoint persistente e confiável")
    print("- Monitoramento em tempo real via SQL")
    print("- Resume automático após qualquer falha")
    print("- Histórico completo de execuções")
    print("- Análise detalhada de performance")
    print("- Ideal para primeira execução com 150GB")


if __name__ == "__main__":
    main()

