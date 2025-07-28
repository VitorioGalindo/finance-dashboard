# Análise do Portal RAD CVM

## URL Principal
https://www.rad.cvm.gov.br/ENET/frmConsultaExternaCVM.aspx

## Estrutura de Filtros Disponíveis

### Filtros de Empresa
- **Empresa**: Campo de texto para nome ou Código CVM
- **Tipo de participante**: Dropdown com opções
- **Setor de Atividade**: Dropdown com opções
- **Situação do Registro CVM**: Dropdown com opções
- **Categoria de registro CVM**: Dropdown com opções
- **Situação Operacional**: Dropdown com opções

### Filtros de Data
- **Data de Entrega**: 
  - No Dia (checkbox)
  - Na Semana (checkbox)
  - No período (checkbox com campos De/Até)
- **Data de Referência**: Campo de data
- **Última data de referência**: Checkbox

### Filtros de Documento
- **Status**: Dropdown (TODOS)
- **Tipo de entrega**: Dropdown (TODOS)
- **Categoria**: Link para seleção (TODAS)
- **Tipo**: Link para seleção (TODOS)
- **Espécie**: Link para seleção (TODOS)
- **Palavra-chave**: Campo de texto

### Tipos de Documentos Observados
- **FRE - Formulário de Referência**
- **Estatuto Social**
- **Comunicado ao Mercado**
- **Aviso aos Acionistas**
- **Relatório Proventos**
- **Documentos de Oferta de Distribuição Pública**
- **Informe do Código de Governança**

### Estrutura da Tabela de Resultados
| Campo | Descrição |
|-------|-----------|
| Código CVM | Código identificador da empresa |
| Empresa | Nome da empresa |
| Categoria | Categoria do documento |
| Tipo | Tipo específico do documento |
| Espécie | Espécie do documento |
| Data Referência | Data de referência do documento |
| Data Entrega | Data e hora de entrega |
| Status | Status do documento (Ativo/Inativo) |
| V | Versão |
| Modalidade | Modalidade (AP, RE, etc.) |
| Ações | Links para visualizar/baixar |

## Observações Importantes
1. O portal mostra documentos em tempo real
2. Há muitos documentos de empresas estrangeiras (códigos 05xxx)
3. Documentos brasileiros têm códigos menores (01xxx, 02xxx)
4. Cada documento tem links de ação para download
5. Sistema usa formulários com postback ASP.NET



## Resultados das Buscas Realizadas

### Busca por "CVM 44"
- Retornou principalmente documentos de empresas estrangeiras (códigos 05xxx)
- Tipos encontrados: "Outros Comunicados Não Considerados Fatos Relevantes"
- Assuntos: 10-Q, 6-K, 144, 424B2, etc.

### Busca por "Valores Mobiliários"
- Resultados similares à busca anterior
- Indica que o termo pode não estar sendo indexado corretamente
- Necessário explorar outras abordagens

### Observações sobre Empresas Brasileiras
- Códigos CVM menores (01xxx, 02xxx) indicam empresas brasileiras
- Exemplo: BETAPART PARTICIPACOES S.A. (01788-4)
- USINAS SID DE MINAS GERAIS S.A.-USIMINAS (01432-0)
- JBS S.A. (02057-5)

### Próximos Passos
1. Buscar por empresas brasileiras específicas
2. Analisar estrutura de URLs de download
3. Identificar padrões nos documentos CVM 44
4. Testar download de documentos para análise


## Conclusões da Análise Inicial

### Estrutura do Portal RAD CVM
1. **URL Base**: https://www.rad.cvm.gov.br/ENET/frmConsultaExternaCVM.aspx
2. **Tecnologia**: ASP.NET com postback
3. **Filtros Disponíveis**: Empresa, Data, Categoria, Tipo, Espécie, Palavra-chave
4. **Autocomplete**: Campo empresa tem autocomplete com códigos CVM

### Empresas Brasileiras vs Estrangeiras
- **Brasileiras**: Códigos menores (01xxx, 02xxx, 014xxx)
- **Estrangeiras**: Códigos maiores (05xxx)
- **Exemplo**: PETROBRAS DISTRIBUIDORA SA (014249)

### Tipos de Documentos Observados
- FRE - Formulário de Referência
- Estatuto Social
- Comunicado ao Mercado
- Aviso aos Acionistas
- Relatório Proventos
- Informe do Código de Governança
- Valores Mobiliários Negociados e Detidos (CVM 44)

### Estrutura de URLs e Downloads
- Cada documento tem ícones para: Visualizar, Download, Protocolo
- Sistema usa índices para identificar elementos
- Downloads provavelmente via JavaScript/postback

### Próximos Passos para o Scraper
1. Implementar navegação automatizada
2. Capturar formulários e viewstate ASP.NET
3. Simular buscas por empresas brasileiras
4. Extrair URLs de download
5. Processar PDFs de documentos CVM 44

