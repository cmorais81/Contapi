"""
Classe DadosCadastrais Otimizada para Databricks Runtime 15.4
Corrigida para problemas de broadcast e AQE do Runtime 15.4
"""

import time
import logging
from pyspark.sql import SparkSession
from pyspark.sql.functions import (
    col, when, otherwise, trim, substring, concat, lit, 
    coalesce, regexp_replace, broadcast, hash as spark_hash,
    current_timestamp, date_format, collect_list, collect_set,
    first, count as spark_count, sum as spark_sum
)
from pyspark import StorageLevel
from functools import wraps


def runtime_15_4_compatible(func):
    """Decorator para compatibilidade com Runtime 15.4"""
    @wraps(func)
    def wrapper(self, *args, **kwargs):
        # Configurar ambiente para Runtime 15.4
        self._configure_runtime_15_4()
        return func(self, *args, **kwargs)
    return wrapper


class DadosCadastraisRuntime154:
    """Classe otimizada para Databricks Runtime 15.4"""
    
    def __init__(self, spark, logger, storage_level="MEMORY_AND_DISK_SER"):
        self.spark = spark
        self.logger = logger
        self.storage_level = getattr(StorageLevel, storage_level)
        
        # Configurações específicas do Runtime 15.4
        self._configure_runtime_15_4()
        
        # Métricas de performance
        self.performance_metrics = {}
        
        # Configurações de broadcast adaptativas
        self.broadcast_config = self._get_broadcast_config()
        
        # Cache de lookup tables
        self._lookup_cache = {}
    
    def _configure_runtime_15_4(self):
        """Configura Spark especificamente para Runtime 15.4"""
        
        # Configurações de broadcast otimizadas para 15.4
        self.spark.conf.set("spark.sql.autoBroadcastJoinThreshold", "1GB")
        self.spark.conf.set("spark.sql.broadcastTimeout", "1200")
        self.spark.conf.set("spark.driver.maxResultSize", "8g")
        
        # Configurações AQE específicas para 15.4
        self.spark.conf.set("spark.sql.adaptive.enabled", "true")
        self.spark.conf.set("spark.sql.adaptive.forceOptimizeSkewedJoin", "false")
        self.spark.conf.set("spark.sql.adaptive.coalescePartitions.enabled", "true")
        self.spark.conf.set("spark.sql.adaptive.coalescePartitions.parallelismFirst", "false")
        self.spark.conf.set("spark.sql.adaptive.skewJoin.enabled", "true")
        self.spark.conf.set("spark.sql.adaptive.skewJoin.skewedPartitionFactor", "5")
        self.spark.conf.set("spark.sql.adaptive.skewJoin.skewedPartitionThresholdInBytes", "1GB")
        self.spark.conf.set("spark.sql.adaptive.localShuffleReader.enabled", "true")
        self.spark.conf.set("spark.sql.adaptive.maxShuffledHashJoinLocalMapThreshold", "1GB")
        self.spark.conf.set("spark.sql.adaptive.advisoryPartitionSizeInBytes", "512MB")
        
        # Configurações de memória para broadcast
        self.spark.conf.set("spark.executor.memoryFraction", "0.75")
        self.spark.conf.set("spark.executor.memoryStorageFraction", "0.3")
        self.spark.conf.set("spark.sql.execution.arrow.maxRecordsPerBatch", "25000")
        
        # Configurações de rede
        self.spark.conf.set("spark.network.timeout", "1200s")
        self.spark.conf.set("spark.rpc.askTimeout", "1200s")
        self.spark.conf.set("spark.rpc.lookupTimeout", "1200s")
        
        # Configurações de serialização
        self.spark.conf.set("spark.serializer", "org.apache.spark.serializer.KryoSerializer")
        self.spark.conf.set("spark.kryo.unsafe", "true")
        self.spark.conf.set("spark.kryoserializer.buffer.max", "2048m")
        
        self.logger.info("Configurações Runtime 15.4 aplicadas com sucesso")
    
    def _get_broadcast_config(self):
        """Retorna configurações de broadcast baseadas no cluster"""
        
        try:
            # Obter informações do cluster
            sc = self.spark.sparkContext
            total_cores = sc.defaultParallelism
            executor_memory = self.spark.conf.get("spark.executor.memory", "4g")
            
            # Calcular limites baseados nos recursos
            if "g" in executor_memory.lower():
                memory_gb = int(executor_memory.lower().replace("g", ""))
            else:
                memory_gb = 4  # Padrão
            
            # Configurações adaptativas
            if memory_gb >= 50 and total_cores >= 64:
                # Cluster grande
                return {
                    "max_broadcast_size_gb": 2.0,
                    "auto_broadcast_threshold": "1GB",
                    "broadcast_timeout": 1200,
                    "use_aggressive_broadcast": True
                }
            elif memory_gb >= 25 and total_cores >= 32:
                # Cluster médio
                return {
                    "max_broadcast_size_gb": 1.0,
                    "auto_broadcast_threshold": "500MB",
                    "broadcast_timeout": 900,
                    "use_aggressive_broadcast": True
                }
            else:
                # Cluster pequeno
                return {
                    "max_broadcast_size_gb": 0.5,
                    "auto_broadcast_threshold": "200MB",
                    "broadcast_timeout": 600,
                    "use_aggressive_broadcast": False
                }
                
        except Exception as e:
            self.logger.warning(f"Erro ao detectar configuração do cluster: {e}")
            # Configuração padrão conservadora
            return {
                "max_broadcast_size_gb": 0.5,
                "auto_broadcast_threshold": "200MB",
                "broadcast_timeout": 600,
                "use_aggressive_broadcast": False
            }
    
    def safe_broadcast_15_4(self, df, max_size_gb=None):
        """Broadcast seguro para Runtime 15.4"""
        
        if max_size_gb is None:
            max_size_gb = self.broadcast_config["max_broadcast_size_gb"]
        
        try:
            # Cache e materializar para estimativa precisa
            df_cached = df.cache()
            count = df_cached.count()
            
            # Estimar tamanho baseado em contagem (conservador)
            estimated_size_gb = (count * 1500) / (1024 * 1024 * 1024)  # 1.5KB por registro
            
            self.logger.info(f"Estimativa de tamanho para broadcast: {estimated_size_gb:.3f}GB (limite: {max_size_gb}GB)")
            
            if estimated_size_gb <= max_size_gb:
                # Configurar timeout temporariamente
                original_timeout = self.spark.conf.get("spark.sql.broadcastTimeout")
                self.spark.conf.set("spark.sql.broadcastTimeout", str(self.broadcast_config["broadcast_timeout"]))
                
                try:
                    df_broadcast = broadcast(df_cached)
                    self.logger.info(f"Broadcast aplicado com sucesso para DataFrame de {count:,} registros")
                    return df_broadcast
                finally:
                    # Restaurar timeout original
                    self.spark.conf.set("spark.sql.broadcastTimeout", original_timeout)
            else:
                self.logger.warning(f"DataFrame muito grande para broadcast: {estimated_size_gb:.3f}GB > {max_size_gb}GB")
                return df_cached
                
        except Exception as e:
            self.logger.warning(f"Erro no broadcast, usando DataFrame normal: {e}")
            return df.cache() if not df.is_cached else df
    
    def create_lookup_table_15_4(self, lookup_data, name):
        """Cria tabela de lookup otimizada para Runtime 15.4"""
        
        if name in self._lookup_cache:
            self.logger.info(f"Usando lookup table {name} do cache")
            return self._lookup_cache[name]
        
        # Criar DataFrame de lookup
        lookup_df = self.spark.createDataFrame(lookup_data)
        
        # Aplicar broadcast se apropriado
        lookup_df_broadcast = self.safe_broadcast_15_4(lookup_df, max_size_gb=0.1)  # Limite baixo para lookups
        
        # Cache na memória
        self._lookup_cache[name] = lookup_df_broadcast
        
        self.logger.info(f"Lookup table {name} criada e cached com {len(lookup_data)} registros")
        
        return lookup_df_broadcast
    
    def adaptive_join_15_4(self, df_large, df_small, join_key, join_type="inner"):
        """Join adaptativo otimizado para Runtime 15.4"""
        
        try:
            # Verificar tamanhos
            count_large = df_large.count()
            count_small = df_small.count()
            
            self.logger.info(f"Join adaptativo: {count_large:,} x {count_small:,} registros")
            
            # Decidir estratégia baseada no tamanho
            if count_small < 100000:  # < 100K registros - sempre broadcast
                df_small_broadcast = self.safe_broadcast_15_4(df_small, max_size_gb=0.2)
                result = df_large.join(df_small_broadcast, join_key, join_type)
                self.logger.info("Usando broadcast join (pequeno)")
                
            elif count_small < 1000000 and count_small < count_large * 0.1:  # < 1M e < 10% do maior
                # Tentar broadcast com verificação
                df_small_broadcast = self.safe_broadcast_15_4(df_small)
                result = df_large.join(df_small_broadcast, join_key, join_type)
                self.logger.info("Usando broadcast join (médio)")
                
            else:
                # Usar sort-merge otimizado
                result = self.optimized_sort_merge_join_15_4(df_large, df_small, join_key, join_type)
                self.logger.info("Usando sort-merge join otimizado")
            
            return result
            
        except Exception as e:
            self.logger.error(f"Erro no join adaptativo: {e}")
            # Fallback para join simples
            return df_large.join(df_small, join_key, join_type)
    
    def optimized_sort_merge_join_15_4(self, df1, df2, join_key, join_type="inner"):
        """Sort-merge join otimizado para Runtime 15.4"""
        
        # Calcular número otimizado de partições
        total_count = df1.count() + df2.count()
        num_partitions = max(200, min(2000, total_count // 1000000))
        
        self.logger.info(f"Reparticionando para {num_partitions} partições para sort-merge join")
        
        # Reparticionar ambos DataFrames pela chave de join
        df1_partitioned = df1.repartition(num_partitions, join_key)
        df2_partitioned = df2.repartition(num_partitions, join_key)
        
        return df1_partitioned.join(df2_partitioned, join_key, join_type)
    
    @runtime_15_4_compatible
    def coletapedt001_runtime_15_4(self):
        """Versão otimizada do coletapedt001 para Runtime 15.4"""
        
        start_time = time.time()
        self.logger.info("Iniciando coletapedt001 otimizado para Runtime 15.4")
        
        try:
            # Carregar dados de referência
            df_data_ref = self.spark.read.table("b_stbr_pe.pedt001")
            
            # Carregar dados principais com filtro otimizado
            df_pedt001 = self.spark.read.table("b_stbr_pe.pedt001").select(
                "penompen", "penudoc", "petipdoc", "penumper", "pepriape", 
                "pesecnac", "pesexper", "petipocu", "peusualt", "pesegape", "pettipper"
            ).filter(col("dat_ref_carga") == df_data_ref).distinct()
            
            # Cache estratégico
            df_pedt001_cached = df_pedt001.persist(self.storage_level)
            df_pedt001_cached.count()  # Materializar
            
            # Criar lookup tables otimizadas
            estados_lookup = self.create_lookup_table_15_4([
                ("01", "AC"), ("02", "AL"), ("03", "AP"), ("04", "AM"), ("05", "BA"),
                ("06", "CE"), ("07", "ES"), ("08", "GO"), ("09", "MA"), ("10", "MT"),
                ("11", "MS"), ("12", "MG"), ("13", "PA"), ("14", "PB"), ("15", "PR"),
                ("16", "PE"), ("17", "PI"), ("18", "RJ"), ("19", "RN"), ("20", "RS"),
                ("21", "RO"), ("22", "RR"), ("23", "SC"), ("24", "SP"), ("25", "SE"),
                ("26", "TO"), ("27", "DF"), ("99", "ZZ")
            ], "estados_lookup")
            
            # Transformações consolidadas usando SQL nativo para melhor performance no 15.4
            df_result = df_pedt001_cached.createOrReplaceTempView("pedt001_temp")
            
            # Query SQL otimizada para Runtime 15.4
            sql_query = """
            SELECT 
                penumper,
                CASE 
                    WHEN pesestciv = 'A' THEN 'CASADO(A) S/ INFORMACAO DE REGIME'
                    WHEN pesestciv = 'B' THEN 'CASADO(A)-PARTICIP FINAL DOS AQUESTOS'
                    WHEN pesestciv = 'C' THEN 'SOLTEIRO(A)'
                    WHEN pesestciv = 'D' THEN 'VIUVO(A)'
                    WHEN pesestciv = 'E' THEN 'DIVORCIADO/A'
                    WHEN pesestciv = 'F' THEN 'SEPARADO/A JUDICIALMENTE'
                    WHEN pesestciv = 'G' THEN 'UNIAO ESTAVEL'
                    WHEN pesestciv = 'H' THEN 'CASADO(A)-COMUNHAO PARCIAL BENS'
                    WHEN pesestciv = 'I' THEN 'CASADO(A)-COMUNHAO UNIVERSAL BENS'
                    ELSE ''
                END as pesestciv,
                CASE 
                    WHEN pesexper = 'M' THEN 'masculino'
                    WHEN pesexper = 'F' THEN 'feminino'
                    ELSE ''
                END as pesexper,
                CASE 
                    WHEN petipocu = '01' THEN 'MAIOR C/RENDA'
                    WHEN petipocu = '02' THEN 'MENOR RELATIV.INCAPAZ'
                    WHEN petipocu = '03' THEN 'MENOR ABSOLUT.INCAPAZ'
                    WHEN petipocu = '04' THEN 'INTERDITO'
                    WHEN petipocu = '05' THEN 'ANALFABETO'
                    WHEN petipocu = '06' THEN 'DEF VISUAL/AUDI - MAIOR CON RENDA'
                    WHEN petipocu = '07' THEN 'ESPÓLIO'
                    WHEN petipocu = '08' THEN 'MENOR APRENDIZ'
                    WHEN petipocu = '09' THEN 'MAIOR SEM RENDA'
                    WHEN petipocu = '10' THEN 'MENOR EMANCIP.S/RENDA'
                    WHEN petipocu = '11' THEN 'DEF VISUAL/AUDI-MENOR EMANCIP C/RENDA'
                    WHEN petipocu = '12' THEN 'DEF VISUAL/AUDI-MENOR EMANCIP S/RENDA'
                    WHEN petipocu = '13' THEN 'DEF VISUAL/AUDI-MENOR RELATIV INCAPAZ'
                    WHEN petipocu = '14' THEN 'DEF VISUAL/AUDI-MENOR ABSOLUT INCAPAZ'
                    WHEN petipocu = '15' THEN 'PESSOA FALECIDA'
                    ELSE ''
                END as petipocu,
                CASE 
                    WHEN penacper = 'BRA' THEN 'BRASILEIRA'
                    WHEN penacper = 'EXT' THEN 'ESTRANGEIRA'
                    WHEN penacper = 'NAT' THEN 'NATURALIZADA'
                    ELSE ''
                END as penacper,
                (datediff(current_date(), to_date(pefecnac, 'yyyyMMdd')) / 365.25) as idade,
                concat(trim(penompen), ' ', trim(pepriape), ' ', trim(pesegape)) as nm_comp,
                concat(trim(penompen), ' ', trim(pepriape), ' ', trim(pesegape)) as nome,
                concat(trim(penompen), ' ', trim(pepriape), ' ', trim(pesegape)) as sobrenome
            FROM pedt001_temp
            """
            
            df_transformed = self.spark.sql(sql_query)
            
            # Join com lookup de estados usando join adaptativo
            df_with_states = self.adaptive_join_15_4(
                df_transformed, 
                estados_lookup.withColumnRenamed("_1", "pesestper").withColumnRenamed("_2", "estado_desc"),
                "pesestper",
                "left"
            )
            
            # Adicionar coluna de sobrenome final
            df_final = df_with_states.withColumn(
                "sobrenome_final",
                when(
                    (col("sobrenome") != "") & (col("sobrenome").isNotNull()),
                    col("sobrenome")
                ).otherwise(None)
            )
            
            # Cache final
            df_result_cached = df_final.persist(self.storage_level)
            
            # Métricas de performance
            duration = time.time() - start_time
            count = df_result_cached.count()
            
            self.performance_metrics['coletapedt001_runtime_15_4'] = {
                'duration_seconds': duration,
                'record_count': count,
                'throughput_records_per_second': count / duration if duration > 0 else 0
            }
            
            self.logger.info(f"coletapedt001 Runtime 15.4 concluído: {count:,} registros em {duration:.2f}s")
            
            return df_result_cached
            
        except Exception as e:
            self.logger.error(f"Erro em coletapedt001 Runtime 15.4: {e}")
            raise
    
    @runtime_15_4_compatible
    def coletapedt205_runtime_15_4(self):
        """Versão otimizada do coletapedt205 para Runtime 15.4"""
        
        start_time = time.time()
        self.logger.info("Iniciando coletapedt205 otimizado para Runtime 15.4")
        
        try:
            # Carregar dados de referência
            df_data_ref = self.spark.read.table("b_stbr_pe.pedt205")
            
            # Carregar e transformar dados em uma única operação SQL
            df_pedt205 = self.spark.read.table("b_stbr_pe.pedt205").select(
                "cd_pess", "tp_bem"
            ).filter(col("dat_ref_carga") == df_data_ref).distinct()
            
            # Cache estratégico
            df_pedt205_cached = df_pedt205.persist(self.storage_level)
            df_pedt205_cached.count()  # Materializar
            
            # Criar view temporária para SQL otimizado
            df_pedt205_cached.createOrReplaceTempView("pedt205_temp")
            
            # Transformação usando SQL nativo (mais eficiente no Runtime 15.4)
            sql_transform = """
            SELECT 
                cd_pess as penumper,
                CASE 
                    WHEN tp_bem = '01' THEN 'ACOES'
                    WHEN tp_bem = '02' THEN 'AUTOMOVEIS'
                    WHEN tp_bem = '03' THEN 'IMOVEIS'
                    WHEN tp_bem = '04' THEN 'INVESTIMENTOS'
                    WHEN tp_bem = '05' THEN 'NAO POSSUI'
                    WHEN tp_bem = '06' THEN 'OUTROS'
                    WHEN tp_bem = '07' THEN 'NAO INFORMADO'
                    WHEN tp_bem = '08' THEN 'PATRIMONIO LIQUIDO'
                    ELSE ''
                END as tp_bem_desc
            FROM pedt205_temp
            """
            
            df_transformed = self.spark.sql(sql_transform)
            
            # Agrupamento otimizado usando collect_set para eliminar duplicatas automaticamente
            df_grouped = df_transformed.groupBy("penumper").agg(
                collect_set("tp_bem_desc").alias("tp_bem_list")
            )
            
            # Cache do resultado
            df_result = df_grouped.persist(self.storage_level)
            
            # Métricas de performance
            duration = time.time() - start_time
            count = df_result.count()
            
            self.performance_metrics['coletapedt205_runtime_15_4'] = {
                'duration_seconds': duration,
                'record_count': count,
                'throughput_records_per_second': count / duration if duration > 0 else 0
            }
            
            self.logger.info(f"coletapedt205 Runtime 15.4 concluído: {count:,} registros em {duration:.2f}s")
            
            return df_result
            
        except Exception as e:
            self.logger.error(f"Erro em coletapedt205 Runtime 15.4: {e}")
            raise
    
    @runtime_15_4_compatible
    def coletapedt002_runtime_15_4(self):
        """Versão otimizada do coletapedt002 para Runtime 15.4"""
        
        start_time = time.time()
        self.logger.info("Iniciando coletapedt002 otimizado para Runtime 15.4")
        
        try:
            # Carregar dados de referência
            df_data_ref = self.spark.read.table("b_stbr_pe.pedt002")
            
            # Carregar dados principais
            df_pedt002 = self.spark.read.table("b_stbr_pe.pedt002").select(
                "penumper", "penumest", "pesestrat", "penommad", "penompad"
            ).filter(col("dat_ref_carga") == df_data_ref).distinct()
            
            # Cache estratégico
            df_pedt002_cached = df_pedt002.persist(self.storage_level)
            df_pedt002_cached.count()  # Materializar
            
            # Criar lookup table para estados (mais eficiente que 28 when/otherwise)
            estados_data = [
                ("01", "AC - ACRE"), ("02", "AL - ALAGOAS"), ("03", "AP - AMAPA"),
                ("04", "AM - AMAZONAS"), ("05", "BA - BAHIA"), ("06", "CE - CEARA"),
                ("07", "ES - ESPIRITO SANTO"), ("08", "GO - GOIAS"), ("09", "MA - MARANHAO"),
                ("10", "MT - MATO GROSSO"), ("11", "MS - MATO GROSSO DO SUL"),
                ("12", "MG - MINAS GERAIS"), ("13", "PA - PARA"), ("14", "PB - PARAIBA"),
                ("15", "PR - PARANA"), ("16", "PE - PERNAMBUCO"), ("17", "PI - PIAUI"),
                ("18", "RJ - RIO DE JANEIRO"), ("19", "RN - RIO GRANDE DO NORTE"),
                ("20", "RS - RIO GRANDE DO SUL"), ("21", "RO - RONDONIA"),
                ("22", "RR - RORAIMA"), ("23", "SC - SANTA CATARINA"),
                ("24", "SP - SAO PAULO"), ("25", "SE - SERGIPE"), ("26", "TO - TOCANTINS"),
                ("27", "DF - DISTRITO FEDERAL"), ("99", "ZZ - NAO INFORMADA")
            ]
            
            # Criar lookup table com broadcast otimizado
            estados_lookup = self.create_lookup_table_15_4(estados_data, "estados_pedt002")
            
            # Join adaptativo com lookup de estados
            df_with_states = self.adaptive_join_15_4(
                df_pedt002_cached,
                estados_lookup.withColumnRenamed("_1", "pesestrat").withColumnRenamed("_2", "estado_desc"),
                "pesestrat",
                "left"
            )
            
            # Cache do resultado
            df_result = df_with_states.persist(self.storage_level)
            
            # Métricas de performance
            duration = time.time() - start_time
            count = df_result.count()
            
            self.performance_metrics['coletapedt002_runtime_15_4'] = {
                'duration_seconds': duration,
                'record_count': count,
                'throughput_records_per_second': count / duration if duration > 0 else 0
            }
            
            self.logger.info(f"coletapedt002 Runtime 15.4 concluído: {count:,} registros em {duration:.2f}s")
            
            return df_result
            
        except Exception as e:
            self.logger.error(f"Erro em coletapedt002 Runtime 15.4: {e}")
            raise
    
    def execute_optimized_pipeline_runtime_15_4(self):
        """Pipeline completo otimizado para Runtime 15.4"""
        
        total_start_time = time.time()
        self.logger.info("=== INICIANDO PIPELINE OTIMIZADO RUNTIME 15.4 ===")
        
        try:
            # Executar todos os métodos
            df_pedt001 = self.coletapedt001_runtime_15_4()
            df_pedt205 = self.coletapedt205_runtime_15_4()
            df_pedt002 = self.coletapedt002_runtime_15_4()
            
            # Join final usando estratégia adaptativa
            self.logger.info("Executando joins finais...")
            
            # Join 1: pedt001 + pedt205
            df_joined_1 = self.adaptive_join_15_4(df_pedt001, df_pedt205, "penumper", "left")
            
            # Join 2: resultado + pedt002
            df_final = self.adaptive_join_15_4(df_joined_1, df_pedt002, "penumper", "left")
            
            # Cache final
            df_result = df_final.persist(self.storage_level)
            
            # Métricas finais
            total_duration = time.time() - total_start_time
            final_count = df_result.count()
            
            self.performance_metrics['pipeline_total_runtime_15_4'] = {
                'duration_seconds': total_duration,
                'record_count': final_count,
                'throughput_records_per_second': final_count / total_duration if total_duration > 0 else 0
            }
            
            self.logger.info(f"=== PIPELINE RUNTIME 15.4 CONCLUÍDO EM {total_duration:.2f}s ===")
            self.logger.info(f"Total de registros processados: {final_count:,}")
            
            # Log das métricas de performance
            self.log_performance_metrics()
            
            return df_result
            
        except Exception as e:
            self.logger.error(f"Erro no pipeline Runtime 15.4: {e}")
            raise
        finally:
            # Limpar cache de lookup tables
            self.cleanup_lookup_cache()
    
    def log_performance_metrics(self):
        """Log detalhado das métricas de performance"""
        self.logger.info("=== MÉTRICAS DE PERFORMANCE RUNTIME 15.4 ===")
        
        for operation, metrics in self.performance_metrics.items():
            self.logger.info(f"{operation.upper()}:")
            for metric, value in metrics.items():
                if isinstance(value, float):
                    self.logger.info(f"  {metric}: {value:.2f}")
                else:
                    self.logger.info(f"  {metric}: {value:,}")
    
    def cleanup_lookup_cache(self):
        """Limpa cache de lookup tables"""
        for name, df in self._lookup_cache.items():
            try:
                df.unpersist()
                self.logger.info(f"Cache da lookup table {name} limpo")
            except:
                pass
        self._lookup_cache.clear()
    
    def get_performance_metrics(self):
        """Retorna métricas de performance para análise externa"""
        return self.performance_metrics.copy()
    
    def diagnose_broadcast_issues(self):
        """Diagnóstica problemas de broadcast no Runtime 15.4"""
        
        self.logger.info("=== DIAGNÓSTICO DE BROADCAST RUNTIME 15.4 ===")
        
        # Verificar configurações atuais
        config_checks = {
            'broadcast_threshold': self.spark.conf.get("spark.sql.autoBroadcastJoinThreshold"),
            'broadcast_timeout': self.spark.conf.get("spark.sql.broadcastTimeout"),
            'driver_memory': self.spark.conf.get("spark.driver.maxResultSize"),
            'aqe_enabled': self.spark.conf.get("spark.sql.adaptive.enabled"),
            'force_skew_join': self.spark.conf.get("spark.sql.adaptive.forceOptimizeSkewedJoin"),
            'max_shuffled_hash_join': self.spark.conf.get("spark.sql.adaptive.maxShuffledHashJoinLocalMapThreshold")
        }
        
        self.logger.info("Configurações atuais:")
        for key, value in config_checks.items():
            self.logger.info(f"  {key}: {value}")
        
        # Verificar saúde dos executors
        sc = self.spark.sparkContext
        status_tracker = sc.statusTracker()
        executor_infos = status_tracker.getExecutorInfos()
        
        self.logger.info(f"Executors ativos: {len(executor_infos)}")
        
        for executor in executor_infos:
            memory_percent = (executor.memoryUsed / executor.maxMemory) * 100
            self.logger.info(f"Executor {executor.executorId}: {memory_percent:.1f}% memória usada")
        
        return {
            'config': config_checks,
            'executor_count': len(executor_infos),
            'broadcast_config': self.broadcast_config
        }


# Função de configuração específica para Runtime 15.4
def configure_spark_runtime_15_4(spark):
    """Configura Spark especificamente para Runtime 15.4"""
    
    # Configurações de broadcast
    spark.conf.set("spark.sql.autoBroadcastJoinThreshold", "1GB")
    spark.conf.set("spark.sql.broadcastTimeout", "1200")
    spark.conf.set("spark.driver.maxResultSize", "8g")
    
    # Configurações AQE
    spark.conf.set("spark.sql.adaptive.enabled", "true")
    spark.conf.set("spark.sql.adaptive.forceOptimizeSkewedJoin", "false")
    spark.conf.set("spark.sql.adaptive.coalescePartitions.enabled", "true")
    spark.conf.set("spark.sql.adaptive.coalescePartitions.parallelismFirst", "false")
    spark.conf.set("spark.sql.adaptive.skewJoin.enabled", "true")
    spark.conf.set("spark.sql.adaptive.skewJoin.skewedPartitionFactor", "5")
    spark.conf.set("spark.sql.adaptive.skewJoin.skewedPartitionThresholdInBytes", "1GB")
    spark.conf.set("spark.sql.adaptive.localShuffleReader.enabled", "true")
    spark.conf.set("spark.sql.adaptive.maxShuffledHashJoinLocalMapThreshold", "1GB")
    spark.conf.set("spark.sql.adaptive.advisoryPartitionSizeInBytes", "512MB")
    
    # Configurações de memória
    spark.conf.set("spark.executor.memoryFraction", "0.75")
    spark.conf.set("spark.executor.memoryStorageFraction", "0.3")
    spark.conf.set("spark.sql.execution.arrow.maxRecordsPerBatch", "25000")
    
    # Configurações de rede
    spark.conf.set("spark.network.timeout", "1200s")
    spark.conf.set("spark.rpc.askTimeout", "1200s")
    spark.conf.set("spark.rpc.lookupTimeout", "1200s")
    
    # Configurações de serialização
    spark.conf.set("spark.serializer", "org.apache.spark.serializer.KryoSerializer")
    spark.conf.set("spark.kryo.unsafe", "true")
    spark.conf.set("spark.kryoserializer.buffer.max", "2048m")
    
    return spark


# Exemplo de uso
def exemplo_uso_runtime_15_4():
    """Exemplo de como usar a classe otimizada para Runtime 15.4"""
    
    # Configurar Spark para Runtime 15.4
    spark = configure_spark_runtime_15_4(spark)
    
    # Instanciar classe otimizada
    dados_cadastrais = DadosCadastraisRuntime154(spark, logger)
    
    # Executar pipeline completo
    df_resultado = dados_cadastrais.execute_optimized_pipeline_runtime_15_4()
    
    # Diagnóstico de broadcast se necessário
    diagnostico = dados_cadastrais.diagnose_broadcast_issues()
    
    # Obter métricas de performance
    metricas = dados_cadastrais.get_performance_metrics()
    
    return df_resultado, diagnostico, metricas

