"""
CompareDataProductionOptimized - Solução Otimizada para Sincronização PostgreSQL
Estratégia COPY + MERGE com checkpoint/resume para volumes de 150GB+

Características:
- UNLOGGED tables para máxima performance
- COPY em chunks de 1M registros
- MERGE nativo do PostgreSQL
- Checkpoint automático com resume
- Configurações otimizadas para Runtime 13/14
"""

import logging
import time
import json
import os
import psycopg2
import psycopg2.extras
from datetime import datetime
from typing import Dict, List, Optional, Any
from contextlib import contextmanager
from pyspark.sql import SparkSession
from pyspark.sql.functions import col, lit, current_timestamp, monotonically_increasing_id
import io


class CompareDataProductionOptimized:
    """
    Classe otimizada para sincronização Delta Lake para PostgreSQL
    Suporta volumes de 150GB+ com checkpoint/resume automático
    """
    
    def __init__(self, spark: SparkSession, logger: logging.Logger, 
                 checkpoint_dir: str = "/tmp/sync_checkpoints"):
        self.spark = spark
        self.logger = logger
        self.postgres_config = {}
        self.checkpoint_dir = checkpoint_dir
        self.current_job_id = None
        self.checkpoint_file = None
        
        # Criar diretório de checkpoint
        os.makedirs(checkpoint_dir, exist_ok=True)
        
        # Aplicar configurações otimizadas
        self._configure_spark_optimizations()
        
        self.logger.info(f"Sistema inicializado com checkpoint em: {checkpoint_dir}")
    
    def _configure_spark_optimizations(self):
        """Configurações Spark otimizadas para operações PostgreSQL em larga escala"""
        
        optimizations = {
            # Adaptive Query Execution otimizado
            "spark.sql.adaptive.enabled": "true",
            "spark.sql.adaptive.coalescePartitions.enabled": "true",
            "spark.sql.adaptive.advisoryPartitionSizeInBytes": "128MB",
            "spark.sql.adaptive.localShuffleReader.enabled": "true",
            
            # Broadcast otimizado para Runtime 13/14
            "spark.sql.autoBroadcastJoinThreshold": "50MB",
            "spark.sql.broadcastTimeout": "600",
            
            # Serialização e Arrow
            "spark.serializer": "org.apache.spark.serializer.KryoSerializer",
            "spark.sql.execution.arrow.pyspark.enabled": "true",
            "spark.sql.execution.arrow.maxRecordsPerBatch": "50000",
            "spark.sql.execution.arrow.pyspark.fallback.enabled": "true",
            
            # Configurações de I/O para grandes volumes
            "spark.sql.files.maxPartitionBytes": "256MB",
            "spark.sql.adaptive.skewJoin.enabled": "true",
            "spark.sql.adaptive.skewJoin.skewedPartitionThresholdInBytes": "256MB",
            
            # Configurações de memória
            "spark.sql.execution.arrow.pyspark.selfDestruct.enabled": "true",
            "spark.sql.adaptive.maxShuffledHashJoinLocalMapThreshold": "0"
        }
        
        for key, value in optimizations.items():
            try:
                current_value = self.spark.conf.get(key)
                if current_value != value:
                    self.spark.conf.set(key, value)
                    self.logger.debug(f"Configuração aplicada: {key} = {value}")
            except:
                self.spark.conf.set(key, value)
                self.logger.debug(f"Configuração definida: {key} = {value}")
    
    def configure_postgres_connection(self, host: str, port: int, database: str, 
                                    user: str, password: str, **kwargs):
        """Configurar parâmetros de conexão PostgreSQL"""
        
        self.postgres_config = {
            'host': host,
            'port': port,
            'database': database,
            'user': user,
            'password': password,
            'connect_timeout': 30,
            'application_name': 'spark_sync_optimizer',
            **kwargs
        }
        
        # Validar conexão
        try:
            with self._get_postgres_connection() as conn:
                cursor = conn.cursor()
                cursor.execute("SELECT version()")
                version = cursor.fetchone()[0]
                self.logger.info(f"Conexão PostgreSQL validada: {host}:{port}/{database}")
                self.logger.debug(f"Versão PostgreSQL: {version}")
        except Exception as e:
            self.logger.error(f"Erro na validação da conexão PostgreSQL: {e}")
            raise
    
    @contextmanager
    def _get_postgres_connection(self):
        """Context manager para conexões PostgreSQL com configurações otimizadas"""
        conn = None
        try:
            conn = psycopg2.connect(**self.postgres_config)
            conn.autocommit = False
            
            # Configurações de sessão otimizadas para ETL
            cursor = conn.cursor()
            cursor.execute("SET work_mem = '256MB'")
            cursor.execute("SET maintenance_work_mem = '1GB'")
            cursor.execute("SET checkpoint_completion_target = 0.9")
            cursor.execute("SET wal_buffers = '16MB'")
            cursor.execute("SET synchronous_commit = off")
            conn.commit()
            
            yield conn
            
        except Exception as e:
            if conn:
                conn.rollback()
            self.logger.error(f"Erro na conexão PostgreSQL: {e}")
            raise
        finally:
            if conn:
                conn.close()
    
    def sync_with_checkpoint(self, delta_table_name: str, postgres_table_name: str,
                           key_columns: List[str], compare_columns: Optional[List[str]] = None,
                           chunk_size: int = 1000000, mark_for_deletion: bool = True,
                           job_id: Optional[str] = None, auto_resume: bool = True) -> Dict[str, Any]:
        """
        Sincronização principal com checkpoint automático
        
        Parâmetros:
            delta_table_name: Nome da tabela no Delta Lake
            postgres_table_name: Nome da tabela no PostgreSQL
            key_columns: Lista de colunas chave para MERGE
            compare_columns: Colunas para comparar (None = todas)
            chunk_size: Tamanho do chunk em registros (padrão 1M)
            mark_for_deletion: Se deve marcar registros órfãos para exclusão
            job_id: Identificador único do job (auto-gerado se None)
            auto_resume: Se deve tentar retomar automaticamente
        
        Retorna:
            Dicionário com estatísticas da execução
        """
        
        # Configurar job ID
        if job_id is None:
            timestamp = datetime.now().strftime('%Y%m%d_%H%M%S')
            job_id = f"sync_{postgres_table_name.replace('.', '_')}_{timestamp}"
        
        self.current_job_id = job_id
        self.checkpoint_file = os.path.join(self.checkpoint_dir, f"{job_id}.json")
        
        self.logger.info(f"Iniciando sincronização com job ID: {job_id}")
        
        # Verificar checkpoint existente
        if auto_resume and os.path.exists(self.checkpoint_file):
            checkpoint_data = self._load_checkpoint()
            if checkpoint_data and self._validate_checkpoint(checkpoint_data, delta_table_name, postgres_table_name):
                self.logger.info(f"Retomando do checkpoint - chunk {checkpoint_data['last_completed_chunk'] + 1}")
                return self._resume_execution(checkpoint_data)
            else:
                self.logger.warning("Checkpoint inválido - iniciando nova execução")
                self._cleanup_checkpoint()
        
        # Iniciar nova execução
        return self._start_new_execution(delta_table_name, postgres_table_name, key_columns, 
                                       compare_columns, chunk_size, mark_for_deletion)
    
    def _start_new_execution(self, delta_table_name: str, postgres_table_name: str,
                           key_columns: List[str], compare_columns: Optional[List[str]],
                           chunk_size: int, mark_for_deletion: bool) -> Dict[str, Any]:
        """Iniciar nova execução com checkpoint"""
        
        start_time = time.time()
        self.logger.info("Iniciando nova execução de sincronização")
        
        # Analisar dados do Delta Lake
        df_delta = self.spark.table(delta_table_name)
        total_records = df_delta.count()
        num_chunks = (total_records + chunk_size - 1) // chunk_size
        
        self.logger.info(f"Dados analisados: {total_records:,} registros em {num_chunks} chunks")
        
        # Criar checkpoint inicial
        checkpoint_data = {
            'job_id': self.current_job_id,
            'start_time': start_time,
            'delta_table_name': delta_table_name,
            'postgres_table_name': postgres_table_name,
            'key_columns': key_columns,
            'compare_columns': compare_columns,
            'chunk_size': chunk_size,
            'mark_for_deletion': mark_for_deletion,
            'total_records': total_records,
            'total_chunks': num_chunks,
            'last_completed_chunk': -1,
            'completed_chunks': [],
            'failed_chunks': [],
            'aux_table_name': f"{postgres_table_name}_sync_aux",
            'status': 'RUNNING',
            'phase': 'COPY_MERGE',
            'performance_metrics': {
                'chunks_processed': 0,
                'total_copy_time': 0,
                'total_merge_time': 0,
                'avg_chunk_throughput': 0
            }
        }
        
        self._save_checkpoint(checkpoint_data)
        
        # Preparar ambiente PostgreSQL
        self._prepare_postgres_environment(checkpoint_data)
        
        # Executar sincronização
        return self._execute_sync_with_monitoring(df_delta, checkpoint_data)
    
    def _prepare_postgres_environment(self, checkpoint_data: Dict):
        """Preparar ambiente PostgreSQL otimizado"""
        
        aux_table_name = checkpoint_data['aux_table_name']
        main_table_name = checkpoint_data['postgres_table_name']
        key_columns = checkpoint_data['key_columns']
        
        self.logger.info(f"Preparando ambiente PostgreSQL - tabela auxiliar: {aux_table_name}")
        
        with self._get_postgres_connection() as conn:
            cursor = conn.cursor()
            
            # Remover tabela auxiliar se existir
            cursor.execute(f"DROP TABLE IF EXISTS {aux_table_name}")
            
            # Criar tabela UNLOGGED otimizada
            cursor.execute(f"""
                CREATE UNLOGGED TABLE {aux_table_name} 
                (LIKE {main_table_name} INCLUDING DEFAULTS)
                WITH (fillfactor = 100, autovacuum_enabled = false)
            """)
            
            # Criar índice apenas nas chaves primárias
            if key_columns:
                key_columns_str = ', '.join(key_columns)
                index_name = f"idx_{aux_table_name.split('.')[-1]}_keys"
                cursor.execute(f"""
                    CREATE INDEX {index_name} ON {aux_table_name} ({key_columns_str})
                    WITH (fillfactor = 100)
                """)
                self.logger.debug(f"Índice criado: {index_name}")
            
            conn.commit()
            self.logger.info("Ambiente PostgreSQL preparado com sucesso")
    
    def _execute_sync_with_monitoring(self, df_delta, checkpoint_data: Dict) -> Dict[str, Any]:
        """Executar sincronização com monitoramento de performance"""
        
        # Preparar dados para processamento
        df_prepared = self._prepare_delta_data(df_delta, checkpoint_data)
        
        # Determinar chunks a processar
        completed_chunks = set(checkpoint_data['completed_chunks'])
        chunks_to_process = [i for i in range(checkpoint_data['total_chunks']) 
                           if i not in completed_chunks]
        
        self.logger.info(f"Processando {len(chunks_to_process)} chunks restantes")
        
        # Processar chunks
        for chunk_id in chunks_to_process:
            try:
                self._process_chunk_with_metrics(df_prepared, chunk_id, checkpoint_data)
            except Exception as e:
                self.logger.error(f"Erro no chunk {chunk_id}: {e}")
                checkpoint_data['failed_chunks'].append({
                    'chunk_id': chunk_id,
                    'error': str(e),
                    'timestamp': time.time()
                })
                checkpoint_data['status'] = 'FAILED'
                self._save_checkpoint(checkpoint_data)
                raise
        
        # Finalizar sincronização
        return self._finalize_sync(checkpoint_data)
    
    def _prepare_delta_data(self, df_delta, checkpoint_data: Dict):
        """Preparar dados do Delta Lake para processamento otimizado"""
        
        key_columns = checkpoint_data['key_columns']
        compare_columns = checkpoint_data['compare_columns']
        
        # Determinar colunas a processar
        if compare_columns is None:
            all_columns = df_delta.columns
            compare_columns = [col for col in all_columns if col not in key_columns]
        
        columns_to_select = key_columns + compare_columns
        
        # Selecionar e preparar dados
        df_prepared = df_delta.select(*columns_to_select)
        
        # Adicionar metadados de controle
        df_prepared = df_prepared.withColumn("data_ultima_atualizacao", current_timestamp()) \
                                .withColumn("status_registro", lit("ATIVO")) \
                                .withColumn("origem_atualizacao", lit("DELTA_LAKE"))
        
        # Otimizar particionamento
        target_partitions = min(200, max(50, checkpoint_data['total_chunks'] // 4))
        df_prepared = df_prepared.coalesce(target_partitions)
        
        # Adicionar ID do chunk
        df_prepared = df_prepared.withColumn("chunk_id", 
                                           (monotonically_increasing_id() / checkpoint_data['chunk_size']).cast("int"))
        
        return df_prepared
    
    def _process_chunk_with_metrics(self, df_prepared, chunk_id: int, checkpoint_data: Dict):
        """Processar chunk individual com métricas detalhadas"""
        
        chunk_start_time = time.time()
        aux_table_name = checkpoint_data['aux_table_name']
        main_table_name = checkpoint_data['postgres_table_name']
        key_columns = checkpoint_data['key_columns']
        
        self.logger.info(f"Processando chunk {chunk_id + 1}/{checkpoint_data['total_chunks']}")
        
        # Limpar tabela auxiliar
        with self._get_postgres_connection() as conn:
            cursor = conn.cursor()
            cursor.execute(f"TRUNCATE TABLE {aux_table_name}")
            conn.commit()
        
        # Filtrar dados do chunk
        df_chunk = df_prepared.filter(col("chunk_id") == chunk_id).drop("chunk_id")
        chunk_data = df_chunk.collect()
        
        if not chunk_data:
            self.logger.info(f"Chunk {chunk_id + 1} vazio - pulando")
            return
        
        chunk_size = len(chunk_data)
        
        # Executar COPY otimizado
        copy_start_time = time.time()
        self._execute_optimized_copy(chunk_data, aux_table_name)
        copy_time = time.time() - copy_start_time
        
        # Executar MERGE otimizado
        merge_start_time = time.time()
        self._execute_optimized_merge(aux_table_name, main_table_name, key_columns)
        merge_time = time.time() - merge_start_time
        
        # Atualizar métricas
        total_chunk_time = time.time() - chunk_start_time
        chunk_throughput = chunk_size / total_chunk_time if total_chunk_time > 0 else 0
        
        # Atualizar checkpoint
        checkpoint_data['completed_chunks'].append(chunk_id)
        checkpoint_data['last_completed_chunk'] = chunk_id
        checkpoint_data['performance_metrics']['chunks_processed'] += 1
        checkpoint_data['performance_metrics']['total_copy_time'] += copy_time
        checkpoint_data['performance_metrics']['total_merge_time'] += merge_time
        
        # Calcular throughput médio
        metrics = checkpoint_data['performance_metrics']
        if metrics['chunks_processed'] > 0:
            total_time = metrics['total_copy_time'] + metrics['total_merge_time']
            total_records = metrics['chunks_processed'] * checkpoint_data['chunk_size']
            metrics['avg_chunk_throughput'] = total_records / total_time if total_time > 0 else 0
        
        self._save_checkpoint(checkpoint_data)
        
        self.logger.info(f"Chunk {chunk_id + 1} concluído: {chunk_size:,} registros em {total_chunk_time:.1f}s "
                        f"(throughput: {chunk_throughput:,.0f} rec/s)")
    
    def _execute_optimized_copy(self, chunk_data: List, aux_table_name: str):
        """Executar COPY otimizado com configurações de performance"""
        
        if not chunk_data:
            return
        
        with self._get_postgres_connection() as conn:
            cursor = conn.cursor()
            
            # Obter estrutura da tabela
            cursor.execute(f"""
                SELECT column_name, data_type 
                FROM information_schema.columns 
                WHERE table_name = '{aux_table_name.split('.')[-1]}'
                ORDER BY ordinal_position
            """)
            
            columns_info = cursor.fetchall()
            column_names = [col[0] for col in columns_info]
            
            # Preparar dados para COPY
            copy_buffer = io.StringIO()
            
            for row in chunk_data:
                row_values = []
                for col_name in column_names:
                    value = getattr(row, col_name, None)
                    if value is None:
                        row_values.append('\\N')
                    elif isinstance(value, str):
                        # Escapar caracteres especiais
                        escaped_value = value.replace('\\', '\\\\').replace('\t', '\\t').replace('\n', '\\n').replace('\r', '\\r')
                        row_values.append(escaped_value)
                    else:
                        row_values.append(str(value))
                
                copy_buffer.write('\t'.join(row_values) + '\n')
            
            # Executar COPY
            copy_buffer.seek(0)
            copy_sql = f"""
                COPY {aux_table_name} ({', '.join(column_names)})
                FROM STDIN WITH (FORMAT TEXT, DELIMITER E'\\t', NULL '\\N', ENCODING 'UTF8')
            """
            
            cursor.copy_expert(copy_sql, copy_buffer)
            
            # ANALYZE para otimizar planner
            cursor.execute(f"ANALYZE {aux_table_name}")
            conn.commit()
    
    def _execute_optimized_merge(self, aux_table_name: str, main_table_name: str, key_columns: List[str]):
        """Executar MERGE otimizado usando INSERT ... ON CONFLICT"""
        
        with self._get_postgres_connection() as conn:
            cursor = conn.cursor()
            
            # Obter colunas da tabela auxiliar (exceto metadados de controle)
            cursor.execute(f"""
                SELECT column_name 
                FROM information_schema.columns 
                WHERE table_name = '{aux_table_name.split('.')[-1]}'
                AND column_name NOT IN ('data_ultima_atualizacao', 'status_registro', 'origem_atualizacao')
                ORDER BY ordinal_position
            """)
            
            data_columns = [row[0] for row in cursor.fetchall()]
            
            # Construir SQL do MERGE
            all_columns = data_columns + ['data_ultima_atualizacao', 'status_registro', 'origem_atualizacao']
            
            # Cláusula INSERT
            insert_columns = ', '.join(all_columns)
            select_values = []
            for col in all_columns:
                if col in data_columns:
                    select_values.append(f"s.{col}")
                elif col == 'data_ultima_atualizacao':
                    select_values.append("s.data_ultima_atualizacao")
                elif col == 'status_registro':
                    select_values.append("s.status_registro")
                elif col == 'origem_atualizacao':
                    select_values.append("s.origem_atualizacao")
            
            # Cláusula UPDATE
            update_sets = []
            for col in data_columns:
                if col not in key_columns:
                    update_sets.append(f"{col} = EXCLUDED.{col}")
            
            update_sets.extend([
                "data_ultima_atualizacao = EXCLUDED.data_ultima_atualizacao",
                "status_registro = EXCLUDED.status_registro",
                "origem_atualizacao = EXCLUDED.origem_atualizacao"
            ])
            
            # SQL final do MERGE
            merge_sql = f"""
                INSERT INTO {main_table_name} ({insert_columns})
                SELECT {', '.join(select_values)}
                FROM {aux_table_name} s
                ON CONFLICT ({', '.join(key_columns)})
                DO UPDATE SET {', '.join(update_sets)}
            """
            
            cursor.execute(merge_sql)
            rows_affected = cursor.rowcount
            conn.commit()
            
            self.logger.debug(f"MERGE executado: {rows_affected:,} registros processados")
    
    def _finalize_sync(self, checkpoint_data: Dict) -> Dict[str, Any]:
        """Finalizar sincronização com limpeza e estatísticas"""
        
        self.logger.info("Finalizando sincronização")
        
        # Executar soft delete se solicitado
        deleted_records = 0
        if checkpoint_data['mark_for_deletion']:
            checkpoint_data['phase'] = 'SOFT_DELETE'
            self._save_checkpoint(checkpoint_data)
            deleted_records = self._execute_soft_delete(checkpoint_data)
        
        # Limpar tabela auxiliar
        self._cleanup_auxiliary_table(checkpoint_data['aux_table_name'])
        
        # Calcular estatísticas finais
        total_time = time.time() - checkpoint_data['start_time']
        metrics = checkpoint_data['performance_metrics']
        
        result = {
            'success': True,
            'job_id': checkpoint_data['job_id'],
            'total_records_processed': checkpoint_data['total_records'],
            'deleted_records_marked': deleted_records,
            'execution_time_seconds': total_time,
            'execution_time_minutes': total_time / 60,
            'throughput_per_second': checkpoint_data['total_records'] / total_time if total_time > 0 else 0,
            'chunks_processed': len(checkpoint_data['completed_chunks']),
            'chunks_failed': len(checkpoint_data['failed_chunks']),
            'avg_copy_time_per_chunk': metrics['total_copy_time'] / metrics['chunks_processed'] if metrics['chunks_processed'] > 0 else 0,
            'avg_merge_time_per_chunk': metrics['total_merge_time'] / metrics['chunks_processed'] if metrics['chunks_processed'] > 0 else 0,
            'avg_chunk_throughput': metrics['avg_chunk_throughput']
        }
        
        # Finalizar checkpoint
        checkpoint_data['status'] = 'COMPLETED'
        checkpoint_data['end_time'] = time.time()
        checkpoint_data['final_result'] = result
        self._save_checkpoint(checkpoint_data)
        
        self.logger.info(f"Sincronização concluída: {checkpoint_data['total_records']:,} registros em {total_time/60:.1f} minutos")
        self.logger.info(f"Throughput médio: {result['throughput_per_second']:,.0f} registros/segundo")
        
        # Arquivar checkpoint
        self._archive_checkpoint()
        
        return result
    
    def _execute_soft_delete(self, checkpoint_data: Dict) -> int:
        """Executar soft delete de registros órfãos"""
        
        self.logger.info("Executando soft delete de registros órfãos")
        
        aux_table_name = checkpoint_data['aux_table_name']
        main_table_name = checkpoint_data['postgres_table_name']
        key_columns = checkpoint_data['key_columns']
        
        with self._get_postgres_connection() as conn:
            cursor = conn.cursor()
            
            # Criar tabela temporária com chaves do Delta Lake
            temp_keys_table = f"{main_table_name}_keys_temp"
            cursor.execute(f"DROP TABLE IF EXISTS {temp_keys_table}")
            
            # Extrair chaves únicas da tabela auxiliar
            key_columns_str = ', '.join(key_columns)
            cursor.execute(f"""
                CREATE TEMP TABLE {temp_keys_table} AS
                SELECT DISTINCT {key_columns_str}
                FROM {aux_table_name}
            """)
            
            # Criar índice na tabela temporária
            cursor.execute(f"CREATE INDEX ON {temp_keys_table} ({key_columns_str})")
            
            # Executar soft delete
            key_conditions = ' AND '.join([f"m.{col} = t.{col}" for col in key_columns])
            
            soft_delete_sql = f"""
                UPDATE {main_table_name} m
                SET 
                    status_registro = 'EXCLUIDO',
                    data_exclusao = NOW(),
                    motivo_exclusao = 'NAO_ENCONTRADO_FONTE',
                    origem_exclusao = 'SOFT_DELETE_PROCESS'
                WHERE NOT EXISTS (
                    SELECT 1 FROM {temp_keys_table} t 
                    WHERE {key_conditions}
                )
                AND m.status_registro = 'ATIVO'
            """
            
            cursor.execute(soft_delete_sql)
            deleted_count = cursor.rowcount
            conn.commit()
            
            self.logger.info(f"Soft delete concluído: {deleted_count:,} registros marcados")
            return deleted_count
    
    def _cleanup_auxiliary_table(self, aux_table_name: str):
        """Remover tabela auxiliar"""
        try:
            with self._get_postgres_connection() as conn:
                cursor = conn.cursor()
                cursor.execute(f"DROP TABLE IF EXISTS {aux_table_name}")
                conn.commit()
                self.logger.info(f"Tabela auxiliar removida: {aux_table_name}")
        except Exception as e:
            self.logger.warning(f"Erro ao remover tabela auxiliar: {e}")
    
    def _save_checkpoint(self, checkpoint_data: Dict):
        """Salvar checkpoint em arquivo JSON"""
        try:
            checkpoint_data['last_update'] = time.time()
            with open(self.checkpoint_file, 'w') as f:
                json.dump(checkpoint_data, f, indent=2, default=str)
        except Exception as e:
            self.logger.warning(f"Erro ao salvar checkpoint: {e}")
    
    def _load_checkpoint(self) -> Optional[Dict]:
        """Carregar checkpoint do arquivo"""
        try:
            with open(self.checkpoint_file, 'r') as f:
                return json.load(f)
        except Exception as e:
            self.logger.warning(f"Erro ao carregar checkpoint: {e}")
            return None
    
    def _validate_checkpoint(self, checkpoint_data: Dict, delta_table: str, postgres_table: str) -> bool:
        """Validar compatibilidade do checkpoint"""
        try:
            # Verificar compatibilidade básica
            if (checkpoint_data.get('delta_table_name') != delta_table or 
                checkpoint_data.get('postgres_table_name') != postgres_table):
                return False
            
            # Verificar idade (máximo 24 horas)
            if time.time() - checkpoint_data.get('start_time', 0) > 86400:
                self.logger.warning("Checkpoint muito antigo - ignorando")
                return False
            
            # Verificar se não foi completado
            if checkpoint_data.get('status') == 'COMPLETED':
                self.logger.info("Job já foi completado anteriormente")
                return False
            
            return True
        except Exception as e:
            self.logger.warning(f"Erro na validação do checkpoint: {e}")
            return False
    
    def _resume_execution(self, checkpoint_data: Dict) -> Dict[str, Any]:
        """Retomar execução do checkpoint"""
        
        self.logger.info("Retomando execução do checkpoint")
        
        # Recarregar dados do Delta Lake
        df_delta = self.spark.table(checkpoint_data['delta_table_name'])
        
        # Verificar se tabela auxiliar ainda existe
        aux_table_name = checkpoint_data['aux_table_name']
        if not self._check_aux_table_exists(aux_table_name):
            self.logger.warning("Tabela auxiliar não encontrada - recriando")
            self._prepare_postgres_environment(checkpoint_data)
        
        # Continuar execução
        checkpoint_data['status'] = 'RESUMING'
        self._save_checkpoint(checkpoint_data)
        
        return self._execute_sync_with_monitoring(df_delta, checkpoint_data)
    
    def _check_aux_table_exists(self, aux_table_name: str) -> bool:
        """Verificar se tabela auxiliar existe"""
        try:
            with self._get_postgres_connection() as conn:
                cursor = conn.cursor()
                cursor.execute(f"""
                    SELECT EXISTS (
                        SELECT FROM information_schema.tables 
                        WHERE table_name = '{aux_table_name.split('.')[-1]}'
                    )
                """)
                return cursor.fetchone()[0]
        except Exception as e:
            self.logger.warning(f"Erro ao verificar tabela auxiliar: {e}")
            return False
    
    def _cleanup_checkpoint(self):
        """Remover checkpoint atual"""
        try:
            if os.path.exists(self.checkpoint_file):
                os.remove(self.checkpoint_file)
                self.logger.info("Checkpoint removido")
        except Exception as e:
            self.logger.warning(f"Erro ao remover checkpoint: {e}")
    
    def _archive_checkpoint(self):
        """Arquivar checkpoint concluído"""
        try:
            archive_dir = os.path.join(self.checkpoint_dir, "completed")
            os.makedirs(archive_dir, exist_ok=True)
            
            if os.path.exists(self.checkpoint_file):
                archive_file = os.path.join(archive_dir, f"{self.current_job_id}_completed.json")
                os.rename(self.checkpoint_file, archive_file)
                self.logger.info(f"Checkpoint arquivado: {archive_file}")
        except Exception as e:
            self.logger.warning(f"Erro ao arquivar checkpoint: {e}")
    
    def get_sync_statistics(self, postgres_table: str) -> Dict[str, Any]:
        """Obter estatísticas da sincronização"""
        try:
            with self._get_postgres_connection() as conn:
                cursor = conn.cursor()
                
                cursor.execute(f"""
                    SELECT 
                        COUNT(*) as total_records,
                        COUNT(*) FILTER (WHERE status_registro = 'ATIVO') as active_records,
                        COUNT(*) FILTER (WHERE status_registro = 'EXCLUIDO') as deleted_records,
                        MAX(data_ultima_atualizacao) as last_update
                    FROM {postgres_table}
                """)
                
                stats = cursor.fetchone()
                return {
                    'total_records': stats[0],
                    'active_records': stats[1],
                    'deleted_records': stats[2],
                    'last_update': stats[3]
                }
        except Exception as e:
            self.logger.error(f"Erro ao obter estatísticas: {e}")
            return {}
    
    def list_checkpoints(self) -> List[Dict]:
        """Listar checkpoints disponíveis"""
        checkpoints = []
        try:
            for file in os.listdir(self.checkpoint_dir):
                if file.endswith('.json'):
                    file_path = os.path.join(self.checkpoint_dir, file)
                    try:
                        with open(file_path, 'r') as f:
                            checkpoint = json.load(f)
                        
                        checkpoints.append({
                            'job_id': checkpoint.get('job_id'),
                            'status': checkpoint.get('status'),
                            'progress': f"{len(checkpoint.get('completed_chunks', []))}/{checkpoint.get('total_chunks', 0)}",
                            'start_time': datetime.fromtimestamp(checkpoint.get('start_time', 0)).strftime('%Y-%m-%d %H:%M:%S'),
                            'file': file_path
                        })
                    except Exception as e:
                        self.logger.warning(f"Erro ao ler checkpoint {file}: {e}")
        except Exception as e:
            self.logger.warning(f"Erro ao listar checkpoints: {e}")
        
        return checkpoints

