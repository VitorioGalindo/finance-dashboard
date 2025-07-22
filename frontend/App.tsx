import React, { useState } from 'react';
import Sidebar from './components/Sidebar';
import Header from './components/Header';
import PortfolioDashboard from './components/PortfolioDashboard';
import AIAssistant from './components/AIAssistant';
import MarketNews from './components/MarketNews';
import YieldCurve from './components/YieldCurve';
import InsiderRadar from './components/InsiderRadar';
import MacroData from './components/MacroData';
import Fundamentalist from './components/Fundamentalist';
import CompanyOverview from './components/CompanyOverview';
import HistoricalData from './components/HistoricalData';
import CvmDocuments from './components/CvmDocuments';
import MarketOverview from './components/MarketOverview';
import Screening from './components/Screening';
import FlowData from './components/FlowData';
import SellSideData from './components/SellSideData';
import Research from './components/Research';
import CompanyNews from './components/CompanyNews';
import { Page } from './types';

const App: React.FC = () => {
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
      case 'portfolio':
        return <PortfolioDashboard />;
      case 'ai-assistant':
        return <AIAssistant />;
      case 'overview':
        return <CompanyOverview ticker={searchedTicker} />;
      case 'history':
        return <HistoricalData ticker="PRIO3" />;
      case 'market-data':
        return <MarketNews />;
      case 'yield-curve':
        return <YieldCurve />;
      case 'insider-radar':
        return <InsiderRadar />;
      case 'macro-data':
        return <MacroData />;
      case 'fundamentalist':
        return <Fundamentalist />;
      case 'cvm-docs':
        return <CvmDocuments />;
      case 'market-overview':
        return <MarketOverview />;
      case 'screening':
        return <Screening />;
      case 'flow-data':
        return <FlowData />;
      case 'sell-side-data':
        return <SellSideData />;
      case 'research':
        return <Research />;
      case 'company-news':
        return <CompanyNews />;
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