"""
CompareDataPostgresCheckpoint - Solução com Checkpoint em Tabela PostgreSQL
Estratégia COPY + MERGE com checkpoint/resume usando tabela de controle no PostgreSQL

Características:
- Checkpoint armazenado em tabela PostgreSQL
- Resume automático baseado em registros da tabela de controle
- Otimizado para primeira execução com grandes volumes
- Configurações específicas para Runtime 13/14
"""

import logging
import time
import json
import psycopg2
import psycopg2.extras
from datetime import datetime
from typing import Dict, List, Optional, Any
from contextlib import contextmanager
from pyspark.sql import SparkSession
from pyspark.sql.functions import col, lit, current_timestamp, monotonically_increasing_id
import io


class CompareDataPostgresCheckpoint:
    """
    Classe otimizada para sincronização Delta Lake para PostgreSQL
    com checkpoint armazenado em tabela de controle PostgreSQL
    """
    
    def __init__(self, spark: SparkSession, logger: logging.Logger, 
                 control_schema: str = "public"):
        self.spark = spark
        self.logger = logger
        self.postgres_config = {}
        self.control_schema = control_schema
        self.control_table = f"{control_schema}.sync_job_control"
        self.chunk_control_table = f"{control_schema}.sync_chunk_control"
        self.current_job_id = None
        
        # Aplicar configurações otimizadas
        self._configure_spark_optimizations()
        
        self.logger.info(f"Sistema inicializado com checkpoint PostgreSQL: {self.control_table}")
    
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
        
        # Validar conexão e criar tabelas de controle
        try:
            with self._get_postgres_connection() as conn:
                cursor = conn.cursor()
                cursor.execute("SELECT version()")
                version = cursor.fetchone()[0]
                self.logger.info(f"Conexão PostgreSQL validada: {host}:{port}/{database}")
                self.logger.debug(f"Versão PostgreSQL: {version}")
                
                # Criar tabelas de controle
                self._create_control_tables()
                
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
    
    def _create_control_tables(self):
        """Criar tabelas de controle para checkpoint no PostgreSQL"""
        
        with self._get_postgres_connection() as conn:
            cursor = conn.cursor()
            
            # Tabela principal de controle de jobs
            cursor.execute(f"""
                CREATE TABLE IF NOT EXISTS {self.control_table} (
                    job_id VARCHAR(255) PRIMARY KEY,
                    delta_table_name VARCHAR(255) NOT NULL,
                    postgres_table_name VARCHAR(255) NOT NULL,
                    key_columns TEXT NOT NULL,
                    compare_columns TEXT,
                    chunk_size INTEGER NOT NULL,
                    mark_for_deletion BOOLEAN NOT NULL,
                    total_records BIGINT,
                    total_chunks INTEGER,
                    status VARCHAR(50) NOT NULL,
                    phase VARCHAR(50) NOT NULL,
                    start_time TIMESTAMP NOT NULL,
                    end_time TIMESTAMP,
                    last_update TIMESTAMP NOT NULL DEFAULT NOW(),
                    aux_table_name VARCHAR(255),
                    error_message TEXT,
                    performance_metrics JSONB,
                    created_at TIMESTAMP NOT NULL DEFAULT NOW()
                )
            """)
            
            # Tabela de controle de chunks
            cursor.execute(f"""
                CREATE TABLE IF NOT EXISTS {self.chunk_control_table} (
                    job_id VARCHAR(255) NOT NULL,
                    chunk_id INTEGER NOT NULL,
                    status VARCHAR(50) NOT NULL,
                    start_time TIMESTAMP,
                    end_time TIMESTAMP,
                    records_processed INTEGER,
                    copy_time_seconds DECIMAL(10,3),
                    merge_time_seconds DECIMAL(10,3),
                    throughput_per_second DECIMAL(15,2),
                    error_message TEXT,
                    created_at TIMESTAMP NOT NULL DEFAULT NOW(),
                    updated_at TIMESTAMP NOT NULL DEFAULT NOW(),
                    PRIMARY KEY (job_id, chunk_id),
                    FOREIGN KEY (job_id) REFERENCES {self.control_table}(job_id)
                )
            """)
            
            # Índices para performance
            cursor.execute(f"""
                CREATE INDEX IF NOT EXISTS idx_sync_job_control_status 
                ON {self.control_table}(status, start_time)
            """)
            
            cursor.execute(f"""
                CREATE INDEX IF NOT EXISTS idx_sync_chunk_control_status 
                ON {self.chunk_control_table}(job_id, status)
            """)
            
            conn.commit()
            self.logger.info("Tabelas de controle criadas/validadas com sucesso")
    
    def sync_with_checkpoint(self, delta_table_name: str, postgres_table_name: str,
                           key_columns: List[str], compare_columns: Optional[List[str]] = None,
                           chunk_size: int = 1000000, mark_for_deletion: bool = True,
                           job_id: Optional[str] = None, auto_resume: bool = True) -> Dict[str, Any]:
        """
        Sincronização principal com checkpoint em tabela PostgreSQL
        
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
        
        self.logger.info(f"Iniciando sincronização com job ID: {job_id}")
        
        # Verificar checkpoint existente
        if auto_resume:
            existing_job = self._load_job_checkpoint(job_id)
            if existing_job and self._validate_job_checkpoint(existing_job, delta_table_name, postgres_table_name):
                self.logger.info(f"Retomando job existente - status: {existing_job['status']}")
                return self._resume_job_execution(existing_job)
            elif existing_job:
                self.logger.warning("Job existente incompatível - iniciando nova execução")
                self._cleanup_job_checkpoint(job_id)
        
        # Iniciar nova execução
        return self._start_new_job_execution(delta_table_name, postgres_table_name, key_columns, 
                                           compare_columns, chunk_size, mark_for_deletion, job_id)
    
    def _load_job_checkpoint(self, job_id: str) -> Optional[Dict]:
        """Carregar checkpoint do job da tabela PostgreSQL"""
        
        try:
            with self._get_postgres_connection() as conn:
                cursor = conn.cursor(cursor_factory=psycopg2.extras.RealDictCursor)
                
                cursor.execute(f"""
                    SELECT * FROM {self.control_table} 
                    WHERE job_id = %s
                """, (job_id,))
                
                job_data = cursor.fetchone()
                
                if job_data:
                    # Converter para dict e processar campos JSON
                    job_dict = dict(job_data)
                    if job_dict.get('key_columns'):
                        job_dict['key_columns'] = json.loads(job_dict['key_columns'])
                    if job_dict.get('compare_columns'):
                        job_dict['compare_columns'] = json.loads(job_dict['compare_columns'])
                    if job_dict.get('performance_metrics'):
                        job_dict['performance_metrics'] = job_dict['performance_metrics']
                    
                    return job_dict
                
                return None
                
        except Exception as e:
            self.logger.warning(f"Erro ao carregar checkpoint do job: {e}")
            return None
    
    def _validate_job_checkpoint(self, job_data: Dict, delta_table: str, postgres_table: str) -> bool:
        """Validar se checkpoint é compatível com execução atual"""
        
        try:
            # Verificar compatibilidade básica
            if (job_data.get('delta_table_name') != delta_table or 
                job_data.get('postgres_table_name') != postgres_table):
                return False
            
            # Verificar idade (máximo 7 dias para primeira execução)
            if job_data.get('start_time'):
                start_time = job_data['start_time']
                if isinstance(start_time, str):
                    start_time = datetime.fromisoformat(start_time.replace('Z', '+00:00'))
                
                age_hours = (datetime.now() - start_time.replace(tzinfo=None)).total_seconds() / 3600
                if age_hours > 168:  # 7 dias
                    self.logger.warning("Checkpoint muito antigo (>7 dias) - ignorando")
                    return False
            
            # Verificar se não foi completado
            if job_data.get('status') == 'COMPLETED':
                self.logger.info("Job já foi completado anteriormente")
                return False
            
            return True
            
        except Exception as e:
            self.logger.warning(f"Erro na validação do checkpoint: {e}")
            return False
    
    def _start_new_job_execution(self, delta_table_name: str, postgres_table_name: str,
                                key_columns: List[str], compare_columns: Optional[List[str]],
                                chunk_size: int, mark_for_deletion: bool, job_id: str) -> Dict[str, Any]:
        """Iniciar nova execução com checkpoint em PostgreSQL"""
        
        start_time = datetime.now()
        self.logger.info("Iniciando nova execução de sincronização")
        
        # Analisar dados do Delta Lake
        df_delta = self.spark.table(delta_table_name)
        total_records = df_delta.count()
        num_chunks = (total_records + chunk_size - 1) // chunk_size
        
        self.logger.info(f"Dados analisados: {total_records:,} registros em {num_chunks} chunks")
        
        # Criar registro do job na tabela de controle
        aux_table_name = f"{postgres_table_name}_sync_aux"
        
        with self._get_postgres_connection() as conn:
            cursor = conn.cursor()
            
            cursor.execute(f"""
                INSERT INTO {self.control_table} 
                (job_id, delta_table_name, postgres_table_name, key_columns, compare_columns,
                 chunk_size, mark_for_deletion, total_records, total_chunks, status, phase,
                 start_time, aux_table_name, performance_metrics)
                VALUES (%s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s)
            """, (
                job_id, delta_table_name, postgres_table_name,
                json.dumps(key_columns), json.dumps(compare_columns),
                chunk_size, mark_for_deletion, total_records, num_chunks,
                'RUNNING', 'COPY_MERGE', start_time, aux_table_name,
                json.dumps({
                    'chunks_processed': 0,
                    'total_copy_time': 0,
                    'total_merge_time': 0,
                    'avg_chunk_throughput': 0
                })
            ))
            
            conn.commit()
        
        # Preparar ambiente PostgreSQL
        self._prepare_postgres_environment(postgres_table_name, aux_table_name, key_columns)
        
        # Executar sincronização
        return self._execute_job_with_monitoring(df_delta, job_id)
    
    def _prepare_postgres_environment(self, main_table_name: str, aux_table_name: str, key_columns: List[str]):
        """Preparar ambiente PostgreSQL otimizado"""
        
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
    
    def _execute_job_with_monitoring(self, df_delta, job_id: str) -> Dict[str, Any]:
        """Executar sincronização com monitoramento via tabela PostgreSQL"""
        
        # Carregar dados do job
        job_data = self._load_job_checkpoint(job_id)
        if not job_data:
            raise Exception(f"Job {job_id} não encontrado na tabela de controle")
        
        # Preparar dados para processamento
        df_prepared = self._prepare_delta_data(df_delta, job_data)
        
        # Determinar chunks a processar
        completed_chunks = self._get_completed_chunks(job_id)
        chunks_to_process = [i for i in range(job_data['total_chunks']) 
                           if i not in completed_chunks]
        
        self.logger.info(f"Processando {len(chunks_to_process)} chunks restantes")
        
        # Processar chunks
        for chunk_id in chunks_to_process:
            try:
                self._process_chunk_with_db_tracking(df_prepared, chunk_id, job_data)
            except Exception as e:
                self.logger.error(f"Erro no chunk {chunk_id}: {e}")
                self._update_chunk_status(job_id, chunk_id, 'FAILED', error_message=str(e))
                self._update_job_status(job_id, 'FAILED', error_message=f"Falha no chunk {chunk_id}: {e}")
                raise
        
        # Finalizar sincronização
        return self._finalize_job_execution(job_id)
    
    def _get_completed_chunks(self, job_id: str) -> List[int]:
        """Obter lista de chunks já processados"""
        
        try:
            with self._get_postgres_connection() as conn:
                cursor = conn.cursor()
                
                cursor.execute(f"""
                    SELECT chunk_id FROM {self.chunk_control_table}
                    WHERE job_id = %s AND status = 'COMPLETED'
                    ORDER BY chunk_id
                """, (job_id,))
                
                return [row[0] for row in cursor.fetchall()]
                
        except Exception as e:
            self.logger.warning(f"Erro ao obter chunks completados: {e}")
            return []
    
    def _prepare_delta_data(self, df_delta, job_data: Dict):
        """Preparar dados do Delta Lake para processamento otimizado"""
        
        key_columns = job_data['key_columns']
        compare_columns = job_data['compare_columns']
        
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
        target_partitions = min(200, max(50, job_data['total_chunks'] // 4))
        df_prepared = df_prepared.coalesce(target_partitions)
        
        # Adicionar ID do chunk
        df_prepared = df_prepared.withColumn("chunk_id", 
                                           (monotonically_increasing_id() / job_data['chunk_size']).cast("int"))
        
        return df_prepared
    
    def _process_chunk_with_db_tracking(self, df_prepared, chunk_id: int, job_data: Dict):
        """Processar chunk individual com tracking na base de dados"""
        
        chunk_start_time = datetime.now()
        job_id = job_data['job_id']
        aux_table_name = job_data['aux_table_name']
        main_table_name = job_data['postgres_table_name']
        key_columns = job_data['key_columns']
        
        self.logger.info(f"Processando chunk {chunk_id + 1}/{job_data['total_chunks']}")
        
        # Registrar início do chunk
        self._update_chunk_status(job_id, chunk_id, 'RUNNING', start_time=chunk_start_time)
        
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
            self._update_chunk_status(job_id, chunk_id, 'COMPLETED', 
                                    end_time=datetime.now(), records_processed=0)
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
        
        # Calcular métricas
        chunk_end_time = datetime.now()
        total_chunk_time = (chunk_end_time - chunk_start_time).total_seconds()
        chunk_throughput = chunk_size / total_chunk_time if total_chunk_time > 0 else 0
        
        # Atualizar status do chunk
        self._update_chunk_status(
            job_id, chunk_id, 'COMPLETED',
            end_time=chunk_end_time,
            records_processed=chunk_size,
            copy_time_seconds=copy_time,
            merge_time_seconds=merge_time,
            throughput_per_second=chunk_throughput
        )
        
        # Atualizar métricas do job
        self._update_job_metrics(job_id, copy_time, merge_time)
        
        self.logger.info(f"Chunk {chunk_id + 1} concluído: {chunk_size:,} registros em {total_chunk_time:.1f}s "
                        f"(throughput: {chunk_throughput:,.0f} rec/s)")
    
    def _update_chunk_status(self, job_id: str, chunk_id: int, status: str, 
                           start_time: Optional[datetime] = None,
                           end_time: Optional[datetime] = None,
                           records_processed: Optional[int] = None,
                           copy_time_seconds: Optional[float] = None,
                           merge_time_seconds: Optional[float] = None,
                           throughput_per_second: Optional[float] = None,
                           error_message: Optional[str] = None):
        """Atualizar status do chunk na tabela de controle"""
        
        try:
            with self._get_postgres_connection() as conn:
                cursor = conn.cursor()
                
                # Verificar se registro já existe
                cursor.execute(f"""
                    SELECT 1 FROM {self.chunk_control_table}
                    WHERE job_id = %s AND chunk_id = %s
                """, (job_id, chunk_id))
                
                exists = cursor.fetchone() is not None
                
                if exists:
                    # Atualizar registro existente
                    update_fields = ["status = %s", "updated_at = NOW()"]
                    update_values = [status]
                    
                    if end_time:
                        update_fields.append("end_time = %s")
                        update_values.append(end_time)
                    if records_processed is not None:
                        update_fields.append("records_processed = %s")
                        update_values.append(records_processed)
                    if copy_time_seconds is not None:
                        update_fields.append("copy_time_seconds = %s")
                        update_values.append(copy_time_seconds)
                    if merge_time_seconds is not None:
                        update_fields.append("merge_time_seconds = %s")
                        update_values.append(merge_time_seconds)
                    if throughput_per_second is not None:
                        update_fields.append("throughput_per_second = %s")
                        update_values.append(throughput_per_second)
                    if error_message:
                        update_fields.append("error_message = %s")
                        update_values.append(error_message)
                    
                    update_values.extend([job_id, chunk_id])
                    
                    cursor.execute(f"""
                        UPDATE {self.chunk_control_table}
                        SET {', '.join(update_fields)}
                        WHERE job_id = %s AND chunk_id = %s
                    """, update_values)
                    
                else:
                    # Inserir novo registro
                    cursor.execute(f"""
                        INSERT INTO {self.chunk_control_table}
                        (job_id, chunk_id, status, start_time, end_time, records_processed,
                         copy_time_seconds, merge_time_seconds, throughput_per_second, error_message)
                        VALUES (%s, %s, %s, %s, %s, %s, %s, %s, %s, %s)
                    """, (job_id, chunk_id, status, start_time, end_time, records_processed,
                          copy_time_seconds, merge_time_seconds, throughput_per_second, error_message))
                
                conn.commit()
                
        except Exception as e:
            self.logger.warning(f"Erro ao atualizar status do chunk: {e}")
    
    def _update_job_status(self, job_id: str, status: str, error_message: Optional[str] = None,
                          end_time: Optional[datetime] = None):
        """Atualizar status do job na tabela de controle"""
        
        try:
            with self._get_postgres_connection() as conn:
                cursor = conn.cursor()
                
                update_fields = ["status = %s", "last_update = NOW()"]
                update_values = [status]
                
                if error_message:
                    update_fields.append("error_message = %s")
                    update_values.append(error_message)
                
                if end_time:
                    update_fields.append("end_time = %s")
                    update_values.append(end_time)
                
                update_values.append(job_id)
                
                cursor.execute(f"""
                    UPDATE {self.control_table}
                    SET {', '.join(update_fields)}
                    WHERE job_id = %s
                """, update_values)
                
                conn.commit()
                
        except Exception as e:
            self.logger.warning(f"Erro ao atualizar status do job: {e}")
    
    def _update_job_metrics(self, job_id: str, copy_time: float, merge_time: float):
        """Atualizar métricas de performance do job"""
        
        try:
            with self._get_postgres_connection() as conn:
                cursor = conn.cursor()
                
                # Obter métricas atuais
                cursor.execute(f"""
                    SELECT performance_metrics FROM {self.control_table}
                    WHERE job_id = %s
                """, (job_id,))
                
                result = cursor.fetchone()
                if result and result[0]:
                    metrics = result[0]
                else:
                    metrics = {
                        'chunks_processed': 0,
                        'total_copy_time': 0,
                        'total_merge_time': 0,
                        'avg_chunk_throughput': 0
                    }
                
                # Atualizar métricas
                metrics['chunks_processed'] += 1
                metrics['total_copy_time'] += copy_time
                metrics['total_merge_time'] += merge_time
                
                # Calcular throughput médio
                if metrics['chunks_processed'] > 0:
                    total_time = metrics['total_copy_time'] + metrics['total_merge_time']
                    if total_time > 0:
                        # Estimar registros processados (assumindo chunk_size médio)
                        cursor.execute(f"""
                            SELECT chunk_size FROM {self.control_table}
                            WHERE job_id = %s
                        """, (job_id,))
                        chunk_size = cursor.fetchone()[0]
                        total_records = metrics['chunks_processed'] * chunk_size
                        metrics['avg_chunk_throughput'] = total_records / total_time
                
                # Salvar métricas atualizadas
                cursor.execute(f"""
                    UPDATE {self.control_table}
                    SET performance_metrics = %s, last_update = NOW()
                    WHERE job_id = %s
                """, (json.dumps(metrics), job_id))
                
                conn.commit()
                
        except Exception as e:
            self.logger.warning(f"Erro ao atualizar métricas do job: {e}")
    
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
    
    def _finalize_job_execution(self, job_id: str) -> Dict[str, Any]:
        """Finalizar execução do job com limpeza e estatísticas"""
        
        self.logger.info("Finalizando sincronização")
        
        # Carregar dados do job
        job_data = self._load_job_checkpoint(job_id)
        if not job_data:
            raise Exception(f"Job {job_id} não encontrado")
        
        # Executar soft delete se solicitado
        deleted_records = 0
        if job_data['mark_for_deletion']:
            self._update_job_status(job_id, 'RUNNING', end_time=None)
            deleted_records = self._execute_soft_delete(job_data)
        
        # Limpar tabela auxiliar
        self._cleanup_auxiliary_table(job_data['aux_table_name'])
        
        # Calcular estatísticas finais
        end_time = datetime.now()
        start_time = job_data['start_time']
        if isinstance(start_time, str):
            start_time = datetime.fromisoformat(start_time.replace('Z', '+00:00')).replace(tzinfo=None)
        
        total_time = (end_time - start_time).total_seconds()
        
        # Obter estatísticas dos chunks
        chunk_stats = self._get_job_chunk_statistics(job_id)
        
        result = {
            'success': True,
            'job_id': job_id,
            'total_records_processed': job_data['total_records'],
            'deleted_records_marked': deleted_records,
            'execution_time_seconds': total_time,
            'execution_time_minutes': total_time / 60,
            'throughput_per_second': job_data['total_records'] / total_time if total_time > 0 else 0,
            'chunks_processed': chunk_stats['completed_chunks'],
            'chunks_failed': chunk_stats['failed_chunks'],
            'avg_copy_time_per_chunk': chunk_stats['avg_copy_time'],
            'avg_merge_time_per_chunk': chunk_stats['avg_merge_time'],
            'avg_chunk_throughput': chunk_stats['avg_throughput']
        }
        
        # Finalizar job na tabela de controle
        self._update_job_status(job_id, 'COMPLETED', end_time=end_time)
        
        self.logger.info(f"Sincronização concluída: {job_data['total_records']:,} registros em {total_time/60:.1f} minutos")
        self.logger.info(f"Throughput médio: {result['throughput_per_second']:,.0f} registros/segundo")
        
        return result
    
    def _get_job_chunk_statistics(self, job_id: str) -> Dict[str, Any]:
        """Obter estatísticas dos chunks do job"""
        
        try:
            with self._get_postgres_connection() as conn:
                cursor = conn.cursor()
                
                cursor.execute(f"""
                    SELECT 
                        COUNT(*) FILTER (WHERE status = 'COMPLETED') as completed_chunks,
                        COUNT(*) FILTER (WHERE status = 'FAILED') as failed_chunks,
                        AVG(copy_time_seconds) as avg_copy_time,
                        AVG(merge_time_seconds) as avg_merge_time,
                        AVG(throughput_per_second) as avg_throughput
                    FROM {self.chunk_control_table}
                    WHERE job_id = %s
                """, (job_id,))
                
                result = cursor.fetchone()
                
                return {
                    'completed_chunks': result[0] or 0,
                    'failed_chunks': result[1] or 0,
                    'avg_copy_time': float(result[2]) if result[2] else 0,
                    'avg_merge_time': float(result[3]) if result[3] else 0,
                    'avg_throughput': float(result[4]) if result[4] else 0
                }
                
        except Exception as e:
            self.logger.warning(f"Erro ao obter estatísticas dos chunks: {e}")
            return {
                'completed_chunks': 0,
                'failed_chunks': 0,
                'avg_copy_time': 0,
                'avg_merge_time': 0,
                'avg_throughput': 0
            }
    
    def _execute_soft_delete(self, job_data: Dict) -> int:
        """Executar soft delete de registros órfãos"""
        
        self.logger.info("Executando soft delete de registros órfãos")
        
        aux_table_name = job_data['aux_table_name']
        main_table_name = job_data['postgres_table_name']
        key_columns = job_data['key_columns']
        
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
    
    def _resume_job_execution(self, job_data: Dict) -> Dict[str, Any]:
        """Retomar execução do job do checkpoint PostgreSQL"""
        
        self.logger.info("Retomando execução do checkpoint PostgreSQL")
        
        # Recarregar dados do Delta Lake
        df_delta = self.spark.table(job_data['delta_table_name'])
        
        # Verificar se tabela auxiliar ainda existe
        aux_table_name = job_data['aux_table_name']
        if not self._check_aux_table_exists(aux_table_name):
            self.logger.warning("Tabela auxiliar não encontrada - recriando")
            self._prepare_postgres_environment(
                job_data['postgres_table_name'], 
                aux_table_name, 
                job_data['key_columns']
            )
        
        # Atualizar status para resuming
        self._update_job_status(job_data['job_id'], 'RESUMING')
        
        # Continuar execução
        return self._execute_job_with_monitoring(df_delta, job_data['job_id'])
    
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
    
    def _cleanup_job_checkpoint(self, job_id: str):
        """Limpar checkpoint do job (marcar como cancelado)"""
        try:
            self._update_job_status(job_id, 'CANCELLED', 
                                  error_message="Job cancelado para nova execução")
        except Exception as e:
            self.logger.warning(f"Erro ao limpar checkpoint do job: {e}")
    
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
    
    def list_jobs(self, limit: int = 10) -> List[Dict]:
        """Listar jobs de sincronização"""
        try:
            with self._get_postgres_connection() as conn:
                cursor = conn.cursor(cursor_factory=psycopg2.extras.RealDictCursor)
                
                cursor.execute(f"""
                    SELECT job_id, delta_table_name, postgres_table_name, status, 
                           start_time, end_time, total_records, total_chunks
                    FROM {self.control_table}
                    ORDER BY start_time DESC
                    LIMIT %s
                """, (limit,))
                
                return [dict(row) for row in cursor.fetchall()]
        except Exception as e:
            self.logger.warning(f"Erro ao listar jobs: {e}")
            return []
    
    def get_job_progress(self, job_id: str) -> Dict[str, Any]:
        """Obter progresso detalhado do job"""
        try:
            with self._get_postgres_connection() as conn:
                cursor = conn.cursor(cursor_factory=psycopg2.extras.RealDictCursor)
                
                # Dados do job
                cursor.execute(f"""
                    SELECT * FROM {self.control_table}
                    WHERE job_id = %s
                """, (job_id,))
                
                job_data = cursor.fetchone()
                if not job_data:
                    return {}
                
                # Estatísticas dos chunks
                cursor.execute(f"""
                    SELECT 
                        COUNT(*) as total_chunks,
                        COUNT(*) FILTER (WHERE status = 'COMPLETED') as completed_chunks,
                        COUNT(*) FILTER (WHERE status = 'RUNNING') as running_chunks,
                        COUNT(*) FILTER (WHERE status = 'FAILED') as failed_chunks,
                        AVG(throughput_per_second) FILTER (WHERE status = 'COMPLETED') as avg_throughput
                    FROM {self.chunk_control_table}
                    WHERE job_id = %s
                """, (job_id,))
                
                chunk_stats = cursor.fetchone()
                
                progress_pct = 0
                if chunk_stats['total_chunks'] > 0:
                    progress_pct = (chunk_stats['completed_chunks'] / chunk_stats['total_chunks']) * 100
                
                return {
                    'job_id': job_data['job_id'],
                    'status': job_data['status'],
                    'progress_percentage': progress_pct,
                    'completed_chunks': chunk_stats['completed_chunks'],
                    'total_chunks': chunk_stats['total_chunks'],
                    'running_chunks': chunk_stats['running_chunks'],
                    'failed_chunks': chunk_stats['failed_chunks'],
                    'avg_throughput': float(chunk_stats['avg_throughput']) if chunk_stats['avg_throughput'] else 0,
                    'start_time': job_data['start_time'],
                    'last_update': job_data['last_update']
                }
                
        except Exception as e:
            self.logger.warning(f"Erro ao obter progresso do job: {e}")
            return {}

