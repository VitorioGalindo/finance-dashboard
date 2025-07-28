# RAD CVM Superscraper

Sistema completo de monitoramento e análise de documentos CVM em tempo real, com foco especial em movimentações de insider trading (CVM 44).

## 🚀 Funcionalidades

### ✅ Scraper Automatizado
- Extração automática de documentos do portal RAD CVM
- Monitoramento em tempo real (atualizações a cada minuto)
- Foco em empresas brasileiras da B3
- Identificação automática de documentos CVM 44

### ✅ Processamento de PDFs
- Leitura inteligente de PDFs de documentos CVM 44
- Extração de dados de tabelas de movimentações
- Identificação de pessoas (administradores, controladores)
- Cálculo automático de valores e quantidades

### ✅ Banco de Dados PostgreSQL
- Estrutura otimizada para armazenamento de dados
- Tabelas para empresas, documentos e movimentações
- Índices para consultas rápidas
- Suporte a dados históricos

### ✅ Dashboard Interativo
- Interface web moderna com tema escuro
- Filtros por empresa, categoria e período
- Visualização de movimentações de insider trading
- Estatísticas em tempo real
- Design responsivo para desktop e mobile

## 📋 Pré-requisitos

- Python 3.11+
- PostgreSQL 12+
- Google Chrome (para scraping)
- 4GB RAM mínimo
- 10GB espaço em disco

## 🛠️ Instalação

### 1. Clone o repositório
```bash
git clone <repository-url>
cd rad_cvm_superscraper
```

### 2. Instale as dependências
```bash
pip install -r requirements.txt
```

### 3. Configure o banco de dados
```bash
# Crie um banco PostgreSQL
createdb rad_cvm_db

# Configure as variáveis de ambiente
cp .env.example .env
# Edite o arquivo .env com suas configurações
```

### 4. Configure o ambiente
```bash
# Instale o Google Chrome (se não estiver instalado)
wget -q -O - https://dl.google.com/linux/linux_signing_key.pub | sudo apt-key add -
echo "deb [arch=amd64] http://dl.google.com/linux/chrome/deb/ stable main" | sudo tee /etc/apt/sources.list.d/google-chrome.list
sudo apt update && sudo apt install -y google-chrome-stable

# Instale o ChromeDriver
sudo apt install -y chromium-chromedriver
```

## 🚀 Uso

### Iniciar o Dashboard
```bash
cd dashboard
source venv/bin/activate
python src/main.py
```

O dashboard estará disponível em: `http://localhost:5001`

### Executar o Scraper
```bash
# Teste básico
python rad_cvm_scraper_requests.py

# Monitoramento contínuo
python -c "
from rad_cvm_scraper_requests import RADCVMScraperRequests
scraper = RADCVMScraperRequests()
scraper.run_continuous_monitoring(interval_minutes=1)
"
```

### Processar PDFs
```bash
# Teste do processador
python pdf_processor.py

# Processar um PDF específico
python -c "
from pdf_processor import CVM44PDFProcessor
processor = CVM44PDFProcessor()
result = processor.process_cvm44_pdf('documento.pdf')
print(result)
"
```

## 📊 Estrutura do Projeto

```
rad_cvm_superscraper/
├── rad_cvm_scraper_requests.py    # Scraper principal
├── pdf_processor.py               # Processador de PDFs
├── database.py                    # Gerenciador de banco
├── requirements.txt               # Dependências
├── .env.example                   # Configurações exemplo
├── dashboard/                     # Aplicação web
│   ├── src/
│   │   ├── main.py               # Servidor Flask
│   │   ├── routes/
│   │   │   └── rad_cvm.py        # Rotas da API
│   │   └── static/
│   │       └── index.html        # Frontend
│   └── venv/                     # Ambiente virtual
└── README.md                     # Esta documentação
```

## 🔧 Configuração

### Variáveis de Ambiente (.env)
```bash
# Banco de Dados
DB_HOST=localhost
DB_PORT=5432
DB_NAME=rad_cvm_db
DB_USER=postgres
DB_PASSWORD=sua_senha

# Scraper
SCRAPER_INTERVAL_MINUTES=1
SCRAPER_HEADLESS=true
SCRAPER_DOWNLOAD_PATH=./downloads

# API
API_HOST=0.0.0.0
API_PORT=5001
API_DEBUG=false
```

## 📱 Interface do Dashboard

### Visão Geral
- Estatísticas do sistema
- Status do scraper
- Resumo de atividades

### Documentos CVM
- Lista de documentos coletados
- Filtros por empresa, categoria e período
- Links para download dos documentos

### Radar de Insiders (CVM 44)
- Movimentações de insider trading
- Filtros por ticker e período
- Tabela detalhada de transações
- Valores com cores (verde=compra, vermelho=venda)

### Configurações
- Parâmetros do scraper
- Logs do sistema
- Configurações de monitoramento

## 🔄 API Endpoints

### Empresas
- `GET /api/rad-cvm/empresas` - Lista empresas
- `GET /api/rad-cvm/stats` - Estatísticas gerais

### Documentos
- `GET /api/rad-cvm/documentos` - Lista documentos
- Parâmetros: `codigo_cvm`, `categoria`, `data_inicio`, `data_fim`

### Movimentações CVM 44
- `GET /api/rad-cvm/movimentacoes` - Lista movimentações
- Parâmetros: `codigo_cvm`, `data_inicio`, `data_fim`, `limit`

### Scraper
- `GET /api/rad-cvm/scraper/status` - Status do scraper
- `POST /api/rad-cvm/scraper/run` - Executa scraper manualmente

## 🗄️ Estrutura do Banco

### Tabela: empresas
- `codigo_cvm` - Código CVM da empresa
- `nome` - Nome da empresa
- `setor` - Setor de atuação
- `situacao` - Situação atual

### Tabela: documentos
- `codigo_cvm` - Código da empresa
- `categoria` - Categoria do documento
- `tipo` - Tipo do documento
- `data_entrega` - Data de entrega
- `download_url` - URL para download

### Tabela: cvm44_movimentacoes
- `codigo_cvm` - Código da empresa
- `nome_pessoa` - Nome do insider
- `cargo` - Cargo da pessoa
- `valor_mobiliario` - Tipo de valor mobiliário
- `quantidade_movimentada` - Quantidade da transação
- `tipo_movimentacao` - Compra/Venda
- `preco_unitario` - Preço por ação
- `valor_total` - Valor total da transação
- `data_movimentacao` - Data da transação

## 🔍 Monitoramento

### Logs
O sistema gera logs detalhados em:
- Console (durante desenvolvimento)
- Arquivo de log (configurável)
- Interface web (aba Configurações)

### Métricas
- Documentos coletados por hora
- Empresas monitoradas
- Movimentações CVM 44 detectadas
- Taxa de sucesso do scraper

## 🚨 Troubleshooting

### Erro de Conexão com RAD CVM
- Verifique sua conexão com a internet
- O portal pode estar temporariamente indisponível
- Aguarde alguns minutos e tente novamente

### Erro no ChromeDriver
- Verifique se o Chrome está instalado
- Instale o ChromeDriver compatível
- Use modo headless em servidores

### Erro no Banco de Dados
- Verifique se o PostgreSQL está rodando
- Confirme as credenciais no arquivo .env
- Execute as migrações de banco

### Performance Lenta
- Aumente o intervalo do scraper
- Otimize consultas no banco
- Use índices apropriados

## 📈 Roadmap

### Próximas Funcionalidades
- [ ] Alertas por email/Slack
- [ ] Análise de tendências
- [ ] Exportação para Excel/CSV
- [ ] API GraphQL
- [ ] Autenticação de usuários
- [ ] Dashboards personalizáveis

### Melhorias Técnicas
- [ ] Cache Redis
- [ ] Queue system (Celery)
- [ ] Containerização (Docker)
- [ ] CI/CD pipeline
- [ ] Testes automatizados
- [ ] Monitoramento (Prometheus)

## 🤝 Contribuição

1. Fork o projeto
2. Crie uma branch para sua feature
3. Commit suas mudanças
4. Push para a branch
5. Abra um Pull Request

## 📄 Licença

Este projeto está sob a licença MIT. Veja o arquivo LICENSE para detalhes.

## 📞 Suporte

Para suporte técnico ou dúvidas:
- Abra uma issue no GitHub
- Consulte a documentação
- Verifique os logs do sistema

---

**Desenvolvido com ❤️ para análise de mercado de capitais brasileiro**

