# Comandos Manuais - TBR GDP Core Data Governance API v2.1

**Versão:** 2.1 Definitiva  
**Data:** 07 de Janeiro de 2025  
**Desenvolvido por:** Carlos Morais  

## 🚀 COMANDOS PARA EXECUTAR A APLICAÇÃO

### 📋 **PRÉ-REQUISITOS**
- ✅ Python 3.11+ instalado
- ✅ pip funcionando
- ✅ Windows 11 (testado)

### 📁 **ESTRUTURA DO PROJETO**
```
tbr-gdpcore-dtgovapi/
├── src/                    # Código fonte
│   ├── main.py            # Arquivo principal
│   ├── api/               # Controllers e rotas
│   ├── database/          # Modelos e conexão
│   └── config/            # Configurações
├── requirements.txt       # Dependências
├── .env.example          # Exemplo de configuração
└── scripts/windows/      # Scripts PowerShell
```

## ⚡ **COMANDOS MANUAIS SIMPLES**

### **1. INSTALAÇÃO DAS DEPENDÊNCIAS**
```bash
# Navegar para o diretório do projeto
cd tbr-gdpcore-dtgovapi

# Instalar dependências
pip install -r requirements.txt
```

### **2. CONFIGURAÇÃO DO AMBIENTE**
```bash
# Copiar arquivo de exemplo
copy .env.example .env

# Editar .env conforme necessário (opcional para teste local)
```

### **3. EXECUTAR A APLICAÇÃO**

#### **Opção A: Do diretório RAIZ (Recomendado)**
```bash
# Se você está no diretório onde vê a pasta 'src/'
uvicorn main:app --host 0.0.0.0 --port 8000 --reload --app-dir src
```

#### **Opção B: De DENTRO da pasta src/**
```bash
# Primeiro navegar para src/
cd src

# Depois executar
uvicorn main:app --host 0.0.0.0 --port 8000 --reload
```

### **4. VERIFICAR SE ESTÁ FUNCIONANDO**
```bash
# Testar health check
curl http://localhost:8000/health

# Ou abrir no navegador:
# http://localhost:8000/health
```

## 🌐 **URLs IMPORTANTES**

Após executar a aplicação, acesse:

- **🏠 Página Principal:** http://localhost:8000/
- **❤️ Health Check:** http://localhost:8000/health
- **📊 Métricas:** http://localhost:8000/metrics
- **📚 Documentação Swagger:** http://localhost:8000/docs
- **📖 Documentação ReDoc:** http://localhost:8000/redoc
- **🔧 OpenAPI Spec:** http://localhost:8000/openapi.json

## ❌ **COMANDOS QUE CAUSAM ERRO**

### **NÃO USAR quando estiver dentro de src/:**
```bash
# ❌ ERRO! Não funciona quando já está em src/:
uvicorn src.main:app --host 0.0.0.0 --port 8000 --reload
```

**Por quê?** O Python procura por um módulo `src` quando já está dentro do diretório `src/`.

## 🔍 **COMO SABER EM QUAL DIRETÓRIO ESTOU?**

### **Windows (PowerShell/CMD):**
```powershell
# Ver conteúdo do diretório atual
dir

# Se você vê a pasta 'src' listada = está no diretório RAIZ
# Se você vê o arquivo 'main.py' listado = está dentro de src/
```

### **Linux/Mac (se aplicável):**
```bash
# Ver conteúdo do diretório atual
ls

# Se você vê a pasta 'src' listada = está no diretório RAIZ  
# Se você vê o arquivo 'main.py' listado = está dentro de src/
```

## 🛠️ **TROUBLESHOOTING**

### **Problema: ModuleNotFoundError: No module named 'src'**
**Solução:** Você está executando o comando errado. Use:
- Do diretório raiz: `uvicorn main:app --host 0.0.0.0 --port 8000 --reload --app-dir src`
- De dentro de src/: `uvicorn main:app --host 0.0.0.0 --port 8000 --reload`

### **Problema: Porta já em uso**
**Solução:** Mude a porta:
```bash
uvicorn main:app --host 0.0.0.0 --port 8001 --reload --app-dir src
```

### **Problema: Dependências não instaladas**
**Solução:** Instale as dependências:
```bash
pip install -r requirements.txt
```

### **Problema: Python não encontrado**
**Solução:** Verifique se Python está no PATH:
```bash
python --version
# ou
python3 --version
```

## 📋 **RESUMO DOS COMANDOS ESSENCIAIS**

```bash
# 1. Instalar dependências
pip install -r requirements.txt

# 2. Executar aplicação (do diretório raiz)
uvicorn main:app --host 0.0.0.0 --port 8000 --reload --app-dir src

# 3. Testar se funcionou
curl http://localhost:8000/health
```

## 🎯 **RESULTADO ESPERADO**

Quando a aplicação estiver rodando, você verá:

```
INFO:     Uvicorn running on http://0.0.0.0:8000 (Press CTRL+C to quit)
INFO:     Started reloader process [XXXX] using StatReload
INFO:     Started server process [XXXX]
INFO:     Waiting for application startup.
INFO:     Application startup complete.
```

E o health check retornará:
```json
{
  "status": "healthy",
  "timestamp": "2025-01-07T10:00:00Z",
  "version": "2.1.0",
  "environment": "development",
  "developer": "Carlos Morais"
}
```

## 🏆 **PRONTO!**

Sua **TBR GDP Core Data Governance API v2.1** está rodando e pronta para uso!

---

**Desenvolvido por Carlos Morais - Janeiro 2025**

