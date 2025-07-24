import React, { useState } from 'react';
// Removidos os imports de componentes de página temporariamente
// import Sidebar from './components/Sidebar';
// import Header from './components/Header';
// import PortfolioDashboard from './components/PortfolioDashboard';
// import AIAssistant from './components/AIAssistant';
// ... outros imports de componentes ...
import { Page } from './types';

const App: React.FC = () => {
  // Mantido o estado, mas não será usado temporariamente
  const [activePage, setActivePage] = useState<Page>('company-news');
  const [searchedTicker, setSearchedTicker] = useState('ITUB4');

  // Removida a lógica de handleSearch e renderContent temporariamente
  // const handleSearch = (ticker: string) => { ... };
  // const renderContent = () => { ... };

  return (
    // --- Renderização Temporária para Debug --- VAI REMOVER ISSO DEPOIS!
    <div className="flex h-screen bg-slate-900 font-sans items-center justify-center text-white text-2xl">
      Frontend Temporariamente Desabilitado para Debug. Verificando... 
    </div>
    // --- Fim da Renderização Temporária ---

    // Código original comentado:
    // <div className="flex h-screen bg-slate-900 font-sans">
    //   <Sidebar activePage={activePage} setActivePage={setActivePage} />
    //   <div className="flex-1 flex flex-col overflow-hidden">
    //     <Header onSearch={handleSearch} />
    //     <main className="flex-1 overflow-x-hidden overflow-y-auto bg-slate-900 p-4 sm:p-6 lg:p-8">
    //       {renderContent()}
    //     </main>
    //   </div>
    // </div>
  );
};

export default App;