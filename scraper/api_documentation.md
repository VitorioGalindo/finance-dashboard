# API Completa - Mercado Financeiro Brasileiro

## 📋 Visão Geral

Esta API fornece acesso abrangente a todos os dados do mercado financeiro brasileiro, integrando informações da B3, CVM, RAD CVM, e outras fontes oficiais.

**Base URL:** `https://your-api-domain.com/api/v1`

## 🔑 Autenticação

Todas as requisições devem incluir o header de autenticação:

```http
Authorization: Bearer {sua_api_key}
Content-Type: application/json
```

## 📊 Endpoints Implementados

### 🏢 EMPRESAS & COMPANHIAS

#### 1. Lista de Empresas
```http
GET /companies
```

**Parâmetros:**
- `sector` (string): Filtrar por setor
- `segment` (string): Filtrar por segmento de listagem  
- `is_b3_listed` (boolean): Apenas empresas listadas na B3
- `page` (int): Página (default: 1)
- `limit` (int): Limite por página (default: 50, max: 200)

**Exemplo de Resposta:**
```json
{
  "companies": [
    {
      "cvm_code": "5410",
      "company_name": "Petróleo Brasileiro S.A.",
      "trade_name": "PETROBRAS",
      "cnpj": "33.000.167/0001-01",
      "ticker": "PETR4",
      "sector": "Petróleo, Gás e Biocombustíveis",
      "is_b3_listed": true,
      "market_cap": 389450000000
    }
  ],
  "pagination": {
    "current_page": 1,
    "total_pages": 25,
    "total_items": 400,
    "per_page": 50
  }
}
```

#### 2. Detalhes da Empresa
```http
GET /companies/{cvm_code}
```

#### 3. Demonstrações Financeiras
```http
GET /companies/{cvm_code}/financial-statements
```

**Parâmetros:**
- `statement_type` (string): `DFP`, `ITR`
- `document_type` (string): `BPA`, `BPP`, `DRE`, `DFC_MD`, `DFC_MI`, `DMPL`, `DVA`
- `year` (int): Ano específico
- `period` (int): Trimestre (para ITR)

**Exemplo de Resposta:**
```json
{
  "financial_statements": [
    {
      "cvm_code": "5410",
      "year": 2023,
      "period": 4,
      "statement_type": "DFP",
      "document_type": "DRE",
      "account_code": "3.01",
      "account_description": "Receita de Venda de Bens e/ou Serviços",
      "account_value": 450238000000
    }
  ]
}
```

#### 4. Transações de Insiders
```http
GET /companies/{cvm_code}/insider-transactions
```

**Parâmetros:**
- `year` (int): Ano específico
- `date_from` (date): Data inicial
- `date_to` (date): Data final

**Exemplo de Resposta:**
```json
{
  "insider_transactions": [
    {
      "cvm_code": "22187",
      "ticker": "PRIO3",
      "insider_name": "Roberto Monteiro",
      "insider_position": "Diretor",
      "transaction_date": "2024-03-15",
      "transaction_type": "Compra",
      "quantity": 10000,
      "unit_price": 42.50,
      "total_value": 425000.00
    }
  ]
}
```

#### 5. Dividendos e Proventos
```http
GET /companies/{cvm_code}/dividends
```

**Exemplo de Resposta:**
```json
{
  "dividends": [
    {
      "cvm_code": "5410",
      "ticker": "PETR4",
      "dividend_type": "Dividendos",
      "declaration_date": "2023-08-15",
      "ex_date": "2023-08-20",
      "payment_date": "2023-09-01",
      "value_per_share": 1.25,
      "total_amount": 16258750000
    }
  ]
}
```

#### 6. Composição Acionária
```http
GET /companies/{cvm_code}/shareholding
```

#### 7. Administradores e Conselheiros
```http
GET /companies/{cvm_code}/board-members
```

#### 8. Assembleias Gerais
```http
GET /companies/{cvm_code}/assemblies
```

#### 9. Partes Relacionadas
```http
GET /companies/{cvm_code}/related-parties
```

#### 10. Eventos Corporativos
```http
GET /companies/{cvm_code}/corporate-events
```

#### 11. Captações de Recursos
```http
GET /companies/{cvm_code}/fundraising
```

#### 12. Documentos Regulatórios
```http
GET /companies/{cvm_code}/regulatory-documents
```

**Parâmetros:**
- `document_type` (string): `FORM_REF`, `FATO_REL`, `COMUNICADO`
- `date_from` (date): Data inicial
- `date_to` (date): Data final

### 📈 MERCADO & COTAÇÕES

#### 13. Dados de Mercado (Cotações Históricas)
```http
GET /quotes/{ticker}/history
```

**Parâmetros:**
- `period` (string): `1d`, `5d`, `1m`, `3m`, `6m`, `1y`, `2y`, `5y`, `max`
- `interval` (string): `1m`, `5m`, `15m`, `30m`, `1h`, `1d`, `1wk`, `1mo`
- `adjusted` (boolean): Preços ajustados por proventos

**Exemplo de Resposta:**
```json
{
  "market_data": [
    {
      "ticker": "PETR4",
      "trade_date": "2023-12-15",
      "open_price": 27.58,
      "high_price": 28.67,
      "low_price": 27.45,
      "close_price": 28.45,
      "volume": 45230000,
      "trades_count": 12580
    }
  ]
}
```

### 📊 INDICADORES FINANCEIROS

#### 14. Indicadores Financeiros Calculados
```http
GET /companies/{cvm_code}/financial-indicators
```

**Exemplo de Resposta:**
```json
{
  "financial_indicators": {
    "cvm_code": "5410",
    "year": 2023,
    "liquidity_ratios": {
      "current_ratio": 2.15,
      "quick_ratio": 1.87,
      "cash_ratio": 0.54
    },
    "profitability_ratios": {
      "roe": 0.18,
      "roa": 0.12,
      "gross_margin": 0.45,
      "operating_margin": 0.32,
      "net_margin": 0.28
    },
    "leverage_ratios": {
      "debt_to_equity": 0.65,
      "debt_to_assets": 0.38,
      "interest_coverage": 8.5
    },
    "market_ratios": {
      "pe_ratio": 12.5,
      "pb_ratio": 1.8,
      "ev_ebitda": 8.9,
      "dividend_yield": 0.032
    }
  }
}
```

## 🔍 Filtros e Parâmetros Avançados

### Filtros Disponíveis
- **Por Setor:** `?sector=Petróleo`
- **Por Ano:** `?year=2023`
- **Por Período:** `?date_from=2023-01-01&date_to=2023-12-31`
- **Paginação:** `?page=1&limit=50`

### Ordenação
- **Por Data:** `?sort=date&order=desc`
- **Por Valor:** `?sort=value&order=asc`

## ⚡ Rate Limits

- **Plano Básico:** 1,000 requests/hora
- **Plano Profissional:** 10,000 requests/hora  
- **Plano Enterprise:** 100,000 requests/hora

## 🛡️ Códigos de Status

- `200` - Sucesso
- `400` - Requisição inválida
- `401` - Não autorizado
- `403` - Limite excedido
- `404` - Recurso não encontrado
- `429` - Rate limit excedido
- `500` - Erro interno do servidor

## 🔧 Exemplos de Uso

### Python
```python
import requests

headers = {
    'Authorization': 'Bearer sua_api_key',
    'Content-Type': 'application/json'
}

# Buscar empresas do setor petrolífero
response = requests.get(
    'https://api.mercadobrasil.com/v1/companies?sector=Petróleo',
    headers=headers
)

companies = response.json()
print(f"Encontradas {len(companies['companies'])} empresas")
```

### JavaScript
```javascript
const headers = {
  'Authorization': 'Bearer sua_api_key',
  'Content-Type': 'application/json'
};

// Buscar transações de insiders
fetch('https://api.mercadobrasil.com/v1/companies/22187/insider-transactions', {
  headers: headers
})
.then(response => response.json())
.then(data => console.log(data));
```

### cURL
```bash
# Buscar dividendos da Petrobras
curl -H "Authorization: Bearer sua_api_key" \
     -H "Content-Type: application/json" \
     "https://api.mercadobrasil.com/v1/companies/5410/dividends"
```

## 🗄️ Estrutura de Dados

A API utiliza dados coletados diretamente das fontes oficiais:

- **CVM (Comissão de Valores Mobiliários):** Demonstrações financeiras, insider trading, dividendos
- **RAD CVM:** Formulários de referência, fatos relevantes
- **B3:** Cotações históricas, dados de mercado
- **Banco Central:** Indicadores macroeconômicos

## 📝 Changelog

### v1.0.0 (2025-07-28)
- ✅ Implementação completa dos 13 pontos da especificação
- ✅ Dados históricos desde 2012 para todas as empresas B3
- ✅ Database completo com ~400 empresas ativas
- ✅ Indicadores financeiros calculados automaticamente
- ✅ Sistema de rate limiting implementado

## 📞 Suporte

Para dúvidas ou suporte técnico:
- **Email:** suporte@mercadobrasil.com
- **Documentação:** https://docs.mercadobrasil.com
- **Status da API:** https://status.mercadobrasil.com

---

**Última atualização:** 28 de Julho de 2025  
**Versão da API:** v1.0.0