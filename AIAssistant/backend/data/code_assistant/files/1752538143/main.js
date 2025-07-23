document.addEventListener('DOMContentLoaded', () => {
    const tableBody = document.getElementById('table-body');
    const tableHead = document.querySelector('#portfolio-table thead');
    let portfolioData = [];
    let metricsData = {};

    // --- Funções de Renderização ---
    function renderTable() {
        if (!tableBody || !tableHead) {
            console.error("Elementos da tabela não encontrados no DOM.");
            return;
        }

        // Limpa a tabela
        tableBody.innerHTML = '';
        tableHead.innerHTML = '';

        if (portfolioData.length === 0) {
            tableBody.innerHTML = '<tr><td colspan="9">A carteira está vazia.</td></tr>';
            return;
        }

        // Cria o cabeçalho dinamicamente
        const headers = ["Ativo", "Quantidade", "Cotação", "Posição (R$)", "Posição (%)", "Posição Alvo (%)", "Desvio (%)", "Ajuste (R$)", "Ações"];
        const headerRow = document.createElement('tr');
        headers.forEach(headerText => {
            const th = document.createElement('th');
            th.textContent = headerText;
            headerRow.appendChild(th);
        });
        tableHead.appendChild(headerRow);

        // Calcula o financeiro total
        const totalValue = portfolioData.reduce((acc, asset) => acc + (asset.Quantidade * (asset.Cotação || 0)), 0);

        // Cria as linhas da tabela
        portfolioData.forEach(asset => {
            const row = document.createElement('tr');
            row.id = `asset-${asset.Ativo}`;

            const assetValue = asset.Quantidade * (asset.Cotação || 0);
            const currentPositionPercent = totalValue > 0 ? (assetValue / totalValue) : 0;
            const targetPositionPercent = asset['Posição % Alvo'] || 0;
            const deviationPercent = currentPositionPercent - targetPositionPercent;
            const adjustmentValue = deviationPercent * totalValue;

            row.innerHTML = `
                <td>${asset.Ativo}</td>
                <td>${asset.Quantidade.toLocaleString('pt-BR')}</td>
                <td class="quote">R$ ${(asset.Cotação || 0).toFixed(2)}</td>
                <td>R$ ${assetValue.toLocaleString('pt-BR', { minimumFractionDigits: 2, maximumFractionDigits: 2 })}</td>
                <td>${(currentPositionPercent * 100).toFixed(2)}%</td>
                <td>${(targetPositionPercent * 100).toFixed(2)}%</td>
                <td>${(deviationPercent * 100).toFixed(2)}%</td>
                <td>R$ ${adjustmentValue.toLocaleString('pt-BR', { minimumFractionDigits: 2, maximumFractionDigits: 2 })}</td>
                <td><button class="delete-btn" data-ticker="${asset.Ativo}">X</button></td>
            `;
            tableBody.appendChild(row);
        });
    }

    // --- Funções de API ---
    async function fetchPortfolio() {
        try {
            const response = await fetch('/api/portfolio');
            if (!response.ok) throw new Error(`Erro HTTP: ${response.status}`);
            portfolioData = await response.json();
            renderTable(); // Renderiza a tabela inicial sem cotações
            fetchQuotes(); // Busca as cotações logo em seguida
        } catch (error) {
            console.error('Falha ao buscar a carteira:', error);
            tableBody.innerHTML = `<tr><td colspan="9">Erro ao carregar carteira: ${error.message}</td></tr>`;
        }
    }

    async function fetchQuotes() {
        try {
            const response = await fetch('/api/quotes');
            if (!response.ok) throw new Error(`Erro HTTP: ${response.status}`);
            const quotes = await response.json();
            
            // Atualiza os dados da carteira com as novas cotações
            portfolioData.forEach(asset => {
                if (quotes[asset.Ativo]) {
                    asset.Cotação = quotes[asset.Ativo];
                }
            });
            
            // Re-renderiza a tabela com os dados atualizados
            renderTable();

        } catch (error) {
            console.error('Falha ao buscar cotações:', error);
        }
    }

    // --- Inicialização ---
    fetchPortfolio(); // Busca os dados iniciais
    
    // Define um intervalo para buscar as cotações periodicamente (a cada 30 segundos)
    setInterval(fetchQuotes, 30000);
});