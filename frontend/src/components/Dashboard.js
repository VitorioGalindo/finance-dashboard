// frontend/src/components/Dashboard.js
import React, { useState, useEffect } from 'react';
import apiService from '../services/api';

const Dashboard = () => {
  const [marketOverview, setMarketOverview] = useState(null);
  const [sectors, setSectors] = useState(null);
  const [recentNews, setRecentNews] = useState([]);
  const [insiderTransactions, setInsiderTransactions] = useState([]);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState(null);

  useEffect(() => {
    loadDashboardData();
  }, []);

  const loadDashboardData = async () => {
    try {
      setLoading(true);
      setError(null);

      // Carrega dados em paralelo
      const [overviewData, sectorsData, newsData, insiderData] = await Promise.all([
        apiService.getMarketOverview().catch(e => ({ error: e.message })),
        apiService.getMarketSectors().catch(e => ({ error: e.message })),
        apiService.getNews(5).catch(e => ({ error: e.message })),
        apiService.getInsiderTransactions(5).catch(e => ({ error: e.message }))
      ]);

      setMarketOverview(overviewData);
      setSectors(sectorsData);
      setRecentNews(newsData.news || []);
      setInsiderTransactions(insiderData.transactions || []);

    } catch (error) {
      setError('Erro ao carregar dados do dashboard');
      console.error('Dashboard error:', error);
    } finally {
      setLoading(false);
    }
  };

  if (loading) {
    return (
      <div className="dashboard">
        <div className="loading">
          <h2>Carregando Dashboard...</h2>
          <div className="spinner"></div>
        </div>
      </div>
    );
  }

  if (error) {
    return (
      <div className="dashboard">
        <div className="error">
          <h2>❌ {error}</h2>
          <button onClick={loadDashboardData}>Tentar Novamente</button>
        </div>
      </div>
    );
  }

  return (
    <div className="dashboard">
      <h1>Dashboard Financeiro</h1>
      
      {/* Visão Geral do Mercado */}
      <section className="market-overview">
        <h2>📊 Visão Geral do Mercado</h2>
        {marketOverview && !marketOverview.error ? (
          <div className="stats-grid">
            <div className="stat-card">
              <h3>Empresas Ativas</h3>
              <p className="stat-number">{marketOverview.statistics?.total_tickers || 0}</p>
            </div>
            <div className="stat-card">
              <h3>Cotações Hoje</h3>
              <p className="stat-number">{marketOverview.statistics?.total_quotes || 0}</p>
            </div>
            <div className="stat-card">
              <h3>Volume Total</h3>
              <p className="stat-number">
                {marketOverview.statistics?.total_volume 
                  ? `R$ ${(marketOverview.statistics.total_volume / 1000000).toFixed(1)}M`
                  : 'N/A'
                }
              </p>
            </div>
          </div>
        ) : (
          <p>Dados de mercado não disponíveis</p>
        )}
      </section>

      {/* Setores */}
      <section className="sectors-overview">
        <h2>🏭 Setores</h2>
        {sectors && !sectors.error ? (
          <div className="sectors-summary">
            <p><strong>{sectors.total_sectors}</strong> setores com <strong>{sectors.total_companies}</strong> empresas</p>
            <div className="top-sectors">
              {Object.entries(sectors.sectors || {}).slice(0, 5).map(([sector, companies]) => (
                <div key={sector} className="sector-item">
                  <span className="sector-name">{sector}</span>
                  <span className="sector-count">{companies.length} empresas</span>
                </div>
              ))}
            </div>
          </div>
        ) : (
          <p>Dados de setores não disponíveis</p>
        )}
      </section>

      {/* Transações de Insider */}
      <section className="insider-overview">
        <h2>👥 Transações de Insider Recentes</h2>
        {insiderTransactions.length > 0 ? (
          <div className="insider-list">
            {insiderTransactions.map((transaction, index) => (
              <div key={index} className="insider-item">
                <div className="insider-company">{transaction.company_name}</div>
                <div className="insider-details">
                  <span className="insider-name">{transaction.insider_name}</span>
                  <span className="insider-type">{transaction.transaction_type}</span>
                  <span className="insider-value">
                    R$ {transaction.total_value?.toLocaleString('pt-BR') || 'N/A'}
                  </span>
                </div>
              </div>
            ))}
          </div>
        ) : (
          <p>Nenhuma transação de insider recente</p>
        )}
      </section>

      {/* Notícias Recentes */}
      <section className="news-overview">
        <h2>📰 Notícias Recentes</h2>
        {recentNews.length > 0 ? (
          <div className="news-list">
            {recentNews.map((article, index) => (
              <div key={index} className="news-item">
                <h4>{article.title}</h4>
                <p>{article.summary}</p>
                <div className="news-meta">
                  <span>Por: {article.author}</span>
                  <span>Categoria: {article.category}</span>
                </div>
              </div>
            ))}
          </div>
        ) : (
          <p>Nenhuma notícia recente disponível</p>
        )}
      </section>

      <div className="dashboard-actions">
        <button onClick={loadDashboardData} className="refresh-btn">
          🔄 Atualizar Dashboard
        </button>
      </div>
    </div>
  );
};

export default Dashboard;

