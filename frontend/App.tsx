import React, { useState } from 'react';
import Sidebar from './components/Sidebar';
import Header from './components/Header';
import PortfolioDashboard from './components/PortfolioDashboard';
// Importe outros componentes se precisar alternar para eles, mas mantenha o foco no teste
import { Page } from './types';

const App: React.FC = () => {
  // Força a página inicial a ser 'portfolio' para o nosso teste
  const [activePage, setActivePage] = useState<Page>('portfolio');
  const [searchedTicker, setSearchedTicker] = useState('ITUB4');

  const handleSearch = (ticker: string) => {
    if (ticker) {
      setSearchedTicker(ticker.toUpperCase());
      // Você pode querer que a busca leve para a página de overview no futuro
      // setActivePage('overview'); 
    }
  };

  const renderContent = () => {
    switch (activePage) {
      case 'portfolio':
        return <PortfolioDashboard />;
      // Outros casos podem ser adicionados aqui mais tarde
      default:
        return (
          <div className="flex items-center justify-center h-full">
            <div className="text-center p-8 bg-slate-800/50 rounded-lg border border-slate-700">
              <h2 className="text-2xl font-bold text-white mb-2">Página em Construção</h2>
              <p className="text-slate-400">Selecione uma página na barra lateral.</p>
            </div>
          </div>
        );
    }
  };

  return (
    <div className="flex h-screen bg-slate-900 font-sans">
      <Sidebar activePage={activePage} setActivePage={setActivePage} />
      <div className="flex-1 flex flex-col overflow-hidden">
        <Header onSearch={handleSearch} />
        <main className="flex-1 overflow-x-hidden overflow-y-auto bg-slate-900 p-4 sm:p-6 lg:p-8">
          {renderContent()}
        </main>
      </div>
    </div>
  );
};

export default App;
