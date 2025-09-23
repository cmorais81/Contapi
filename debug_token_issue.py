#!/usr/bin/env python3
"""
Debug específico para problemas de token OAuth2
"""

import os
import sys
import json
import requests
import base64
import logging

def debug_token_issue():
    """Debug do problema de token"""
    
    print("=" * 80)
    print("DEBUG: PROBLEMA DE TOKEN OAUTH2")
    print("=" * 80)
    
    # Verificar credenciais
    client_id = os.getenv('LUZIA_CLIENT_ID')
    client_secret = os.getenv('LUZIA_CLIENT_SECRET')
    
    print("1. VERIFICAÇÃO DE CREDENCIAIS")
    print("-" * 50)
    
    if not client_id:
        print("❌ LUZIA_CLIENT_ID não definido")
        print("   Execute: export LUZIA_CLIENT_ID='seu_client_id'")
        return False
    
    if not client_secret:
        print("❌ LUZIA_CLIENT_SECRET não definido")
        print("   Execute: export LUZIA_CLIENT_SECRET='seu_client_secret'")
        return False
    
    print(f"✅ LUZIA_CLIENT_ID: {client_id[:10]}...{client_id[-5:]}")
    print(f"✅ LUZIA_CLIENT_SECRET: {client_secret[:5]}...{client_secret[-3:]}")
    
    print("\n2. TESTE DE AUTENTICAÇÃO OAUTH2")
    print("-" * 50)
    
    auth_url = "https://login.azure.paas.santanderbr.pre.corp/auth/realms/santander/protocol/openid-connect/token"
    
    # Payload exato do teste.py
    request_body = {
        "grant_type": "client_credentials",
        "client_id": client_id,
        "client_secret": client_secret
    }
    
    # Headers exatos do teste.py
    headers = {
        'Content-Type': 'application/x-www-form-urlencoded',
        'Accept': '*/*'
    }
    
    print("URL de autenticação:")
    print(f"  {auth_url}")
    
    print("\nPayload de autenticação:")
    print(f"  grant_type: {request_body['grant_type']}")
    print(f"  client_id: {request_body['client_id'][:10]}...{request_body['client_id'][-5:]}")
    print(f"  client_secret: {request_body['client_secret'][:5]}...{request_body['client_secret'][-3:]}")
    
    print("\nHeaders de autenticação:")
    print(json.dumps(headers, indent=2))
    
    try:
        print("\n📤 Fazendo requisição OAuth2...")
        
        response = requests.post(
            auth_url,
            headers=headers,
            data=request_body,  # Usar 'data' não 'json'
            verify=False,
            timeout=30
        )
        
        print(f"Status Code: {response.status_code}")
        print(f"Headers de resposta: {dict(response.headers)}")
        
        if response.status_code == 200:
            print("✅ Autenticação bem-sucedida!")
            
            token_data = response.json()
            print("\nDados do token:")
            print(json.dumps(token_data, indent=2))
            
            access_token = token_data.get('access_token')
            if access_token:
                print(f"\n🔑 Access Token obtido:")
                print(f"   Tamanho: {len(access_token)} chars")
                print(f"   Início: {access_token[:20]}...")
                print(f"   Fim: ...{access_token[-20:]}")
                
                # Verificar se é JWT
                if access_token.count('.') == 2:
                    print("   Formato: JWT (3 partes)")
                    parts = access_token.split('.')
                    
                    # Decodificar header JWT
                    try:
                        header_padding = parts[0] + '=' * (4 - len(parts[0]) % 4)
                        header_decoded = base64.urlsafe_b64decode(header_padding)
                        header_json = json.loads(header_decoded)
                        print(f"   JWT Header: {header_json}")
                    except Exception as e:
                        print(f"   Erro ao decodificar JWT header: {e}")
                
                else:
                    print("   Formato: Token opaco (não JWT)")
                
                # Testar o token na API
                print("\n3. TESTE DO TOKEN NA API")
                print("-" * 50)
                
                api_url = "https://gut-api-aws.santanderbr.dev.corp/genai_services/v1/pipelines/submit"
                
                # Payload de teste simples
                test_payload = {
                    "input": {
                        "query": [
                            {
                                "role": "system",
                                "content": "Answer all questions in brazilian portuguese."
                            },
                            {
                                "role": "user",
                                "content": "Diga apenas 'teste ok'"
                            }
                        ]
                    },
                    "config": {
                        "type": "catena.llm.LLMRouter",
                        "obj_kwargs": {
                            "routing_model": "azure-gpt-4o-mini",
                            "temperature": 0.1
                        }
                    }
                }
                
                # Headers para API
                api_headers = {
                    "X-santander-client-id": client_id,
                    "Authorization": f"Bearer {access_token}"
                }
                
                print("URL da API:")
                print(f"  {api_url}")
                
                print("\nHeaders da API:")
                print(f"  X-santander-client-id: {client_id[:10]}...{client_id[-5:]}")
                print(f"  Authorization: Bearer {access_token[:20]}...{access_token[-10:]}")
                
                print("\nPayload da API:")
                print(json.dumps(test_payload, indent=2, ensure_ascii=False))
                
                print("\n📤 Testando API...")
                
                api_response = requests.post(
                    api_url,
                    headers=api_headers,
                    json=test_payload,
                    verify=False,
                    timeout=30
                )
                
                print(f"Status Code: {api_response.status_code}")
                print(f"Headers de resposta: {dict(api_response.headers)}")
                print(f"Resposta: {api_response.text[:500]}...")
                
                if api_response.status_code == 200:
                    print("✅ API funcionando corretamente!")
                    return True
                elif api_response.status_code == 403:
                    print("❌ Erro 403 - Problema de autorização")
                    
                    # Analisar resposta de erro
                    try:
                        error_data = api_response.json()
                        print("Detalhes do erro:")
                        print(json.dumps(error_data, indent=2))
                    except:
                        print(f"Texto do erro: {api_response.text}")
                    
                    return False
                else:
                    print(f"❌ Erro {api_response.status_code}")
                    print(f"Resposta: {api_response.text}")
                    return False
            else:
                print("❌ Access token não encontrado na resposta")
                return False
        else:
            print(f"❌ Erro na autenticação: {response.status_code}")
            print(f"Resposta: {response.text}")
            return False
            
    except Exception as e:
        print(f"❌ Exceção durante teste: {e}")
        import traceback
        traceback.print_exc()
        return False

if __name__ == "__main__":
    success = debug_token_issue()
    
    print("\n" + "=" * 80)
    if success:
        print("✅ TOKEN E API FUNCIONANDO!")
        print("O problema pode estar na implementação do provider")
    else:
        print("❌ PROBLEMA IDENTIFICADO!")
        print("Verifique credenciais e conectividade")
    print("=" * 80)
