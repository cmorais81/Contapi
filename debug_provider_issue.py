#!/usr/bin/env python3
"""
Debug do problema com provider manager
"""

import os
import sys
import logging

# Adicionar src ao path
sys.path.insert(0, os.path.join(os.path.dirname(__file__), 'src'))

def debug_provider_issue():
    """Debug do problema com providers"""
    
    print("=" * 60)
    print("DEBUG DO PROBLEMA COM PROVIDER MANAGER")
    print("=" * 60)
    
    try:
        # Configurar logging
        logging.basicConfig(level=logging.INFO)
        
        # Importar configuração
        from src.core.config import ConfigManager
        
        print("1. Carregando configuração...")
        config_manager = ConfigManager()
        config = config_manager.config
        
        print(f"   Primary provider: {config.get('ai', {}).get('primary_provider')}")
        print(f"   Fallback providers: {config.get('ai', {}).get('fallback_providers')}")
        
        # Verificar providers configurados
        providers_config = config.get('providers', {})
        print(f"   Providers configurados: {list(providers_config.keys())}")
        
        for provider_name, provider_config in providers_config.items():
            enabled = provider_config.get('enabled', False)
            print(f"   - {provider_name}: {'Habilitado' if enabled else 'Desabilitado'}")
        
        print()
        print("2. Inicializando Provider Manager...")
        
        # Importar provider manager
        from src.providers.enhanced_provider_manager import EnhancedProviderManager
        
        provider_manager = EnhancedProviderManager(config)
        
        print(f"   Providers inicializados: {list(provider_manager.providers.keys())}")
        print(f"   Primary provider configurado: {provider_manager.primary_provider}")
        print(f"   Fallback providers: {provider_manager.fallback_providers}")
        
        print()
        print("3. Verificando disponibilidade...")
        
        available_providers = provider_manager.get_available_providers()
        print(f"   Providers disponíveis: {available_providers}")
        
        for provider_name in provider_manager.providers.keys():
            try:
                status = provider_manager.get_provider_status(provider_name)
                print(f"   - {provider_name}: {status}")
            except Exception as e:
                print(f"   - {provider_name}: ERRO - {e}")
        
        print()
        print("4. Verificando credenciais LuzIA...")
        
        client_id = os.getenv('LUZIA_CLIENT_ID')
        client_secret = os.getenv('LUZIA_CLIENT_SECRET')
        
        print(f"   LUZIA_CLIENT_ID: {'Definido' if client_id else 'NÃO DEFINIDO'}")
        print(f"   LUZIA_CLIENT_SECRET: {'Definido' if client_secret else 'NÃO DEFINIDO'}")
        
        if client_id and client_secret:
            print(f"   Client ID: {client_id[:10]}...{client_id[-5:]}")
        
        print()
        print("5. Testando provider LuzIA diretamente...")
        
        if 'luzia' in provider_manager.providers:
            luzia_provider = provider_manager.providers['luzia']
            print(f"   Provider LuzIA encontrado: {type(luzia_provider)}")
            
            try:
                available = luzia_provider.is_available()
                print(f"   Disponível: {available}")
                
                if available:
                    models = luzia_provider.get_models()
                    print(f"   Modelos: {models}")
                    
                    status = luzia_provider.get_status()
                    print(f"   Status: {status}")
                else:
                    print("   Provider não disponível - verificar credenciais")
                    
            except Exception as e:
                print(f"   ERRO ao verificar provider: {e}")
                import traceback
                traceback.print_exc()
        else:
            print("   Provider LuzIA NÃO ENCONTRADO!")
            print("   Isso explica o erro 'luzia' got an unexpected keyword argument")
        
        print()
        print("6. Diagnóstico...")
        
        if provider_manager.primary_provider not in provider_manager.providers:
            print(f"   PROBLEMA: Provider primário '{provider_manager.primary_provider}' não foi inicializado")
            print("   CAUSA: Provavelmente credenciais não definidas ou erro na inicialização")
            print("   SOLUÇÃO: Verificar credenciais e logs de inicialização")
        else:
            print(f"   OK: Provider primário '{provider_manager.primary_provider}' inicializado")
        
        return True
        
    except Exception as e:
        print(f"ERRO durante debug: {e}")
        import traceback
        traceback.print_exc()
        return False

if __name__ == "__main__":
    debug_provider_issue()
