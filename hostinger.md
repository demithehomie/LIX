# 🚀 Deploy FastAPI na Hostinger

## 📋 Pré-requisitos
- Conta Hostinger com suporte Python
- Acesso via SSH ou File Manager
- Python 3.8+ disponível

## 📁 Estrutura de Arquivos

```
projeto/
├── main.py                 # Sua API FastAPI
├── requirements.txt        # Dependências
├── passenger_wsgi.py      # Configuração Hostinger
├── .htaccess              # Reescrita de URLs
└── public/                # Arquivos estáticos (opcional)
```

## 📄 Arquivos de Configuração

### requirements.txt
```
fastapi==0.104.1
uvicorn[standard]==0.24.0
httpx==0.25.2
python-multipart==0.0.6
gunicorn==21.2.0
```

### passenger_wsgi.py
```python
#!/usr/bin/env python3
import sys
import os

# Adicionar o diretório do projeto ao path
sys.path.insert(0, os.path.dirname(__file__))

# Importar a aplicação FastAPI
from main import app

# Configuração para Passenger (usado pela Hostinger)
application = app

# Se estiver usando gunicorn localmente para testes
if __name__ == "__main__":
    import uvicorn
    uvicorn.run(app, host="0.0.0.0", port=8000)
```

### .htaccess
```apache
RewriteEngine On
RewriteCond %{REQUEST_FILENAME} !-f
RewriteCond %{REQUEST_FILENAME} !-d
RewriteRule ^(.*)$ passenger_wsgi.py/$1 [QSA,L]

# Headers para CORS (se necessário)
Header always set Access-Control-Allow-Origin "*"
Header always set Access-Control-Allow-Methods "GET, POST, PUT, DELETE, OPTIONS"
Header always set Access-Control-Allow-Headers "Content-Type, Authorization"

# Cache para arquivos estáticos
<FilesMatch "\.(js|css|png|jpg|jpeg|gif|ico|svg)$">
    ExpiresActive On
    ExpiresDefault "access plus 1 month"
</FilesMatch>
```

## 🔧 Passos do Deploy

### 1. Preparar Arquivos Localmente
```bash
# Criar requirements.txt
pip freeze > requirements.txt

# Criar passenger_wsgi.py (use o código acima)
# Criar .htaccess (use o código acima)
```

### 2. Upload via File Manager ou FTP
- Faça upload de todos os arquivos para a pasta `public_html` (ou subpasta)
- Estrutura final na Hostinger:
```
public_html/
├── main.py
├── passenger_wsgi.py  
├── .htaccess
└── requirements.txt
```

### 3. Instalar Dependências (via SSH)
```bash
# Conectar via SSH
ssh seu-usuario@seu-dominio.com

# Ir para o diretório
cd public_html

# Instalar dependências
pip3 install --user -r requirements.txt

# Ou se tiver problemas de permissão:
python3 -m pip install --user -r requirements.txt
```

### 4. Configurar Domínio/Subdomínio
- Aponte seu domínio para a pasta onde estão os arquivos
- Exemplo: `api.seudominio.com` → `/public_html/`

### 5. Testar
- Acesse: `https://seudominio.com/`
- Documentação: `https://seudominio.com/docs`

## ⚠️ Possíveis Problemas e Soluções

### Problema: "ModuleNotFoundError"
**Solução:**
```bash
# Verificar versão do Python
python3 --version

# Instalar com usuário específico
pip3 install --user fastapi uvicorn httpx
```

### Problema: "Permission Denied" 
**Solução:**
```bash
# Dar permissões corretas
chmod 644 main.py passenger_wsgi.py .htaccess
chmod 755 public_html
```

### Problema: API não responde
**Solução:**
1. Verificar logs da Hostinger
2. Testar o `passenger_wsgi.py` diretamente
3. Verificar se o `.htaccess` está funcionando

### Problema: CORS errors
**Solução:**
Adicionar no `main.py`:
```python
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],  # ou seu domínio específico
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)
```

## 🔄 Deploy Alternativo: Via Git

Se a Hostinger suportar Git:

```bash
# No servidor
git clone https://github.com/seu-usuario/api-licitacoes.git
cd api-licitacoes
pip3 install --user -r requirements.txt
```

## 📊 Monitoramento

### Log de Erros
```bash
# Ver logs (se disponível via SSH)
tail -f /path/to/passenger.log
tail -f /path/to/error.log
```

### Teste de Saúde
Adicionar endpoint de health check no `main.py`:
```python
@app.get("/health")
async def health_check():
    return {
        "status": "healthy",
        "timestamp": datetime.now(),
        "version": "1.0.0"
    }
```

## 📱 URLs Finais

Após o deploy, suas URLs serão:
- **API Base**: `https://seudominio.com/`
- **Docs**: `https://seudominio.com/docs`
- **Licitações PNCP**: `https://seudominio.com/licitacoes/pncp`
- **Health Check**: `https://seudominio.com/health`

## 💡 Dicas Importantes

1. **Performance**: Para produção, considere usar Gunicorn em vez do uvicorn básico
2. **Cache**: Implemente cache Redis/Memcached se a Hostinger suportar
3. **Rate Limiting**: Adicione rate limiting para proteger a API
4. **SSL**: Certifique-se de que SSL está ativo na Hostinger
5. **Backup**: Sempre tenha backup dos dados e configurações

## 🆘 Suporte

Se tiver problemas:
1. Verificar documentação da Hostinger sobre Python/WSGI
2. Contatar suporte técnico da Hostinger
3. Verificar logs de erro do servidor
4. Testar localmente antes do deploy
