"""
Versão Completa - dados_cadastrais_otimizado.py + Tabelas Bureau
Inclui todas as tabelas e métodos faltantes:
1. Bureau Email (s_stbr_dps_dps.dps_bure_pf_email)
2. Bureau Endereço (s_stbr_dps_dps.dps_bure_pf_ende)  
3. Bureau Telefone (s_stbr_dps_dps.dps_bure_pf_telf)
4. Correção CPF (petipodoc da PEDT150)
"""

from datetime import date
from pyspark.sql.functions import (
    col, concat, max, regexp_replace, when, trim, lit, substring, coalesce,
    first, concat_ws, collect_list, sort_array, datediff, current_date, lpad,
    upper, sha2, md5, broadcast, expr, split, array_join, size, filter as spark_filter,
    row_number, rank, dense_rank, lag, lead, sum as spark_sum, count, avg,
    collect_set, array_distinct, flatten, transform, exists, forall
)
from pyspark.sql.window import Window
from pyspark import StorageLevel
from pyspark.sql import DataFrame
import time
import logging
from typing import Dict, List, Optional, Tuple


class DadosCadastraisCompletoComBureau:
    """
    Versão COMPLETA da classe DadosCadastrais incluindo:
    - Todas as tabelas PEDT (001, 002, 003, 023, 036, 052, 150, 205)
    - Todas as tabelas Bureau (email, endereço, telefone)
    - Correção CPF (petipodoc da PEDT150)
    - Otimizações para 150GB+ de dados
    """

    def __init__(self, spark, logger=None):
        self.spark = spark
        self.logger = logger or logging.getLogger(__name__)
        
        # Configurações otimizadas para volume completo (350-450GB)
        self._configure_spark_for_complete_dataset()
        
        # Storage levels estratégicos
        self.storage_level_base = StorageLevel.MEMORY_AND_DISK_SER_2
        self.storage_level_intermediate = StorageLevel.DISK_ONLY_2
        self.storage_level_final = StorageLevel.MEMORY_ONLY_SER
        
        # Broadcast maps para lookups eficientes
        self._initialize_broadcast_maps()
        
        # Métricas de performance
        self.performance_metrics = {}

    def _configure_spark_for_complete_dataset(self):
        """Configurações específicas do Spark para dataset completo (PEDT + Bureau)"""
        
        optimizations = {
            # Adaptive Query Execution para dataset completo
            "spark.sql.adaptive.enabled": "true",
            "spark.sql.adaptive.coalescePartitions.enabled": "true",
            "spark.sql.adaptive.advisoryPartitionSizeInBytes": "256MB",  # Aumentado para Bureau
            "spark.sql.adaptive.localShuffleReader.enabled": "true",
            "spark.sql.adaptive.skewJoin.enabled": "true",
            "spark.sql.adaptive.skewJoin.skewedPartitionThresholdInBytes": "512MB",
            
            # Broadcast otimizado para múltiplas tabelas
            "spark.sql.autoBroadcastJoinThreshold": "100MB",  # Aumentado para Bureau
            "spark.sql.broadcastTimeout": "900",  # Aumentado para Bureau
            
            # Configurações de memória para dataset completo
            "spark.sql.execution.arrow.maxRecordsPerBatch": "50000",  # Reduzido para Bureau
            "spark.sql.adaptive.maxShuffledHashJoinLocalMapThreshold": "0",
            
            # Configurações específicas para Bureau (tabelas grandes)
            "spark.sql.files.maxPartitionBytes": "512MB",
            "spark.sql.adaptive.nonEmptyPartitionRatioForBroadcastJoin": "0.2",
            
            # Otimizações de I/O para múltiplas fontes
            "spark.sql.adaptive.optimizeSkewsInRebalancePartitions.enabled": "true",
            "spark.sql.adaptive.forceOptimizeSkewedJoin": "true"
        }
        
        for key, value in optimizations.items():
            try:
                self.spark.conf.set(key, value)
                self.logger.debug(f"Configuração aplicada: {key} = {value}")
            except Exception as e:
                self.logger.warning(f"Erro ao aplicar configuração {key}: {e}")

    def load_base_tables_completo(self) -> Dict[str, DataFrame]:
        """
        Carrega TODAS as tabelas base: PEDT + Bureau
        Estratégia: load-first, transform-later para aproveitar lazy evaluation.
        """
        self.logger.info("Iniciando carregamento COMPLETO das tabelas base (PEDT + Bureau)...")
        
        tables = {}
        
        # ========== TABELAS PEDT ==========
        
        # PEDT001 - Dados pessoais básicos
        df_data_ref_001 = self.collectOdate('b_stbr_pe.pedt001')
        tables['pedt001'] = (
            self.spark.read.table("b_stbr_pe.pedt001")
            .select("penomper", "penumdoc", "petipdoc", "penumper", "pepriape", 
                   "pefecnac", "peestciv", "penacper", "pesexper", "petipocu", 
                   "peusualt", "pesegape", "petipper")
            .where(
                (col("dat_ref_carga") == df_data_ref_001) &
                (col("petipper") == "F") &
                (~col("peusualt").isin("BG28101", "BG28102", "CIPRSANF", "CIPRSANJ", 
                                      "MQCICP", "MQWPCG", "RBD0712", "RBD0713", 
                                      "RBDO730", "RBHG702"))
            )
            .repartition(300, col("penumper"))  # Aumentado para dataset completo
        )
        
        # PEDT002 - Naturalidade e filiação
        df_data_ref_002 = self.collectOdate('b_stbr_pe.pedt002')
        tables['pedt002'] = (
            self.spark.read.table("b_stbr_pe.pedt002")
            .select("penumper", "peestrat", "penommad", "penompad")
            .where(col("dat_ref_carga") == df_data_ref_002)
            .repartition(300, col("penumper"))
        )
        
        # PEDT003 - Endereços e emails
        df_data_ref_003 = self.collectOdate('b_stbr_pe.pedt003')
        tables['pedt003'] = (
            self.spark.read.table("b_stbr_pe.pedt003")
            .select("penumper", "petipnur", "peobserv", "penumblo", 
                   "pedesloc", "pecodpro", "pecodpos")
            .where(col("dat_ref_carga") == df_data_ref_003)
            .repartition(300, col("penumper"))
        )
        
        # PEDT023 - Telefones
        df_data_ref_023 = self.collectOdate('b_stbr_pe.pedt023')
        tables['pedt023'] = (
            self.spark.read.table("b_stbr_pe.pedt023")
            .select("penumper", "peclatel", "pepretel", "peobserv", "petiptel")
            .where(col("dat_ref_carga") == df_data_ref_023)
            .repartition(300, col("penumper"))
        )
        
        # PEDT036 - Renda
        df_data_ref_036 = self.collectOdate('b_stbr_pe.pedt036')
        tables['pedt036'] = (
            self.spark.read.table("b_stbr_pe.pedt036")
            .select("penumper", "pefecalt", "peimping", "petiping")
            .where(
                (col("dat_ref_carga") == df_data_ref_036) &
                (col('petiping') == '099')
            )
            .repartition(300, col("penumper"))
        )
        
        # PEDT052 - PEP e coligadas
        df_data_ref_052 = self.collectOdate('b_stbr_pe.pedt052')
        tables['pedt052'] = (
            self.spark.read.table("b_stbr_pe.pedt052")
            .select("penumper", "peindica", "pevalind")
            .where(
                (col("dat_ref_carga") == df_data_ref_052) &
                (col('pevalind') == "S")
            )
            .repartition(300, col("penumper"))
        )
        
        # PEDT150 - Documentos (CORRIGIDO: petipodoc)
        df_data_ref_150 = self.collectOdate('b_stbr_pe.pedt150')
        tables['pedt150'] = (
            self.spark.read.table("b_stbr_pe.pedt150")
            .select("penumper", "penumero", "pecondoc", "petipodoc",  # ← CORRIGIDO
                   "peexppor", "pefecexp", "pelugexp")
            .where(col("dat_ref_carga") == df_data_ref_150)
            .repartition(300, col("penumper"))
        )
        
        # PEDT205 - Bens patrimoniais
        df_data_ref_205 = self.collectOdate('b_stbr_pe.pedt205')
        tables['pedt205'] = (
            self.spark.read.table("b_stbr_pe.pedt205")
            .select("cd_pess", "tp_bem")
            .where(col("dat_ref_carga") == df_data_ref_205)
            .withColumnRenamed("cd_pess", "penumper")
            .repartition(300, col("penumper"))
        )
        
        # ========== TABELAS BUREAU (FALTANTES) ==========
        
        # Bureau Email
        df_data_ref_bureau_email = self.collectOdate('s_stbr_dps_dps.dps_bure_pf_email')
        tables['bureau_email'] = (
            self.spark.read.table("s_stbr_dps_dps.dps_bure_pf_email")
            .select("nr_cpf", "ds_email", "ds_selo_quld", "id_pe")
            .where(
                (col("dat_ref_carga") == df_data_ref_bureau_email) &
                (upper(col("ds_selo_quld")) != "RUIM") &
                (col("id_pe") != 1)
            )
            .repartition(400, col("nr_cpf"))  # Bureau tem mais dados
        )
        
        # Bureau Endereço
        df_data_ref_bureau_ende = self.collectOdate('s_stbr_dps_dps.dps_bure_pf_ende')
        tables['bureau_endereco'] = (
            self.spark.read.table("s_stbr_dps_dps.dps_bure_pf_ende")
            .select("nr_cpf", "ds_logr", "nr_logr", "ds_comp", "ds_bair", 
                   "ds_cida", "sg_uf", "nr_cep", "tp_doml", "ds_selo_quld", "id_pe")
            .where(
                (col("dat_ref_carga") == df_data_ref_bureau_ende) &
                (upper(col("ds_selo_quld")) != "RUIM") &
                (col("id_pe") != 1) &
                (col("tp_doml").isin(1, 2, 3))
            )
            .repartition(500, col("nr_cpf"))  # Bureau endereço é a maior tabela
        )
        
        # Bureau Telefone
        df_data_ref_bureau_telf = self.collectOdate('s_stbr_dps_dps.dps_bure_pf_telf')
        tables['bureau_telefone'] = (
            self.spark.read.table("s_stbr_dps_dps.dps_bure_pf_telf")
            .select("nr_cpf", "nr_ddd", "nr_telf", "id_celu", "ds_selo_quld", "id_pe")
            .where(
                (col("dat_ref_carga") == df_data_ref_bureau_telf) &
                (col("id_pe") != 1) &
                (upper(col("ds_selo_quld")) != "RUIM")
            )
            .repartition(450, col("nr_cpf"))
        )
        
        self.logger.info(f"Carregadas {len(tables)} tabelas base COMPLETAS (PEDT + Bureau)")
        self.logger.info("Tabelas PEDT: pedt001, pedt002, pedt003, pedt023, pedt036, pedt052, pedt150, pedt205")
        self.logger.info("Tabelas Bureau: bureau_email, bureau_endereco, bureau_telefone")
        
        return tables

    def _process_pedt150_optimized_corrigido(self, df: DataFrame) -> DataFrame:
        """Processa PEDT150 (documentos) com CPF CORRETO (petipodoc)"""
        
        # Filtro para documentos relevantes (CORRIGIDO: petipodoc)
        df_filtered = df.where(
            col("petipodoc").isin("01", "02", "04", "07", "08", "09", "10", "12", "36", "39", "13")
        )
        
        # *** LÓGICA DE CPF CORRIGIDA ***
        df_with_cpf = df_filtered.withColumn(
            "CPF", 
            when(col("petipodoc") == "13", col("penumero"))
        )
        
        # Window specification
        window_spec = Window.partitionBy("penumper")
        
        return df_with_cpf.select(
            col("penumper"),
            col("petipodoc"),  # ← CORRIGIDO
            col("penumero"),
            col("CPF"),        # ← NOVA COLUNA CPF
            col("peexppor"),
            col("pefecexp"),
            expr(self._create_estado_lookup_expr("pelugexp", "full")).alias("cd_esta_emis"),
            
            # Concatenação otimizada de documentos
            concat_ws(" ", 
                trim(col("penumero")),
                trim(col("peexppor")),
                trim(col("pefecexp")),
                expr(self._create_estado_lookup_expr("pelugexp", "full"))
            ).alias("documento_completo")
        ).select(
            col("penumper"),
            col("CPF"),  # ← INCLUIR CPF NO SELECT FINAL
            
            # Documentos específicos usando window functions (TODOS CORRIGIDOS: petipodoc)
            first(
                when(col("petipodoc") == "01", col("documento_completo")),
                ignorenulls=True
            ).over(window_spec).alias("identidade_rg"),
            
            first(
                when(col("petipodoc") == "02", col("documento_completo")),
                ignorenulls=True
            ).over(window_spec).alias("carteira_profissional"),
            
            first(
                when(col("petipodoc") == "04", col("documento_completo")),
                ignorenulls=True
            ).over(window_spec).alias("passaporte"),
            
            first(
                when(col("petipodoc") == "07", col("documento_completo")),
                ignorenulls=True
            ).over(window_spec).alias("pis"),
            
            first(
                when(col("petipodoc") == "08", col("documento_completo")),
                ignorenulls=True
            ).over(window_spec).alias("titulo_de_eleitor"),
            
            first(
                when(col("petipodoc") == "09", col("documento_completo")),
                ignorenulls=True
            ).over(window_spec).alias("identidade_entidades_classe"),
            
            first(
                when(col("petipodoc") == "10", col("documento_completo")),
                ignorenulls=True
            ).over(window_spec).alias("rne_registro_nac_estrang"),
            
            first(
                when(col("petipodoc") == "12", col("documento_completo")),
                ignorenulls=True
            ).over(window_spec).alias("cnh_cart_nac_habilitacao"),
            
            first(
                when(col("petipodoc") == "36", col("documento_completo")),
                ignorenulls=True
            ).over(window_spec).alias("protocolo_do_pedido_refugio"),
            
            first(
                when(col("petipodoc") == "39", col("documento_completo")),
                ignorenulls=True
            ).over(window_spec).alias("guia_de_acolhimento"),
            
            # *** CPF COMO DOCUMENTO ESPECÍFICO ***
            first(
                when(col("petipodoc") == "13", col("penumero")),
                ignorenulls=True
            ).over(window_spec).alias("cpf_documento")
            
        ).distinct()

    def _process_bureau_email_optimized(self, df: DataFrame) -> DataFrame:
        """Processa emails do Bureau com otimizações"""
        
        self.logger.info("Processando Bureau Email...")
        
        # Preparar CPF com padding
        df_prepared = df.withColumn("cpf", lpad(col("nr_cpf"), 11, "0"))
        
        # Selecionar e renomear colunas
        df_selected = df_prepared.select(
            col("cpf"),
            col("ds_email").alias("email_bureau")
        )
        
        # Agrupamento otimizado - primeiro email válido por CPF
        window_spec = Window.partitionBy("cpf").orderBy(col("email_bureau"))
        
        df_grouped = df_selected.withColumn(
            "rn", row_number().over(window_spec)
        ).filter(col("rn") == 1).drop("rn")
        
        self.logger.info("Bureau Email processado")
        return df_grouped

    def _process_bureau_endereco_optimized(self, df: DataFrame) -> DataFrame:
        """Processa endereços do Bureau com otimizações"""
        
        self.logger.info("Processando Bureau Endereço...")
        
        # Preparar CPF com padding
        df_prepared = df.withColumn("cpf", lpad(col("nr_cpf"), 11, "0"))
        
        # Criar endereços por tipo de domicílio
        df_enderecos = df_prepared.withColumn(
            "endereco_residencial_bureau",
            when(col("tp_doml") == 1,
                trim(concat_ws(", ",
                    coalesce(trim(col("ds_logr")), lit("")),
                    coalesce(trim(col("nr_logr")), lit("")),
                    coalesce(trim(col("ds_comp")), lit("")),
                    coalesce(trim(col("ds_bair")), lit("")),
                    coalesce(trim(col("ds_cida")), lit("")),
                    coalesce(trim(col("sg_uf")), lit("")),
                    coalesce(trim(col("nr_cep")), lit(""))
                ))
            )
        ).withColumn(
            "endereco_comercial_bureau",
            when(col("tp_doml") == 2,
                trim(concat_ws(", ",
                    coalesce(trim(col("ds_logr")), lit("")),
                    coalesce(trim(col("nr_logr")), lit("")),
                    coalesce(trim(col("ds_comp")), lit("")),
                    coalesce(trim(col("ds_bair")), lit("")),
                    coalesce(trim(col("ds_cida")), lit("")),
                    coalesce(trim(col("sg_uf")), lit("")),
                    coalesce(trim(col("nr_cep")), lit(""))
                ))
            )
        ).withColumn(
            "endereco_correspondencia_bureau",
            when(col("tp_doml") == 3,
                trim(concat_ws(", ",
                    coalesce(trim(col("ds_logr")), lit("")),
                    coalesce(trim(col("nr_logr")), lit("")),
                    coalesce(trim(col("ds_comp")), lit("")),
                    coalesce(trim(col("ds_bair")), lit("")),
                    coalesce(trim(col("ds_cida")), lit("")),
                    coalesce(trim(col("sg_uf")), lit("")),
                    coalesce(trim(col("nr_cep")), lit(""))
                ))
            )
        )
        
        # Agrupamento por CPF
        df_grouped = df_enderecos.groupBy("cpf").agg(
            first("endereco_residencial_bureau", ignorenulls=True).alias("endereco_residencial_bureau"),
            first("endereco_comercial_bureau", ignorenulls=True).alias("endereco_comercial_bureau"),
            first("endereco_correspondencia_bureau", ignorenulls=True).alias("endereco_correspondencia_bureau")
        )
        
        self.logger.info("Bureau Endereço processado")
        return df_grouped

    def _process_bureau_telefone_optimized(self, df: DataFrame) -> DataFrame:
        """Processa telefones do Bureau com otimizações"""
        
        self.logger.info("Processando Bureau Telefone...")
        
        # Preparar CPF com padding
        df_prepared = df.withColumn("cpf", lpad(col("nr_cpf"), 11, "0"))
        
        # Criar telefones por tipo
        df_telefones = df_prepared.withColumn(
            "nr_tel_cel_bureau",
            when(col("id_celu") == "1",
                concat(lit("55 "), col("nr_ddd"), lit(" "), col("nr_telf"))
            )
        ).withColumn(
            "nr_tel_alternativo_bureau",
            when(col("id_celu") != "1",
                concat(lit("55 "), col("nr_ddd"), lit(" "), col("nr_telf"))
            )
        )
        
        # Agrupamento e concatenação de múltiplos telefones
        df_grouped = df_telefones.groupBy("cpf").agg(
            concat_ws(" | ", 
                sort_array(collect_list("nr_tel_cel_bureau"))
            ).alias("nr_tel_cel_bureau"),
            concat_ws(" | ", 
                sort_array(collect_list("nr_tel_alternativo_bureau"))
            ).alias("nr_tel_alternativo_bureau")
        )
        
        self.logger.info("Bureau Telefone processado")
        return df_grouped

    def process_unified_pipeline_completo(self) -> DataFrame:
        """
        Pipeline unificado COMPLETO que processa TODAS as transformações:
        - Tabelas PEDT (8 tabelas)
        - Tabelas Bureau (3 tabelas)
        - CPF corrigido (petipodoc)
        - Otimizações para 350-450GB
        """
        
        start_time = time.time()
        self.logger.info("Iniciando pipeline unificado COMPLETO (PEDT + Bureau)...")
        
        # Carregar todas as tabelas (PEDT + Bureau)
        tables = self.load_base_tables_completo()
        
        # Processar tabelas PEDT
        self.logger.info("Processando tabelas PEDT...")
        df_base = self._process_pedt001_optimized(tables['pedt001'])
        df_naturalidade = self._process_pedt002_optimized(tables['pedt002'])
        df_endereco = self._process_pedt003_optimized(tables['pedt003'])
        df_telefone = self._process_pedt023_optimized(tables['pedt023'])
        df_renda = self._process_pedt036_optimized(tables['pedt036'])
        df_pep = self._process_pedt052_optimized(tables['pedt052'])
        df_documentos = self._process_pedt150_optimized_corrigido(tables['pedt150'])  # ← CORRIGIDO
        df_bens = self._process_pedt205_optimized(tables['pedt205'])
        
        # Processar tabelas Bureau
        self.logger.info("Processando tabelas Bureau...")
        df_bureau_email = self._process_bureau_email_optimized(tables['bureau_email'])
        df_bureau_endereco = self._process_bureau_endereco_optimized(tables['bureau_endereco'])
        df_bureau_telefone = self._process_bureau_telefone_optimized(tables['bureau_telefone'])
        
        # Joins otimizados incluindo Bureau
        self.logger.info("Executando joins otimizados (PEDT + Bureau)...")
        result = self._perform_optimized_joins_with_bureau(
            df_base, df_naturalidade, df_endereco, df_telefone, df_renda, 
            df_pep, df_documentos, df_bens,
            df_bureau_email, df_bureau_endereco, df_bureau_telefone
        )
        
        # Aplicar transformações finais
        result_final = self._apply_final_transformations_completo(result)
        
        # Cache do resultado final
        result_final = result_final.persist(self.storage_level_final)
        
        # Métricas de performance
        total_time = time.time() - start_time
        record_count = result_final.count()
        
        self.performance_metrics.update({
            'total_execution_time': total_time,
            'total_records': record_count,
            'throughput_per_second': record_count / total_time if total_time > 0 else 0,
            'tables_processed': len(tables),
            'includes_bureau': True,
            'cpf_corrected': True
        })
        
        self.logger.info(f"Pipeline COMPLETO concluído: {record_count:,} registros em {total_time/60:.1f} minutos")
        self.logger.info(f"Throughput: {self.performance_metrics['throughput_per_second']:,.0f} registros/segundo")
        self.logger.info("Inclui: PEDT (8 tabelas) + Bureau (3 tabelas) + CPF corrigido")
        
        return result_final

    def _perform_optimized_joins_with_bureau(self, df_base, df_naturalidade, df_endereco, 
                                           df_telefone, df_renda, df_pep, df_documentos, df_bens,
                                           df_bureau_email, df_bureau_endereco, df_bureau_telefone):
        """Realiza joins otimizados incluindo tabelas Bureau"""
        
        self.logger.info("Iniciando joins otimizados com Bureau...")
        
        # Função para determinar se deve usar broadcast
        def smart_join(large_df: DataFrame, small_df: DataFrame, join_key: str, join_type: str = "left") -> DataFrame:
            try:
                small_count = small_df.count()
                estimated_size = small_count * 1000  # 1KB por registro
                
                if estimated_size < 300_000_000:  # 300MB (aumentado para Bureau)
                    self.logger.info(f"Usando broadcast join para tabela com {small_count:,} registros")
                    return large_df.join(broadcast(small_df), join_key, join_type)
                else:
                    self.logger.info(f"Usando join regular para tabela com {small_count:,} registros")
                    return large_df.join(small_df, join_key, join_type)
            except Exception as e:
                self.logger.warning(f"Erro ao determinar tipo de join: {e}. Usando join regular.")
                return large_df.join(small_df, join_key, join_type)
        
        # Sequência de joins otimizados - PEDT primeiro
        result = df_base
        result = smart_join(result, df_naturalidade, "penumper")
        result = smart_join(result, df_endereco, "penumper")
        result = smart_join(result, df_telefone, "penumper")
        result = smart_join(result, df_renda, "penumper")
        result = smart_join(result, df_pep, "penumper")
        result = smart_join(result, df_documentos, "penumper")
        result = smart_join(result, df_bens, "penumper")
        
        # Joins Bureau por CPF (requer CPF da PEDT150)
        self.logger.info("Executando joins Bureau por CPF...")
        result = smart_join(result, df_bureau_email, "CPF")
        result = smart_join(result, df_bureau_endereco, "CPF")
        result = smart_join(result, df_bureau_telefone, "CPF")
        
        self.logger.info("Joins otimizados com Bureau concluídos")
        return result

    def _apply_final_transformations_completo(self, df: DataFrame) -> DataFrame:
        """Aplica transformações finais incluindo consolidação Bureau"""
        
        self.logger.info("Aplicando transformações finais com dados Bureau...")
        
        # Consolidar emails (PEDT + Bureau)
        df = df.withColumn(
            "email_consolidado",
            when(
                col("email").isNull() | (col("email") == "") | (col("email") == "null"),
                col("email_bureau")
            ).otherwise(
                when(
                    col("email_bureau").isNotNull() & (col("email_bureau") != ""),
                    concat_ws(", ", col("email"), col("email_bureau"))
                ).otherwise(col("email"))
            )
        )
        
        # Consolidar telefones (PEDT + Bureau)
        df = df.withColumn(
            "nr_tel_cel_consolidado",
            when(
                col("nr_tel_cel").isNull() | (col("nr_tel_cel") == "") | (col("nr_tel_cel") == "null"),
                col("nr_tel_cel_bureau")
            ).otherwise(
                when(
                    col("nr_tel_cel_bureau").isNotNull() & (col("nr_tel_cel_bureau") != ""),
                    concat_ws(", ", col("nr_tel_cel"), col("nr_tel_cel_bureau"))
                ).otherwise(col("nr_tel_cel"))
            )
        ).withColumn(
            "nr_tel_res_consolidado",
            when(
                col("nr_tel_res").isNull() | (col("nr_tel_res") == "") | (col("nr_tel_res") == "null"),
                col("nr_tel_alternativo_bureau")
            ).otherwise(
                when(
                    col("nr_tel_alternativo_bureau").isNotNull() & (col("nr_tel_alternativo_bureau") != ""),
                    concat_ws(", ", col("nr_tel_res"), col("nr_tel_alternativo_bureau"))
                ).otherwise(col("nr_tel_res"))
            )
        )
        
        # Consolidar endereços (PEDT + Bureau)
        df = df.withColumn(
            "endereco_residencial_consolidado",
            when(
                col("endereco_residencial").isNull() | (col("endereco_residencial") == ""),
                col("endereco_residencial_bureau")
            ).otherwise(col("endereco_residencial"))
        ).withColumn(
            "endereco_comercial_consolidado",
            coalesce(col("endereco_comercial_bureau"), lit(""))
        ).withColumn(
            "endereco_correspondencia_consolidado",
            coalesce(col("endereco_correspondencia_bureau"), lit(""))
        )
        
        # Adicionar metadados de qualidade
        df = df.withColumn("fonte_dados", lit("PEDT_BUREAU_CONSOLIDADO")) \
               .withColumn("data_processamento", current_date()) \
               .withColumn("versao_pipeline", lit("COMPLETO_V1.0")) \
               .withColumn("cpf_corrigido", lit(True)) \
               .withColumn("bureau_incluido", lit(True))
        
        self.logger.info("Transformações finais com Bureau concluídas")
        return df

    # Métodos auxiliares (collectOdate, broadcast maps, etc.) permanecem iguais
    def collectOdate(self, tabela):
        """Coleta a data de referência mais recente da tabela"""
        odate = self.spark.sql(f'show partitions {tabela}').orderBy(col('dat_ref_carga').asc()).collect()[-1][-1]
        return odate

    def get_performance_metrics(self) -> Dict[str, any]:
        """Retorna métricas de performance do pipeline completo"""
        return self.performance_metrics

    def validate_completeness(self, df_result: DataFrame) -> Dict[str, any]:
        """Valida se o pipeline completo incluiu todos os dados esperados"""
        
        validations = {
            'has_cpf_column': 'CPF' in df_result.columns,
            'has_bureau_email': 'email_bureau' in df_result.columns,
            'has_bureau_endereco': 'endereco_residencial_bureau' in df_result.columns,
            'has_bureau_telefone': 'nr_tel_cel_bureau' in df_result.columns,
            'has_consolidated_fields': 'email_consolidado' in df_result.columns,
            'cpf_not_null_count': df_result.filter(col("CPF").isNotNull()).count(),
            'bureau_email_not_null_count': df_result.filter(col("email_bureau").isNotNull()).count(),
            'total_records': df_result.count()
        }
        
        validations['completeness_score'] = sum([
            validations['has_cpf_column'],
            validations['has_bureau_email'],
            validations['has_bureau_endereco'],
            validations['has_bureau_telefone'],
            validations['has_consolidated_fields']
        ]) / 5.0
        
        return validations


# Exemplo de uso
def exemplo_uso_completo():
    """Exemplo de uso da versão completa"""
    
    exemplo = '''
# EXEMPLO DE USO - VERSÃO COMPLETA:

from dados_cadastrais_completo_com_bureau import DadosCadastraisCompletoComBureau
import logging

# Configurar logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

# Inicializar classe completa
dados_cadastrais = DadosCadastraisCompletoComBureau(spark=spark, logger=logger)

# Executar pipeline completo (PEDT + Bureau + CPF corrigido)
df_resultado = dados_cadastrais.process_unified_pipeline_completo()

# Validar completude
validacao = dados_cadastrais.validate_completeness(df_resultado)
print(f"Score de completude: {validacao['completeness_score']:.1%}")

# Métricas de performance
metricas = dados_cadastrais.get_performance_metrics()
print(f"Tempo total: {metricas['total_execution_time']/60:.1f} minutos")
print(f"Registros processados: {metricas['total_records']:,}")
print(f"Inclui Bureau: {metricas['includes_bureau']}")
print(f"CPF corrigido: {metricas['cpf_corrected']}")

# Verificar dados consolidados
df_resultado.select(
    "penumper", "CPF", "nome", 
    "email_consolidado", "nr_tel_cel_consolidado",
    "endereco_residencial_consolidado"
).show(10, truncate=False)
'''
    
    return exemplo


if __name__ == "__main__":
    print("Versão COMPLETA - DadosCadastrais com Bureau")
    print("=" * 60)
    print("Inclui:")
    print("- 8 tabelas PEDT (001, 002, 003, 023, 036, 052, 150, 205)")
    print("- 3 tabelas Bureau (email, endereço, telefone)")
    print("- CPF corrigido (petipodoc da PEDT150)")
    print("- Consolidação PEDT + Bureau")
    print("- Otimizações para 350-450GB")
    print("\nExemplo de uso:")
    print(exemplo_uso_completo())

