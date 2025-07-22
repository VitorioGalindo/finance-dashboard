import React, { useState } from 'react';
import { Page } from '../types';
import { navigationItems } from '../constants';

interface SidebarProps {
  activePage: Page;
  setActivePage: (page: Page) => void;
}

const Sidebar: React.FC<SidebarProps> = ({ activePage, setActivePage }) => {
  const [isCollapsed, setIsCollapsed] = useState(false);

  return (
    <div className={`bg-slate-900 border-r border-slate-800 transition-all duration-300 ease-in-out flex flex-col ${isCollapsed ? 'w-20' : 'w-72'}`}>
      <div className={`flex items-center justify-between h-24 px-4 border-b border-slate-800 shrink-0`}>
        {!isCollapsed && (
            <div className="text-white">
                <h2 className="text-base font-bold leading-tight">Dashboard de Análise e Gerenciamento da Carteira</h2>
                <p className="text-sm text-sky-400 mt-1">Apex - Clube Agathos</p>
            </div>
        )}
        <button onClick={() => setIsCollapsed(!isCollapsed)} className="p-2 rounded-md hover:bg-slate-700 text-slate-400 self-start mt-3">
          {isCollapsed ? (
             <svg xmlns="http://www.w3.org/2000/svg" fill="none" viewBox="0 0 24 24" strokeWidth={1.5} stroke="currentColor" className="w-6 h-6"><path strokeLinecap="round" strokeLinejoin="round" d="M8.25 4.5l7.5 7.5-7.5 7.5" /></svg>
          ) : (
            <svg xmlns="http://www.w3.org/2000/svg" fill="none" viewBox="0 0 24 24" strokeWidth={1.5} stroke="currentColor" className="w-6 h-6"><path strokeLinecap="round" strokeLinejoin="round" d="M15.75 19.5L8.25 12l7.5-7.5" /></svg>
          )}
        </button>
      </div>
      <nav className="mt-4 px-2 overflow-y-auto flex-grow">
        <p className={`px-2 py-2 text-xs font-semibold text-slate-500 uppercase tracking-wider ${isCollapsed ? 'text-center' : ''}`}>Navegar para</p>
        <ul className="space-y-1">
          {navigationItems.map(item => (
            <li key={item.id}>
              <a
                href="#"
                onClick={(e) => { e.preventDefault(); setActivePage(item.id); }}
                className={`flex items-center p-2 rounded-md text-sm font-medium transition-colors ${
                  activePage === item.id 
                    ? 'bg-sky-500/20 text-sky-400' 
                    : 'text-slate-300 hover:bg-slate-700 hover:text-white'
                } ${isCollapsed ? 'justify-center' : ''}`}
                title={item.name}
              >
                <span className="shrink-0">{item.icon}</span>
                {!isCollapsed && <span className="ml-3">{item.name}</span>}
              </a>
            </li>
          ))}
        </ul>
      </nav>
    </div>
  );
};

export default Sidebar;