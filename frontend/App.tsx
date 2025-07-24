import React, { useState } from 'react';
import Sidebar from './components/Sidebar';
import Header from './components/Header';
// Temporariamente removidos os imports de outros componentes de página
// import PortfolioDashboard from './components/PortfolioDashboard';
// import AIAssistant from './components/AIAssistant';
// ...
import CompanyNews from './components/CompanyNews'; // Mantido apenas o import de CompanyNews
import { Page } from './types';

const App: React.FC = () => {
  // Restaurado o estado activePage para iniciar em 'company-news'
  const [activePage, setActivePage] = useState<Page>('company-news');
  const [searchedTicker, setSearchedTicker] = useState('ITUB4'); // Default ticker

  const handleSearch = (ticker: string) => {
    if (ticker) {
      setSearchedTicker(ticker.toUpperCase());
      setActivePage('overview');
    }
  };

  const renderContent = () => {
    switch (activePage) {
      case 'company-news':
        return <CompanyNews />;
      // Temporariamente removidos os outros casos
      // case 'portfolio': return <PortfolioDashboard />; ...
      default:
        return (
          <div className="flex items-center justify-center h-full">
            <div className="text-center p-8 bg-slate-800/50 rounded-lg border border-slate-700">
              <h2 className="text-2xl font-bold text-white mb-2">Página em Construção</h2>
              <p className="text-slate-400">Esta funcionalidade estará disponível em breve.</p>
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