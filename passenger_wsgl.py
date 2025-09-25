#!/usr/bin/env python3
"""
Arquivo de configuração para deploy na Hostinger
Este arquivo é necessário para que o Passenger (usado pela Hostinger) rode sua aplicação FastAPI
"""

import sys
import os

# Adicionar o diretório atual ao Python path
current_dir = os.path.dirname(os.path.abspath(__file__))
sys.path.insert(0, current_dir)

try:
    # Importar a aplicação FastAPI
    from main import app
    
    # Esta é a aplicação que o Passenger irá usar
    application = app
    
    print("✅ FastAPI app carregada com sucesso!")
    
except ImportError as e:
    print(f"❌ Erro ao importar a aplicação: {e}")
    
    # Criar uma aplicação básica em caso de erro
    from fastapi import FastAPI
    from fastapi.responses import JSONResponse
    
    app = FastAPI(title="API Error")
    
    @app.get("/")
    async def error_root():
        return JSONResponse(
            status_code=500,
            content={
                "error": "Erro na importação da aplicação",
                "message": str(e),
                "suggestion": "Verifique se todas as dependências estão instaladas"
            }
        )
    
    application = app

# Para desenvolvimento local (opcional)
if __name__ == "__main__":
    import uvicorn
    print("🚀 Rodando em modo desenvolvimento...")
    uvicorn.run(application, host="0.0.0.0", port=8000, reload=True)
