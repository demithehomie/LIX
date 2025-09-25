from fastapi import FastAPI, Query, HTTPException, Depends
from fastapi.middleware.cors import CORSMiddleware
from typing import List, Optional, Dict, Any
from pydantic import BaseModel, Field
from datetime import datetime, date
from enum import Enum
import json
import httpx
import asyncio
from urllib.parse import urlencode

# Configurações das APIs governamentais
PNCP_BASE_URL = "https://pncp.gov.br/api/pncp/v1"
TRANSPARENCIA_BASE_URL = "https://api.portaldatransparencia.gov.br/api-de-dados"

# Modelos de dados
class TipoLicitacao(str, Enum):
    CONVITE = "convite"
    TOMADA_PRECOS = "tomada_precos"
    CONCORRENCIA = "concorrencia"
    PREGAO = "pregao"
    CONCURSO = "concurso"
    LEILAO = "leilao"
    RDC = "rdc"
    CONSULTA_PUBLICA = "consulta_publica"

class StatusLicitacao(str, Enum):
    ABERTA = "aberta"
    EM_ANDAMENTO = "em_andamento"
    ENCERRADA = "encerrada"
    SUSPENSA = "suspensa"
    CANCELADA = "cancelada"

class UF(str, Enum):
    AC = "AC"
    AL = "AL" 
    AP = "AP"
    AM = "AM"
    BA = "BA"
    CE = "CE"
    DF = "DF"
    ES = "ES"
    GO = "GO"
    MA = "MA"
    MT = "MT"
    MS = "MS"
    MG = "MG"
    PA = "PA"
    PB = "PB"
    PR = "PR"
    PE = "PE"
    PI = "PI"
    RJ = "RJ"
    RN = "RN"
    RS = "RS"
    RO = "RO"
    RR = "RR"
    SC = "SC"
    SP = "SP"
    SE = "SE"
    TO = "TO"

class LicitacaoBase(BaseModel):
    numero: str = Field(..., description="Número da licitação")
    tipo: TipoLicitacao = Field(..., description="Tipo da licitação")
    objeto: str = Field(..., description="Objeto da licitação")
    orgao: str = Field(..., description="Órgão responsável")
    status: StatusLicitacao = Field(..., description="Status atual")
    valor_estimado: Optional[float] = Field(None, description="Valor estimado em R$")
    data_abertura: date = Field(..., description="Data de abertura")
    data_encerramento: Optional[date] = Field(None, description="Data de encerramento")
    uf: UF = Field(..., description="Estado")
    cidade: str = Field(..., description="Cidade")
    modalidade_participacao: Optional[str] = Field(None, description="Modalidade de participação")
    link_edital: Optional[str] = Field(None, description="Link para o edital")

class LicitacaoResponse(LicitacaoBase):
    id: int = Field(..., description="ID único da licitação")
    created_at: datetime = Field(..., description="Data de criação do registro")
    updated_at: datetime = Field(..., description="Data de atualização do registro")

class FiltrosLicitacao(BaseModel):
    tipos: Optional[List[TipoLicitacao]] = None
    status: Optional[List[StatusLicitacao]] = None
    ufs: Optional[List[UF]] = None
    cidades: Optional[List[str]] = None
    valor_min: Optional[float] = None
    valor_max: Optional[float] = None
    data_abertura_inicio: Optional[date] = None
    data_abertura_fim: Optional[date] = None
    texto_busca: Optional[str] = None

# Serviços de integração com APIs governamentais
class LicitacaoService:
    def __init__(self):
        self.pncp_base_url = PNCP_BASE_URL
        self.transparencia_base_url = TRANSPARENCIA_BASE_URL
        
    async def buscar_licitacoes_pncp(
        self,
        cnpj_orgao: Optional[str] = None,
        data_inicio: Optional[str] = None,
        data_fim: Optional[str] = None,
        modalidade: Optional[str] = None,
        pagina: int = 1,
        tam_pagina: int = 100
    ) -> Dict[str, Any]:
        """
        Buscar licitações no PNCP (Portal Nacional de Contratações Públicas)
        """
        try:
            params = {
                "pagina": pagina,
                "tamanhoPagina": tam_pagina
            }
            
            if cnpj_orgao:
                params["cnpjOrgao"] = cnpj_orgao
            if data_inicio:
                params["dataInicial"] = data_inicio  # formato: YYYY-MM-DD
            if data_fim:
                params["dataFinal"] = data_fim
            if modalidade:
                params["modalidadeContratacao"] = modalidade
            
            url = f"{self.pncp_base_url}/orgaos/{cnpj_orgao}/licitacoes" if cnpj_orgao else f"{self.pncp_base_url}/licitacoes"
            
            async with httpx.AsyncClient(timeout=30.0) as client:
                response = await client.get(url, params=params)
                
                if response.status_code == 200:
                    return response.json()
                else:
                    print(f"Erro na API PNCP: {response.status_code}")
                    return {"data": [], "totalElements": 0}
                    
        except Exception as e:
            print(f"Erro ao buscar dados do PNCP: {str(e)}")
            return {"data": [], "totalElements": 0}

    async def listar_orgaos_pncp(self, pagina: int = 1, tamanho_pagina: int = 50):
        url = f"{self.pncp_base_url}/orgaos"
        params = {"pagina": pagina, "tamanhoPagina": tamanho_pagina}

        async with httpx.AsyncClient(timeout=30.0) as client:
            response = await client.get(url, params=params)

            if response.status_code == 200:
                return response.json()
            else:
                print(f"Erro ao buscar órgãos PNCP: {response.status_code}")
                return {"data": [], "totalElements": 0}
    
    async def buscar_licitacoes_transparencia(
        self,
        codigo_orgao: Optional[str] = None,
        data_inicio: Optional[str] = None,
        data_fim: Optional[str] = None,
        pagina: int = 1
    ) -> Dict[str, Any]:
        """
        Buscar licitações no Portal da Transparência
        """
        try:
            params = {"pagina": pagina}
            
            if codigo_orgao:
                params["codigoOrgao"] = codigo_orgao
            if data_inicio:
                params["dataInicial"] = data_inicio
            if data_fim:
                params["dataFinal"] = data_fim
            
            url = f"{self.transparencia_base_url}/licitacoes"
            
            # Nota: API da Transparência pode requerer chave de acesso
            headers = {
                "Accept": "application/json",
                "User-Agent": "API-Licitacoes/1.0"
            }
            
            async with httpx.AsyncClient(timeout=30.0) as client:
                response = await client.get(url, params=params, headers=headers)
                
                if response.status_code == 200:
                    return response.json()
                else:
                    print(f"Erro na API Transparência: {response.status_code}")
                    return []
                    
        except Exception as e:
            print(f"Erro ao buscar dados da Transparência: {str(e)}")
            return []
    
    def normalizar_dados_pncp(self, dados_pncp: Dict) -> List[Dict]:
        """
        Normalizar dados do PNCP para o formato padrão da API
        """
        licitacoes_normalizadas = []
        
        for item in dados_pncp.get("data", []):
            try:
                licitacao = {
                    "id": item.get("sequencialLicitacao", 0),
                    "numero": item.get("numeroLicitacao", ""),
                    "tipo": self.mapear_tipo_pncp(item.get("modalidadeContratacao", "")),
                    "objeto": item.get("objetoLicitacao", ""),
                    "orgao": item.get("nomeOrgao", ""),
                    "status": self.mapear_status_pncp(item.get("situacaoLicitacao", "")),
                    "valor_estimado": item.get("valorEstimado", 0),
                    "data_abertura": item.get("dataAbertura", ""),
                    "data_encerramento": item.get("dataEncerramento"),
                    "uf": item.get("ufOrgao", ""),
                    "cidade": item.get("cidadeOrgao", ""),
                    "modalidade_participacao": item.get("modalidadeContratacao", ""),
                    "link_edital": item.get("linkEdital"),
                    "created_at": datetime.now(),
                    "updated_at": datetime.now()
                }
                licitacoes_normalizadas.append(licitacao)
            except Exception as e:
                print(f"Erro ao normalizar item: {str(e)}")
                continue
                
        return licitacoes_normalizadas
    
    def mapear_tipo_pncp(self, modalidade: str) -> TipoLicitacao:
        """
        Mapear modalidades do PNCP para enum interno
        """
        mapeamento = {
            "PREGAO": TipoLicitacao.PREGAO,
            "CONCORRENCIA": TipoLicitacao.CONCORRENCIA,
            "TOMADA_PRECOS": TipoLicitacao.TOMADA_PRECOS,
            "CONVITE": TipoLicitacao.CONVITE,
            "RDC": TipoLicitacao.RDC,
            "CONCURSO": TipoLicitacao.CONCURSO,
            "LEILAO": TipoLicitacao.LEILAO
        }
        return mapeamento.get(modalidade.upper(), TipoLicitacao.PREGAO)
    
    def mapear_status_pncp(self, situacao: str) -> StatusLicitacao:
        """
        Mapear situações do PNCP para enum interno
        """
        mapeamento = {
            "ABERTA": StatusLicitacao.ABERTA,
            "EM_ANDAMENTO": StatusLicitacao.EM_ANDAMENTO,
            "ENCERRADA": StatusLicitacao.ENCERRADA,
            "SUSPENSA": StatusLicitacao.SUSPENSA,
            "CANCELADA": StatusLicitacao.CANCELADA
        }
        return mapeamento.get(situacao.upper(), StatusLicitacao.ABERTA)

# Instância do serviço
licitacao_service = LicitacaoService()
MOCK_LICITACOES = [
    {
        "id": 1,
        "numero": "001/2024",
        "tipo": TipoLicitacao.PREGAO,
        "objeto": "Aquisição de equipamentos de informática",
        "orgao": "Prefeitura Municipal de São Paulo",
        "status": StatusLicitacao.ABERTA,
        "valor_estimado": 150000.00,
        "data_abertura": date(2024, 10, 15),
        "data_encerramento": date(2024, 11, 15),
        "uf": UF.SP,
        "cidade": "São Paulo",
        "modalidade_participacao": "Presencial/Online",
        "link_edital": "https://exemplo.com/edital1",
        "created_at": datetime.now(),
        "updated_at": datetime.now()
    },
    {
        "id": 2,
        "numero": "002/2024",
        "tipo": TipoLicitacao.CONCORRENCIA,
        "objeto": "Construção de escola municipal",
        "orgao": "Governo do Estado do Rio de Janeiro",
        "status": StatusLicitacao.EM_ANDAMENTO,
        "valor_estimado": 2500000.00,
        "data_abertura": date(2024, 9, 20),
        "data_encerramento": date(2024, 12, 20),
        "uf": UF.RJ,
        "cidade": "Rio de Janeiro",
        "modalidade_participacao": "Presencial",
        "link_edital": "https://exemplo.com/edital2",
        "created_at": datetime.now(),
        "updated_at": datetime.now()
    },
    {
        "id": 3,
        "numero": "003/2024",
        "tipo": TipoLicitacao.TOMADA_PRECOS,
        "objeto": "Serviços de limpeza urbana",
        "orgao": "Prefeitura de Brasília",
        "status": StatusLicitacao.ABERTA,
        "valor_estimado": 800000.00,
        "data_abertura": date(2024, 10, 10),
        "data_encerramento": date(2024, 11, 30),
        "uf": UF.DF,
        "cidade": "Brasília",
        "modalidade_participacao": "Online",
        "link_edital": "https://exemplo.com/edital3",
        "created_at": datetime.now(),
        "updated_at": datetime.now()
    },
    {
        "id": 4,
        "numero": "004/2024",
        "tipo": TipoLicitacao.PREGAO,
        "objeto": "Aquisição de medicamentos",
        "orgao": "Hospital Regional de Salvador",
        "status": StatusLicitacao.ABERTA,
        "valor_estimado": 500000.00,
        "data_abertura": date(2024, 10, 25),
        "data_encerramento": date(2024, 12, 15),
        "uf": UF.BA,
        "cidade": "Salvador",
        "modalidade_participacao": "Online",
        "link_edital": "https://exemplo.com/edital4",
        "created_at": datetime.now(),
        "updated_at": datetime.now()
    },
    {
        "id": 5,
        "numero": "005/2024",
        "tipo": TipoLicitacao.RDC,
        "objeto": "Construção de ponte",
        "orgao": "DNIT - Departamento Nacional de Infraestrutura",
        "status": StatusLicitacao.ENCERRADA,
        "valor_estimado": 15000000.00,
        "data_abertura": date(2024, 8, 1),
        "data_encerramento": date(2024, 9, 30),
        "uf": UF.MG,
        "cidade": "Belo Horizonte",
        "modalidade_participacao": "Presencial",
        "link_edital": "https://exemplo.com/edital5",
        "created_at": datetime.now(),
        "updated_at": datetime.now()
    }
]

# Inicialização da API
app = FastAPI(
    title="API de Licitações",
    description="API para consulta de licitações com filtros por tipo e localização",
    version="1.0.0",
    docs_url="/docs",
    redoc_url="/redoc"
)

# CORS
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Funções auxiliares
def filtrar_licitacoes(
    licitacoes: List[Dict],
    tipos: Optional[List[TipoLicitacao]] = None,
    status: Optional[List[StatusLicitacao]] = None,
    ufs: Optional[List[UF]] = None,
    cidades: Optional[List[str]] = None,
    valor_min: Optional[float] = None,
    valor_max: Optional[float] = None,
    data_abertura_inicio: Optional[date] = None,
    data_abertura_fim: Optional[date] = None,
    texto_busca: Optional[str] = None,
    limite: int = 100,
    offset: int = 0
) -> List[Dict]:
    
    resultado = licitacoes.copy()
    
    # Filtro por tipos
    if tipos:
        resultado = [l for l in resultado if l["tipo"] in tipos]
    
    # Filtro por status
    if status:
        resultado = [l for l in resultado if l["status"] in status]
    
    # Filtro por UF
    if ufs:
        resultado = [l for l in resultado if l["uf"] in ufs]
    
    # Filtro por cidades
    if cidades:
        cidades_lower = [c.lower() for c in cidades]
        resultado = [l for l in resultado if l["cidade"].lower() in cidades_lower]
    
    # Filtro por valor mínimo
    if valor_min is not None:
        resultado = [l for l in resultado if l.get("valor_estimado", 0) >= valor_min]
    
    # Filtro por valor máximo
    if valor_max is not None:
        resultado = [l for l in resultado if l.get("valor_estimado", float('inf')) <= valor_max]
    
    # Filtro por data de abertura início
    if data_abertura_inicio:
        resultado = [l for l in resultado if l["data_abertura"] >= data_abertura_inicio]
    
    # Filtro por data de abertura fim
    if data_abertura_fim:
        resultado = [l for l in resultado if l["data_abertura"] <= data_abertura_fim]
    
    # Busca textual
    if texto_busca:
        texto_lower = texto_busca.lower()
        resultado = [
            l for l in resultado 
            if texto_lower in l["objeto"].lower() 
            or texto_lower in l["orgao"].lower()
            or texto_lower in l["numero"].lower()
        ]
    
    # Paginação
    total = len(resultado)
    resultado = resultado[offset:offset + limite]
    
    return resultado, total

# Endpoints com integração a APIs governamentais

@app.get("/licitacoes/pncp", response_model=Dict[str, Any])
async def obter_licitacoes_pncp(
    cnpj_orgao: Optional[str] = Query(None, description="CNPJ do órgão"),
    data_inicio: Optional[date] = Query(None, description="Data início (YYYY-MM-DD)"),
    data_fim: Optional[date] = Query(None, description="Data fim (YYYY-MM-DD)"),
    modalidade: Optional[str] = Query(None, description="Modalidade de contratação"),
    pagina: int = Query(1, ge=1, description="Página"),
    tamanho_pagina: int = Query(100, ge=1, le=500, description="Tamanho da página")
):
    """
    Obter licitações diretamente do PNCP (Portal Nacional de Contratações Públicas).
    
    Esta rota busca dados em tempo real da API oficial do governo.
    """
    
    try:
        # Converter datas para string se fornecidas
        data_inicio_str = data_inicio.strftime("%Y-%m-%d") if data_inicio else None
        data_fim_str = data_fim.strftime("%Y-%m-%d") if data_fim else None
        
        # Buscar dados no PNCP
        dados_pncp = await licitacao_service.buscar_licitacoes_pncp(
            cnpj_orgao=cnpj_orgao,
            data_inicio=data_inicio_str,
            data_fim=data_fim_str,
            modalidade=modalidade,
            pagina=pagina,
            tam_pagina=tamanho_pagina
        )
        
        # Normalizar dados
        licitacoes_normalizadas = licitacao_service.normalizar_dados_pncp(dados_pncp)
        
        return {
            "fonte": "PNCP - Portal Nacional de Contratações Públicas",
            "dados": licitacoes_normalizadas,
            "total": dados_pncp.get("totalElements", 0),
            "pagina": pagina,
            "tamanho_pagina": tamanho_pagina,
            "parametros_busca": {
                "cnpj_orgao": cnpj_orgao,
                "data_inicio": data_inicio_str,
                "data_fim": data_fim_str,
                "modalidade": modalidade
            }
        }
        
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Erro ao consultar PNCP: {str(e)}")

@app.get("/licitacoes/transparencia", response_model=Dict[str, Any])
async def obter_licitacoes_transparencia(
    codigo_orgao: Optional[str] = Query(None, description="Código do órgão"),
    data_inicio: Optional[date] = Query(None, description="Data início (YYYY-MM-DD)"),
    data_fim: Optional[date] = Query(None, description="Data fim (YYYY-MM-DD)"),
    pagina: int = Query(1, ge=1, description="Página")
):
    """
    Obter licitações do Portal da Transparência do Governo Federal.
    
    Esta rota busca dados em tempo real da API oficial da transparência.
    """
    
    try:
        # Converter datas para string se fornecidas
        data_inicio_str = data_inicio.strftime("%d/%m/%Y") if data_inicio else None
        data_fim_str = data_fim.strftime("%d/%m/%Y") if data_fim else None
        
        # Buscar dados no Portal da Transparência
        dados_transparencia = await licitacao_service.buscar_licitacoes_transparencia(
            codigo_orgao=codigo_orgao,
            data_inicio=data_inicio_str,
            data_fim=data_fim_str,
            pagina=pagina
        )
        
        return {
            "fonte": "Portal da Transparência - Governo Federal",
            "dados": dados_transparencia,
            "total": len(dados_transparencia) if isinstance(dados_transparencia, list) else 0,
            "pagina": pagina,
            "parametros_busca": {
                "codigo_orgao": codigo_orgao,
                "data_inicio": data_inicio_str,
                "data_fim": data_fim_str
            }
        }
        
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Erro ao consultar Portal da Transparência: {str(e)}")

@app.get("/licitacoes/consolidado", response_model=Dict[str, Any])
async def obter_licitacoes_consolidado(
    # Filtros gerais
    data_inicio: Optional[date] = Query(None, description="Data início (YYYY-MM-DD)"),
    data_fim: Optional[date] = Query(None, description="Data fim (YYYY-MM-DD)"),
    
    # Filtros PNCP
    cnpj_orgao: Optional[str] = Query(None, description="CNPJ do órgão (PNCP)"),
    modalidade: Optional[str] = Query(None, description="Modalidade (PNCP)"),
    
    # Filtros Transparência
    codigo_orgao: Optional[str] = Query(None, description="Código do órgão (Transparência)"),
    
    # Controles
    incluir_pncp: bool = Query(True, description="Incluir dados do PNCP"),
    incluir_transparencia: bool = Query(False, description="Incluir dados da Transparência"),
    
    pagina: int = Query(1, ge=1, description="Página"),
    tamanho_pagina: int = Query(100, ge=1, le=500, description="Tamanho da página")
):
    """
    Obter licitações consolidadas de múltiplas fontes governamentais.
    
    Combina dados do PNCP e Portal da Transparência em uma única resposta.
    """
    
    try:
        resultados = {}
        dados_consolidados = []
        
        # Buscar no PNCP se solicitado
        if incluir_pncp:
            data_inicio_str = data_inicio.strftime("%Y-%m-%d") if data_inicio else None
            data_fim_str = data_fim.strftime("%Y-%m-%d") if data_fim else None
            
            dados_pncp = await licitacao_service.buscar_licitacoes_pncp(
                cnpj_orgao=cnpj_orgao,
                data_inicio=data_inicio_str,
                data_fim=data_fim_str,
                modalidade=modalidade,
                pagina=pagina,
                tam_pagina=tamanho_pagina
            )
            
            licitacoes_pncp = licitacao_service.normalizar_dados_pncp(dados_pncp)
            dados_consolidados.extend(licitacoes_pncp)
            
            resultados["pncp"] = {
                "total": dados_pncp.get("totalElements", 0),
                "recuperados": len(licitacoes_pncp)
            }
        
        # Buscar na Transparência se solicitado
        if incluir_transparencia:
            data_inicio_str = data_inicio.strftime("%d/%m/%Y") if data_inicio else None
            data_fim_str = data_fim.strftime("%d/%m/%Y") if data_fim else None
            
            dados_transparencia = await licitacao_service.buscar_licitacoes_transparencia(
                codigo_orgao=codigo_orgao,
                data_inicio=data_inicio_str,
                data_fim=data_fim_str,
                pagina=pagina
            )
            
            dados_consolidados.extend(dados_transparencia)
            
            resultados["transparencia"] = {
                "total": len(dados_transparencia) if isinstance(dados_transparencia, list) else 0,
                "recuperados": len(dados_transparencia) if isinstance(dados_transparencia, list) else 0
            }
        
        # Se nenhuma fonte foi solicitada, usar dados mock
        if not incluir_pncp and not incluir_transparencia:
            dados_consolidados = MOCK_LICITACOES
            resultados["mock"] = {
                "total": len(MOCK_LICITACOES),
                "recuperados": len(MOCK_LICITACOES)
            }
        
        return {
            "fonte": "Dados Consolidados",
            "fontes_consultadas": resultados,
            "dados": dados_consolidados,
            "total_consolidado": len(dados_consolidados),
            "configuracao": {
                "incluir_pncp": incluir_pncp,
                "incluir_transparencia": incluir_transparencia,
                "pagina": pagina,
                "tamanho_pagina": tamanho_pagina
            }
        }
        
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Erro na busca consolidada: {str(e)}")

@app.get("/")
async def root():
    return {
        "message": "API de Licitações - Bem-vindo!",
        "version": "1.0.0",
        "endpoints": {
            "licitacoes_mock": "/licitacoes",
            "licitacoes_pncp": "/licitacoes/pncp",
            "licitacoes_transparencia": "/licitacoes/transparencia", 
            "licitacoes_consolidado": "/licitacoes/consolidado",
            "tipos": "/tipos",
            "status": "/status",
            "ufs": "/ufs",
            "documentacao": "/docs"
        }
    }


@app.get("/licitacoes", response_model=Dict[str, Any])
async def obter_licitacoes(
    # Filtros por tipo
    tipos: Optional[List[TipoLicitacao]] = Query(None, description="Filtrar por tipos de licitação"),
    
    # Filtros por status
    status: Optional[List[StatusLicitacao]] = Query(None, description="Filtrar por status"),
    
    # Filtros geográficos
    ufs: Optional[List[UF]] = Query(None, description="Filtrar por estados (UF)"),
    cidades: Optional[List[str]] = Query(None, description="Filtrar por cidades"),
    
    # Filtros por valor
    valor_min: Optional[float] = Query(None, description="Valor mínimo estimado"),
    valor_max: Optional[float] = Query(None, description="Valor máximo estimado"),
    
    # Filtros por data
    data_abertura_inicio: Optional[date] = Query(None, description="Data de abertura início (YYYY-MM-DD)"),
    data_abertura_fim: Optional[date] = Query(None, description="Data de abertura fim (YYYY-MM-DD)"),
    
    # Busca textual
    texto_busca: Optional[str] = Query(None, description="Busca no objeto, órgão ou número"),
    
    # Paginação
    limite: int = Query(100, ge=1, le=1000, description="Número máximo de resultados"),
    offset: int = Query(0, ge=0, description="Número de registros a pular"),
    
    # Ordenação
    ordenar_por: Optional[str] = Query("data_abertura", description="Campo para ordenação"),
    ordem_desc: bool = Query(False, description="Ordem decrescente")
):
    """
    Obter licitações com filtros avançados.
    
    Permite filtrar por:
    - Tipo de licitação (pregão, concorrência, etc.)
    - Status (aberta, em andamento, etc.)
    - Localização (UF, cidade)
    - Faixa de valores
    - Período de abertura
    - Busca textual
    """
    
    try:
        licitacoes_filtradas, total = filtrar_licitacoes(
            MOCK_LICITACOES,
            tipos=tipos,
            status=status,
            ufs=ufs,
            cidades=cidades,
            valor_min=valor_min,
            valor_max=valor_max,
            data_abertura_inicio=data_abertura_inicio,
            data_abertura_fim=data_abertura_fim,
            texto_busca=texto_busca,
            limite=limite,
            offset=offset
        )
        
        # Ordenação
        if ordenar_por and ordenar_por in ['data_abertura', 'valor_estimado', 'numero']:
            reverse = ordem_desc
            if ordenar_por == 'data_abertura':
                licitacoes_filtradas.sort(key=lambda x: x['data_abertura'], reverse=reverse)
            elif ordenar_por == 'valor_estimado':
                licitacoes_filtradas.sort(key=lambda x: x.get('valor_estimado', 0), reverse=reverse)
            elif ordenar_por == 'numero':
                licitacoes_filtradas.sort(key=lambda x: x['numero'], reverse=reverse)
        
        return {
            "dados": licitacoes_filtradas,
            "total": total,
            "limite": limite,
            "offset": offset,
            "tem_proxima_pagina": offset + limite < total,
            "filtros_aplicados": {
                "tipos": tipos,
                "status": status,
                "ufs": ufs,
                "cidades": cidades,
                "valor_min": valor_min,
                "valor_max": valor_max,
                "data_abertura_inicio": data_abertura_inicio,
                "data_abertura_fim": data_abertura_fim,
                "texto_busca": texto_busca
            }
        }
        
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Erro interno: {str(e)}")

async def listar_orgaos_pncp(self, pagina: int = 1, tamanho_pagina: int = 50):
    url = f"{self.pncp_base_url}/orgaos"
    params = {"pagina": pagina, "tamanhoPagina": tamanho_pagina}

    async with httpx.AsyncClient(timeout=30.0) as client:
        response = await client.get(url, params=params)

        if response.status_code == 200:
            return response.json()
        else:
            print(f"Erro ao buscar órgãos PNCP: {response.status_code}")
            return {"data": [], "totalElements": 0}

@app.get("/orgaos/pncp")
async def obter_orgaos_pncp(
    pagina: int = Query(1, ge=1, description="Página"),
    tamanho_pagina: int = Query(50, ge=1, le=500, description="Tamanho da página")
):
    return await licitacao_service.listar_orgaos_pncp(pagina=pagina, tamanho_pagina=tamanho_pagina)


@app.get("/licitacoes/{licitacao_id}", response_model=LicitacaoResponse)
async def obter_licitacao_por_id(licitacao_id: int):
    """Obter uma licitação específica pelo ID."""
    
    licitacao = next((l for l in MOCK_LICITACOES if l["id"] == licitacao_id), None)
    
    if not licitacao:
        raise HTTPException(status_code=404, detail="Licitação não encontrada")
    
    return licitacao

@app.get("/tipos", response_model=List[str])
async def obter_tipos_licitacao():
    """Obter todos os tipos de licitação disponíveis."""
    return [tipo.value for tipo in TipoLicitacao]

@app.get("/status", response_model=List[str])
async def obter_status_licitacao():
    """Obter todos os status de licitação disponíveis."""
    return [status.value for status in StatusLicitacao]

@app.get("/ufs", response_model=List[str])
async def obter_ufs():
    """Obter todas as UFs (estados) disponíveis."""
    return [uf.value for uf in UF]

@app.get("/cidades")
async def obter_cidades(uf: Optional[UF] = Query(None, description="Filtrar cidades por UF")):
    """Obter cidades disponíveis, opcionalmente filtradas por UF."""
    
    if uf:
        cidades = [l["cidade"] for l in MOCK_LICITACOES if l["uf"] == uf]
    else:
        cidades = [l["cidade"] for l in MOCK_LICITACOES]
    
    return {"cidades": sorted(list(set(cidades)))}

@app.get("/estatisticas")
async def obter_estatisticas():
    """Obter estatísticas gerais das licitações."""
    
    total_licitacoes = len(MOCK_LICITACOES)
    
    # Estatísticas por tipo
    tipos_count = {}
    for licitacao in MOCK_LICITACOES:
        tipo = licitacao["tipo"].value
        tipos_count[tipo] = tipos_count.get(tipo, 0) + 1
    
    # Estatísticas por status
    status_count = {}
    for licitacao in MOCK_LICITACOES:
        status = licitacao["status"].value
        status_count[status] = status_count.get(status, 0) + 1
    
    # Estatísticas por UF
    ufs_count = {}
    for licitacao in MOCK_LICITACOES:
        uf = licitacao["uf"].value
        ufs_count[uf] = ufs_count.get(uf, 0) + 1
    
    # Valor total estimado
    valor_total = sum(l.get("valor_estimado", 0) for l in MOCK_LICITACOES)
    
    return {
        "total_licitacoes": total_licitacoes,
        "valor_total_estimado": valor_total,
        "distribuicao_por_tipo": tipos_count,
        "distribuicao_por_status": status_count,
        "distribuicao_por_uf": ufs_count
    }

# Rota para busca avançada com POST (para filtros complexos)
@app.post("/licitacoes/buscar", response_model=Dict[str, Any])
async def buscar_licitacoes(filtros: FiltrosLicitacao):
    """
    Busca avançada de licitações usando POST para filtros complexos.
    Útil quando você tem muitos parâmetros ou filtros complexos.
    """
    
    licitacoes_filtradas, total = filtrar_licitacoes(
        MOCK_LICITACOES,
        tipos=filtros.tipos,
        status=filtros.status,
        ufs=filtros.ufs,
        cidades=filtros.cidades,
        valor_min=filtros.valor_min,
        valor_max=filtros.valor_max,
        data_abertura_inicio=filtros.data_abertura_inicio,
        data_abertura_fim=filtros.data_abertura_fim,
        texto_busca=filtros.texto_busca
    )
    
    return {
        "dados": licitacoes_filtradas,
        "total": total,
        "filtros_aplicados": filtros.dict(exclude_none=True)
    }

if __name__ == "__main__":
    import uvicorn
    print("🚀 Iniciando API de Licitações...")
    print("📊 Fontes de dados disponíveis:")
    print("   • MOCK: Dados simulados para testes")
    print("   • PNCP: Portal Nacional de Contratações Públicas") 
    print("   • Transparência: Portal da Transparência Federal")
    print("   • Consolidado: Combinação de fontes oficiais")
    print("📖 Documentação disponível em: http://localhost:8000/docs")
    uvicorn.run(app, host="0.0.0.0", port=8000)
