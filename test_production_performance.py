"""
Script de Teste de Performance para Solução de Sincronização PostgreSQL
Valida performance e funcionalidade para volumes de 150GB
"""

import logging
import time
import random
import string
from datetime import datetime, timedelta
from pyspark.sql import SparkSession
from pyspark.sql.functions import col, lit, rand, when
from pyspark.sql.types import StructType, StructField, StringType, IntegerType, TimestampType
from compare_data_production_optimized import CompareDataProductionOptimized


class PerformanceTestSuite:
    """Suite de testes de performance para validação da solução"""
    
    def __init__(self, spark: SparkSession):
        self.spark = spark
        self.logger = self._setup_logging()
        self.test_results = {}
        
    def _setup_logging(self):
        """Configurar logging para testes"""
        logging.basicConfig(
            level=logging.INFO,
            format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
        )
        return logging.getLogger(__name__)
    
    def create_test_data(self, num_records: int, table_name: str):
        """Criar dados de teste simulando estrutura real"""
        
        self.logger.info(f"Criando {num_records:,} registros de teste")
        
        # Definir schema similar aos dados reais
        schema = StructType([
            StructField("penumper", StringType(), False),
            StructField("nome", StringType(), True),
            StructField("endereco", StringType(), True),
            StructField("cidade", StringType(), True),
            StructField("estado", StringType(), True),
            StructField("cep", StringType(), True),
            StructField("telefone", StringType(), True),
            StructField("email", StringType(), True),
            StructField("data_nascimento", TimestampType(), True),
            StructField("estado_civil", StringType(), True),
            StructField("ocupacao", StringType(), True),
            StructField("renda", IntegerType(), True)
        ])
        
        # Gerar dados sintéticos
        def generate_record(i):
            return (
                f"PER{i:010d}",  # penumper
                f"Nome Teste {i}",  # nome
                f"Rua Teste {i % 1000}, {i % 100}",  # endereco
                f"Cidade{i % 50}",  # cidade
                random.choice(['SP', 'RJ', 'MG', 'RS', 'PR', 'SC', 'BA', 'GO']),  # estado
                f"{random.randint(10000, 99999):05d}-{random.randint(100, 999):03d}",  # cep
                f"({random.randint(11, 99):02d}) {random.randint(90000, 99999):05d}-{random.randint(1000, 9999):04d}",  # telefone
                f"teste{i}@email.com",  # email
                datetime.now() - timedelta(days=random.randint(365*18, 365*80)),  # data_nascimento
                random.choice(['SOLTEIRO', 'CASADO', 'DIVORCIADO', 'VIUVO']),  # estado_civil
                random.choice(['ENGENHEIRO', 'MEDICO', 'PROFESSOR', 'ADVOGADO', 'COMERCIANTE']),  # ocupacao
                random.randint(1000, 20000)  # renda
            )
        
        # Criar DataFrame com paralelização otimizada
        num_partitions = min(200, max(10, num_records // 50000))
        
        records_rdd = self.spark.sparkContext.parallelize(
            [generate_record(i) for i in range(num_records)], 
            numSlices=num_partitions
        )
        
        df = self.spark.createDataFrame(records_rdd, schema)
        
        # Salvar como tabela Delta
        df.write.mode("overwrite").saveAsTable(table_name)
        
        self.logger.info(f"Dados de teste criados: {table_name}")
        return df
    
    def test_small_volume(self, compare_data: CompareDataProductionOptimized):
        """Teste com volume pequeno (100K registros)"""
        
        self.logger.info("Executando teste de volume pequeno (100K registros)")
        
        # Criar dados de teste
        test_table = "test_data_small"
        self.create_test_data(100000, test_table)
        
        # Executar sincronização
        start_time = time.time()
        
        result = compare_data.sync_with_checkpoint(
            delta_table_name=test_table,
            postgres_table_name="test_sync_small",
            key_columns=["penumper"],
            chunk_size=50000,
            mark_for_deletion=False,
            job_id="test_small_volume"
        )
        
        execution_time = time.time() - start_time
        
        # Validar resultados
        expected_throughput = 10000  # registros por segundo mínimo
        actual_throughput = result['throughput_per_second']
        
        test_result = {
            'volume': '100K',
            'execution_time': execution_time,
            'throughput': actual_throughput,
            'expected_throughput': expected_throughput,
            'passed': actual_throughput >= expected_throughput,
            'chunks_processed': result['chunks_processed']
        }
        
        self.test_results['small_volume'] = test_result
        
        if test_result['passed']:
            self.logger.info(f"Teste pequeno PASSOU: {actual_throughput:,.0f} rec/s")
        else:
            self.logger.warning(f"Teste pequeno FALHOU: {actual_throughput:,.0f} rec/s < {expected_throughput:,.0f} rec/s")
        
        return test_result
    
    def test_medium_volume(self, compare_data: CompareDataProductionOptimized):
        """Teste com volume médio (10M registros)"""
        
        self.logger.info("Executando teste de volume médio (10M registros)")
        
        # Criar dados de teste
        test_table = "test_data_medium"
        self.create_test_data(10000000, test_table)
        
        # Executar sincronização
        start_time = time.time()
        
        result = compare_data.sync_with_checkpoint(
            delta_table_name=test_table,
            postgres_table_name="test_sync_medium",
            key_columns=["penumper"],
            chunk_size=1000000,
            mark_for_deletion=True,
            job_id="test_medium_volume"
        )
        
        execution_time = time.time() - start_time
        
        # Validar resultados
        expected_throughput = 25000  # registros por segundo mínimo
        actual_throughput = result['throughput_per_second']
        
        test_result = {
            'volume': '10M',
            'execution_time': execution_time,
            'throughput': actual_throughput,
            'expected_throughput': expected_throughput,
            'passed': actual_throughput >= expected_throughput,
            'chunks_processed': result['chunks_processed']
        }
        
        self.test_results['medium_volume'] = test_result
        
        if test_result['passed']:
            self.logger.info(f"Teste médio PASSOU: {actual_throughput:,.0f} rec/s")
        else:
            self.logger.warning(f"Teste médio FALHOU: {actual_throughput:,.0f} rec/s < {expected_throughput:,.0f} rec/s")
        
        return test_result
    
    def test_checkpoint_resume(self, compare_data: CompareDataProductionOptimized):
        """Teste de funcionalidade de checkpoint/resume"""
        
        self.logger.info("Testando funcionalidade de checkpoint/resume")
        
        # Criar dados de teste
        test_table = "test_data_checkpoint"
        self.create_test_data(5000000, test_table)
        
        job_id = "test_checkpoint_resume"
        
        # Simular falha após alguns chunks
        class SimulatedFailure(Exception):
            pass
        
        # Primeira execução (com falha simulada)
        try:
            # Modificar temporariamente para falhar após 3 chunks
            original_method = compare_data._process_chunk_with_metrics
            
            def failing_method(df_prepared, chunk_id, checkpoint_data):
                if chunk_id >= 3:
                    raise SimulatedFailure("Falha simulada para teste")
                return original_method(df_prepared, chunk_id, checkpoint_data)
            
            compare_data._process_chunk_with_metrics = failing_method
            
            compare_data.sync_with_checkpoint(
                delta_table_name=test_table,
                postgres_table_name="test_sync_checkpoint",
                key_columns=["penumper"],
                chunk_size=1000000,
                mark_for_deletion=False,
                job_id=job_id,
                auto_resume=False
            )
            
        except SimulatedFailure:
            self.logger.info("Falha simulada ocorreu conforme esperado")
        
        # Restaurar método original
        compare_data._process_chunk_with_metrics = original_method
        
        # Segunda execução (resume)
        start_resume_time = time.time()
        
        result = compare_data.sync_with_checkpoint(
            delta_table_name=test_table,
            postgres_table_name="test_sync_checkpoint",
            key_columns=["penumper"],
            chunk_size=1000000,
            mark_for_deletion=False,
            job_id=job_id,
            auto_resume=True
        )
        
        resume_time = time.time() - start_resume_time
        
        # Validar que o resume funcionou
        test_result = {
            'resume_time': resume_time,
            'total_chunks': result['chunks_processed'],
            'passed': result['success'] and resume_time < 300,  # Deve completar em menos de 5 min
            'chunks_resumed': result['chunks_processed'] - 3  # Chunks processados após resume
        }
        
        self.test_results['checkpoint_resume'] = test_result
        
        if test_result['passed']:
            self.logger.info(f"Teste checkpoint PASSOU: resume em {resume_time:.1f}s")
        else:
            self.logger.warning(f"Teste checkpoint FALHOU: resume em {resume_time:.1f}s")
        
        return test_result
    
    def test_configuration_optimization(self, compare_data: CompareDataProductionOptimized):
        """Teste de otimizações de configuração"""
        
        self.logger.info("Testando otimizações de configuração Spark")
        
        # Verificar configurações críticas
        critical_configs = {
            "spark.sql.adaptive.enabled": "true",
            "spark.sql.adaptive.coalescePartitions.enabled": "true",
            "spark.sql.autoBroadcastJoinThreshold": "50MB",
            "spark.serializer": "org.apache.spark.serializer.KryoSerializer",
            "spark.sql.execution.arrow.pyspark.enabled": "true"
        }
        
        config_results = {}
        all_configs_correct = True
        
        for config_key, expected_value in critical_configs.items():
            try:
                actual_value = self.spark.conf.get(config_key)
                is_correct = actual_value == expected_value
                config_results[config_key] = {
                    'expected': expected_value,
                    'actual': actual_value,
                    'correct': is_correct
                }
                if not is_correct:
                    all_configs_correct = False
                    self.logger.warning(f"Configuração incorreta: {config_key} = {actual_value} (esperado: {expected_value})")
            except Exception as e:
                config_results[config_key] = {
                    'expected': expected_value,
                    'actual': 'NOT_SET',
                    'correct': False,
                    'error': str(e)
                }
                all_configs_correct = False
        
        test_result = {
            'all_configs_correct': all_configs_correct,
            'config_details': config_results,
            'passed': all_configs_correct
        }
        
        self.test_results['configuration'] = test_result
        
        if test_result['passed']:
            self.logger.info("Teste de configuração PASSOU")
        else:
            self.logger.warning("Teste de configuração FALHOU")
        
        return test_result
    
    def estimate_150gb_performance(self):
        """Estimar performance para 150GB baseado nos testes"""
        
        if 'medium_volume' not in self.test_results:
            self.logger.warning("Teste de volume médio não executado - não é possível estimar 150GB")
            return None
        
        medium_result = self.test_results['medium_volume']
        medium_throughput = medium_result['throughput']
        
        # Estimar para 150GB (aproximadamente 100M registros)
        estimated_records_150gb = 100000000
        estimated_time_seconds = estimated_records_150gb / medium_throughput
        estimated_time_minutes = estimated_time_seconds / 60
        
        # Aplicar fator de correção para volume maior (degradação esperada de 10-15%)
        correction_factor = 1.15
        estimated_time_minutes_corrected = estimated_time_minutes * correction_factor
        
        estimation = {
            'estimated_records': estimated_records_150gb,
            'base_throughput': medium_throughput,
            'estimated_time_minutes': estimated_time_minutes_corrected,
            'estimated_time_hours': estimated_time_minutes_corrected / 60,
            'meets_target': estimated_time_minutes_corrected <= 90  # Meta: máximo 1.5 horas
        }
        
        self.test_results['150gb_estimation'] = estimation
        
        self.logger.info(f"Estimativa para 150GB: {estimated_time_minutes_corrected:.1f} minutos")
        
        return estimation
    
    def run_full_test_suite(self, postgres_config: Dict):
        """Executar suite completa de testes"""
        
        self.logger.info("Iniciando suite completa de testes de performance")
        
        # Inicializar classe de sincronização
        compare_data = CompareDataProductionOptimized(
            spark=self.spark,
            logger=self.logger,
            checkpoint_dir="/tmp/test_checkpoints"
        )
        
        # Configurar PostgreSQL
        compare_data.configure_postgres_connection(**postgres_config)
        
        # Executar testes
        tests = [
            ('Configuração', lambda: self.test_configuration_optimization(compare_data)),
            ('Volume Pequeno', lambda: self.test_small_volume(compare_data)),
            ('Volume Médio', lambda: self.test_medium_volume(compare_data)),
            ('Checkpoint/Resume', lambda: self.test_checkpoint_resume(compare_data))
        ]
        
        for test_name, test_func in tests:
            try:
                self.logger.info(f"Executando teste: {test_name}")
                test_func()
            except Exception as e:
                self.logger.error(f"Erro no teste {test_name}: {e}")
                self.test_results[test_name.lower().replace(' ', '_')] = {
                    'passed': False,
                    'error': str(e)
                }
        
        # Gerar estimativa para 150GB
        self.estimate_150gb_performance()
        
        # Gerar relatório final
        return self.generate_test_report()
    
    def generate_test_report(self):
        """Gerar relatório final dos testes"""
        
        report = {
            'timestamp': datetime.now().isoformat(),
            'summary': {
                'total_tests': len(self.test_results),
                'passed_tests': sum(1 for result in self.test_results.values() 
                                  if isinstance(result, dict) and result.get('passed', False)),
                'overall_success': True
            },
            'test_results': self.test_results,
            'recommendations': []
        }
        
        # Verificar se todos os testes passaram
        failed_tests = [name for name, result in self.test_results.items() 
                       if isinstance(result, dict) and not result.get('passed', False)]
        
        if failed_tests:
            report['summary']['overall_success'] = False
            report['recommendations'].append(f"Testes falharam: {', '.join(failed_tests)}")
        
        # Verificar estimativa para 150GB
        if '150gb_estimation' in self.test_results:
            estimation = self.test_results['150gb_estimation']
            if not estimation['meets_target']:
                report['recommendations'].append(
                    f"Performance estimada para 150GB ({estimation['estimated_time_minutes']:.1f} min) "
                    "excede meta de 90 minutos"
                )
        
        # Gerar recomendações baseadas nos resultados
        if 'medium_volume' in self.test_results:
            throughput = self.test_results['medium_volume'].get('throughput', 0)
            if throughput < 20000:
                report['recommendations'].append(
                    "Throughput abaixo do esperado - considerar aumentar recursos do cluster"
                )
        
        return report


def main():
    """Função principal para executar testes"""
    
    # Configurar Spark
    spark = SparkSession.builder \
        .appName("PerformanceTestSuite") \
        .config("spark.sql.adaptive.enabled", "true") \
        .config("spark.sql.adaptive.coalescePartitions.enabled", "true") \
        .getOrCreate()
    
    # Configuração PostgreSQL para testes
    postgres_config = {
        'host': 'localhost',  # Substituir pelos dados reais
        'port': 5432,
        'database': 'test_db',
        'user': 'test_user',
        'password': 'test_password'
    }
    
    # Executar testes
    test_suite = PerformanceTestSuite(spark)
    
    try:
        report = test_suite.run_full_test_suite(postgres_config)
        
        # Exibir relatório
        print("\n" + "="*80)
        print("RELATÓRIO DE TESTES DE PERFORMANCE")
        print("="*80)
        
        print(f"\nResumo:")
        print(f"- Total de testes: {report['summary']['total_tests']}")
        print(f"- Testes aprovados: {report['summary']['passed_tests']}")
        print(f"- Sucesso geral: {'SIM' if report['summary']['overall_success'] else 'NÃO'}")
        
        if '150gb_estimation' in report['test_results']:
            est = report['test_results']['150gb_estimation']
            print(f"\nEstimativa para 150GB:")
            print(f"- Tempo estimado: {est['estimated_time_minutes']:.1f} minutos")
            print(f"- Atende meta: {'SIM' if est['meets_target'] else 'NÃO'}")
        
        if report['recommendations']:
            print(f"\nRecomendações:")
            for rec in report['recommendations']:
                print(f"- {rec}")
        
        print("\n" + "="*80)
        
        return report
        
    except Exception as e:
        print(f"Erro na execução dos testes: {e}")
        return None
    
    finally:
        spark.stop()


if __name__ == "__main__":
    main()

