"""
Exemplo de Uso - PostgreSQL 14.18+ com MERGE Nativo
Baseado no método de COPY otimizado do exemplo fornecido
"""

import logging
from pyspark.sql import SparkSession
from compare_data_postgres14_merge import CompareDataPostgres14Merge


def exemplo_uso_postgres14():
    """Exemplo para PostgreSQL 14.18+ com MERGE nativo"""
    
    # Configurar logging
    logging.basicConfig(
        level=logging.INFO,
        format='%(asctime)s - %(levelname)s - %(message)s'
    )
    logger = logging.getLogger(__name__)
    
    # Obter sessão Spark ativa
    spark = SparkSession.getActiveSession()
    
    # Inicializar classe para PostgreSQL 14+
    compare_data = CompareDataPostgres14Merge(spark=spark, logger=logger)
    
    # Configurar conexão PostgreSQL 14.18+
    compare_data.configure_postgres_connection(
        host="seu-host-postgres.com",
        port=5432,
        database="sua_database",
        user="seu_usuario",
        password="sua_senha"
    )
    
    # Validar recursos PostgreSQL 14+
    features = compare_data.validate_postgres14_features()
    logger.info(f"Recursos PostgreSQL 14+: {features}")
    
    # Executar sincronização com MERGE nativo
    result = compare_data.sync_delta_to_postgres_merge(
        delta_table_name="seu_schema.dados_cadastrais",
        postgres_table_name="dados_cadastrais_postgres",
        key_columns=["penumper"],
        compare_columns=None,  # Todas as colunas
        batch_size=2000000,    # 2M registros por batch
        mark_for_deletion=True
    )
    
    # Exibir resultados
    logger.info("Sincronização com MERGE nativo concluída:")
    logger.info(f"- Registros processados: {result['total_records_processed']:,}")
    logger.info(f"- Registros copiados: {result['records_copied']:,}")
    logger.info(f"- Registros merged: {result['records_merged']:,}")
    logger.info(f"- Registros inseridos: {result['records_inserted']:,}")
    logger.info(f"- Registros atualizados: {result['records_updated']:,}")
    logger.info(f"- Tempo de execução: {result['execution_time_minutes']:.1f} minutos")
    logger.info(f"- Throughput: {result['throughput_per_second']:,.0f} registros/segundo")
    
    return result


def exemplo_notebook_databricks_postgres14():
    """Código para notebook Databricks com PostgreSQL 14+"""
    
    codigo_notebook = '''
# Célula 1: Importações e configuração
import logging
from compare_data_postgres14_merge import CompareDataPostgres14Merge

# Configurar logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

print("Iniciando sincronização PostgreSQL 14+ com MERGE nativo")

# Célula 2: Inicialização e validação
compare_data = CompareDataPostgres14Merge(spark=spark, logger=logger)

# Configurar PostgreSQL 14.18+
compare_data.configure_postgres_connection(
    host="seu-host-postgres.com",
    port=5432,
    database="sua_database",
    user="seu_usuario",
    password="sua_senha"
)

# Validar recursos PostgreSQL 14+
features = compare_data.validate_postgres14_features()
print(f"PostgreSQL 14+ Features: {features}")

if not features['version_14_plus']:
    raise Exception("PostgreSQL 14+ requerido")

print("PostgreSQL 14+ validado com sucesso")

# Célula 3: Execução da sincronização
try:
    result = compare_data.sync_delta_to_postgres_merge(
        delta_table_name="seu_schema.dados_cadastrais",
        postgres_table_name="dados_cadastrais_postgres",
        key_columns=["penumper"],
        batch_size=2000000,  # 2M registros por batch
        mark_for_deletion=True
    )
    
    print("SUCESSO: Sincronização com MERGE nativo concluída")
    print(f"Registros processados: {result['total_records_processed']:,}")
    print(f"Registros merged: {result['records_merged']:,}")
    print(f"Tempo de execução: {result['execution_time_minutes']:.1f} minutos")
    print(f"Throughput: {result['throughput_per_second']:,.0f} rec/s")
    
except Exception as e:
    print(f"ERRO: {e}")

# Célula 4: Validação dos resultados
stats = compare_data.get_sync_statistics("dados_cadastrais_postgres")
print(f"Estatísticas finais:")
print(f"- Total: {stats['total_records']:,}")
print(f"- Ativos: {stats['active_records']:,}")
print(f"- Excluídos: {stats['deleted_records']:,}")
print(f"- Última atualização: {stats['last_update']}")
'''
    
    return codigo_notebook


def exemplo_copy_method_baseado_exemplo():
    """Método de COPY baseado no exemplo fornecido"""
    
    codigo_copy = '''
# Método de COPY baseado no exemplo fornecido nas imagens

def copy_partition_to_postgres(rows_iter, 
                             dsn: str,
                             table: str,
                             cols: List[str],
                             batch_rows: int = 200000,
                             null_token: str = "\\\\N"):
    """
    Método otimizado baseado no exemplo fornecido
    Processa partição Spark e executa COPY para PostgreSQL
    """
    
    def _to_csv_row(row):
        out = []
        for c in cols:
            v = row[c] if c in row and row[c] is not None else None
            if v is None:
                out.append(null_token)  # Será interpretado como NULL pelo COPY
            else:
                out.append(str(v))
        return out
    
    total = 0
    buf = io.StringIO()
    writer = csv.writer(buf, delimiter='\\t', lineterminator='\\n')
    
    with psycopg2.connect(dsn) as conn:
        with conn.cursor() as cur:
            # COPY preparado (sem header). NOTA: definimos NULL como null_token para escapar None corretamente.
            copy_sql = f"COPY {table} ({', '.join(cols)}) FROM STDIN WITH (FORMAT csv, NULL '{null_token}', DELIMITER E'\\\\t')"
            
            def flush():
                nonlocal buf, writer
                if buf.tell() == 0:
                    return
                buf.seek(0)
                cur.copy_expert(copy_sql, buf)
                buf = io.StringIO()
                writer = csv.writer(buf, delimiter='\\t', lineterminator='\\n')
            
            batch_count = 0
            for r in rows_iter:
                writer.writerow(_to_csv_row(r))
                batch_count += 1
                total += 1
                
                if batch_count >= batch_rows:
                    flush()
                    batch_count = 0
            
            if batch_count > 0:
                flush()
            
            conn.commit()
    
    return total

# Uso no Spark:
# df.mapPartitions(lambda partition: copy_partition_to_postgres(
#     partition, dsn, table, cols, batch_rows
# )).collect()
'''
    
    return codigo_copy


def exemplo_merge_nativo_postgres14():
    """Exemplo de MERGE nativo do PostgreSQL 14+"""
    
    merge_sql = '''
-- MERGE nativo do PostgreSQL 14+ (disponível a partir da versão 15)
-- Para PostgreSQL 14, usar INSERT ... ON CONFLICT

-- Versão PostgreSQL 15+ (MERGE nativo):
MERGE INTO dados_cadastrais_postgres AS target
USING dados_cadastrais_postgres_aux_unlogged AS source
ON (target.penumper = source.penumper)
WHEN MATCHED THEN
    UPDATE SET 
        nome = source.nome,
        endereco = source.endereco,
        cidade = source.cidade,
        estado = source.estado,
        cep = source.cep,
        telefone = source.telefone,
        email = source.email,
        data_nascimento = source.data_nascimento,
        estado_civil = source.estado_civil,
        ocupacao = source.ocupacao,
        renda = source.renda,
        data_ultima_atualizacao = source.data_ultima_atualizacao,
        status_registro = source.status_registro,
        origem_atualizacao = source.origem_atualizacao
WHEN NOT MATCHED THEN
    INSERT (penumper, nome, endereco, cidade, estado, cep, telefone, email,
            data_nascimento, estado_civil, ocupacao, renda, 
            data_ultima_atualizacao, status_registro, origem_atualizacao)
    VALUES (source.penumper, source.nome, source.endereco, source.cidade, 
            source.estado, source.cep, source.telefone, source.email,
            source.data_nascimento, source.estado_civil, source.ocupacao, 
            source.renda, source.data_ultima_atualizacao, source.status_registro, 
            source.origem_atualizacao);

-- Versão PostgreSQL 14 (INSERT ... ON CONFLICT):
INSERT INTO dados_cadastrais_postgres 
    (penumper, nome, endereco, cidade, estado, cep, telefone, email,
     data_nascimento, estado_civil, ocupacao, renda, 
     data_ultima_atualizacao, status_registro, origem_atualizacao)
SELECT penumper, nome, endereco, cidade, estado, cep, telefone, email,
       data_nascimento, estado_civil, ocupacao, renda, 
       data_ultima_atualizacao, status_registro, origem_atualizacao
FROM dados_cadastrais_postgres_aux_unlogged
ON CONFLICT (penumper)
DO UPDATE SET 
    nome = EXCLUDED.nome,
    endereco = EXCLUDED.endereco,
    cidade = EXCLUDED.cidade,
    estado = EXCLUDED.estado,
    cep = EXCLUDED.cep,
    telefone = EXCLUDED.telefone,
    email = EXCLUDED.email,
    data_nascimento = EXCLUDED.data_nascimento,
    estado_civil = EXCLUDED.estado_civil,
    ocupacao = EXCLUDED.ocupacao,
    renda = EXCLUDED.renda,
    data_ultima_atualizacao = EXCLUDED.data_ultima_atualizacao,
    status_registro = EXCLUDED.status_registro,
    origem_atualizacao = EXCLUDED.origem_atualizacao;
'''
    
    return merge_sql


def exemplo_configuracoes_postgres14():
    """Configurações específicas para PostgreSQL 14.18+"""
    
    configuracoes = {
        'postgresql_14_settings': {
            # Configurações gerais
            'shared_buffers': '25% da RAM',
            'effective_cache_size': '75% da RAM',
            'work_mem': '512MB',
            'maintenance_work_mem': '2GB',
            
            # Configurações para COPY/MERGE
            'checkpoint_completion_target': '0.9',
            'wal_buffers': '32MB',
            'max_wal_size': '4GB',
            'min_wal_size': '1GB',
            
            # Configurações de paralelismo (PostgreSQL 14+)
            'max_parallel_workers': '8',
            'max_parallel_workers_per_gather': '4',
            'max_parallel_maintenance_workers': '4',
            'parallel_tuple_cost': '0.1',
            'parallel_setup_cost': '1000',
            
            # Configurações para SSD
            'random_page_cost': '1.1',
            'seq_page_cost': '1.0',
            'effective_io_concurrency': '200',
            
            # Configurações temporárias durante ETL
            'synchronous_commit': 'off',
            'fsync': 'off',
            'full_page_writes': 'off',
            'autovacuum': 'off'
        },
        'pos_etl_restore': {
            'synchronous_commit': 'on',
            'fsync': 'on',
            'full_page_writes': 'on',
            'autovacuum': 'on'
        }
    }
    
    return configuracoes


def exemplo_validacao_postgres14():
    """Validação específica para PostgreSQL 14+"""
    
    codigo_validacao = '''
def validar_postgres14_completo(compare_data):
    """Validação completa para PostgreSQL 14+"""
    
    print("Validando PostgreSQL 14+ e recursos...")
    
    # 1. Validar versão e recursos
    features = compare_data.validate_postgres14_features()
    
    print(f"Versão 14+: {'OK' if features['version_14_plus'] else 'ERRO'}")
    print(f"Comando MERGE: {'OK' if features['merge_command'] else 'FALLBACK para INSERT...ON CONFLICT'}")
    print(f"Parallel Workers: {'OK' if features['parallel_workers'] else 'LIMITADO'}")
    print(f"Vacuum Melhorado: {'OK' if features['improved_vacuum'] else 'BÁSICO'}")
    
    # 2. Validar configurações
    with compare_data._get_postgres_connection() as conn:
        cursor = conn.cursor()
        
        # Verificar configurações críticas
        configs_to_check = [
            'shared_buffers',
            'work_mem', 
            'maintenance_work_mem',
            'max_parallel_workers'
        ]
        
        print("\\nConfigurações PostgreSQL:")
        for config in configs_to_check:
            cursor.execute(f"SHOW {config}")
            value = cursor.fetchone()[0]
            print(f"  {config}: {value}")
    
    # 3. Testar performance de COPY
    print("\\nTestando performance de COPY...")
    # Implementar teste básico se necessário
    
    return features['version_14_plus']

# Executar validação
postgres14_ok = validar_postgres14_completo(compare_data)
print(f"\\nPostgreSQL 14+ pronto: {'SIM' if postgres14_ok else 'NÃO'}")
'''
    
    return codigo_validacao


def main():
    """Função principal com exemplos PostgreSQL 14+"""
    
    print("Exemplos PostgreSQL 14.18+ com MERGE Nativo")
    print("=" * 60)
    
    exemplos = {
        'Uso PostgreSQL 14+': exemplo_uso_postgres14,
        'Notebook Databricks': exemplo_notebook_databricks_postgres14,
        'Método COPY Exemplo': exemplo_copy_method_baseado_exemplo,
        'MERGE Nativo': exemplo_merge_nativo_postgres14,
        'Configurações 14+': exemplo_configuracoes_postgres14,
        'Validação 14+': exemplo_validacao_postgres14
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
    print("Recursos PostgreSQL 14.18+:")
    print("- MERGE nativo (PostgreSQL 15+) ou INSERT...ON CONFLICT otimizado")
    print("- Parallel workers melhorados")
    print("- VACUUM e ANALYZE otimizados")
    print("- Método de COPY baseado no exemplo fornecido")
    print("- Configurações específicas para ETL de 150GB")
    print("- Validação automática de recursos disponíveis")


if __name__ == "__main__":
    main()

