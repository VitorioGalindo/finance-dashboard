// frontend/src/App.js
import React, { useState, useEffect } from 'react';
import { BrowserRouter as Router, Routes, Route, Link } from 'react-router-dom';
import './App.css';
import apiService from './services/api';

// Componentes
import Dashboard from './components/Dashboard';
import Companies from './components/Companies';
import Market from './components/Market';
import InsiderTrading from './components/InsiderTrading';
import News from './components/News';

function App() {
  const [backendStatus, setBackendStatus] = useState('checking');

  useEffect(() => {
    checkBackendHealth();
  }, []);

  const checkBackendHealth = async () => {
    try {
      await apiService.healthCheck();
      setBackendStatus('connected');
    } catch (error) {
      setBackendStatus('disconnected');
      console.error('Backend não está disponível:', error);
    }
  };

  return (
    <Router>
      <div className="App">
        <header className="App-header">
          <nav className="navbar">
            <div className="nav-brand">
              <h1>Dashboard Financeiro</h1>
              <span className={`status-indicator ${backendStatus}`}>
                {backendStatus === 'connected' && '🟢 Conectado'}
                {backendStatus === 'disconnected' && '🔴 Desconectado'}
                {backendStatus === 'checking' && '🟡 Verificando...'}
              </span>
            </div>
            <ul className="nav-links">
              <li><Link to="/">Dashboard</Link></li>
              <li><Link to="/companies">Empresas</Link></li>
              <li><Link to="/market">Mercado</Link></li>
              <li><Link to="/insider">Insider Trading</Link></li>
              <li><Link to="/news">Notícias</Link></li>
            </ul>
          </nav>
        </header>

        <main className="main-content">
          {backendStatus === 'disconnected' && (
            <div className="alert alert-error">
              <h3>⚠️ Backend Desconectado</h3>
              <p>Certifique-se de que o backend está rodando em http://localhost:5001</p>
              <button onClick={checkBackendHealth}>Tentar Novamente</button>
            </div>
          )}

          <Routes>
            <Route path="/" element={<Dashboard />} />
            <Route path="/companies" element={<Companies />} />
            <Route path="/market" element={<Market />} />
            <Route path="/insider" element={<InsiderTrading />} />
            <Route path="/news" element={<News />} />
          </Routes>
        </main>

        <footer className="App-footer">
          <p>Dashboard Financeiro Brasileiro - Dados da CVM e B3</p>
        </footer>
      </div>
    </Router>
  );
}

export default App;

