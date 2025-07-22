
import React, { useState } from 'react';
import { ResponsiveContainer, ComposedChart, Bar, Line, PieChart, Pie, Cell, XAxis, YAxis, Tooltip, Legend } from 'recharts';
import { TechnicalSignal, InsiderDataPoint, RelevantFact, Shareholder } from '../types';
import { BellIcon, ArrowLeftIcon, ArrowTopRightOnSquareIcon, ArrowRightIcon } from '../constants';

// --- Mock Data Store ---

const mockDatabase: { [key: string]: any } = {
    'ITUB4': {
        ticker: 'ITUB4',
        name: 'ITAÚ UNIBANCO',
        price: '35,39',
        change: '-0,14%',
        beta: 0.42,
        volatility: '21,40%',
        freeFloat: '38,36%',
        fundamentals: {
            'Disponibilidades': 'R$ 211.822.000.000,00', 'Receita Bruta': 'R$ 300.1B', 'Receita Líquida': 'R$ 250.5B', 'EBITDA': 'R$ 90.2B', 'Lucro Líquido': 'R$ 40.1B',
            'Dívida Bruta': '39,87%', 'Dívida Líquida': '2.1x', 'Ativo Circulante': 'R$ 500B', 'Passivo Circulante': 'R$ 350B', 'Margem Bruta': '30.05%', 'Margem EBIT': '25.5%',
            'P/L': 9.16, 'P/VP': 1.81, 'ROIC': '19,57%', 'LPA': '3,87', 'ROE': '19,80%', 'ROA': '1,49%', 'CAGR Receitas 5 anos': '4,50%'
        },
        insiderData: Array.from({ length: 50 }, (_, i) => ({ date: `01/${(i % 12) + 1}/24`, price: 30 + Math.sin(i / 5) * 5 + Math.random() * 2, buyVolume: Math.random() > 0.8 ? Math.random() * 1000000 : 0, sellVolume: Math.random() > 0.9 ? Math.random() * 800000 : 0 })),
        relevantFacts: [{id: '1', title: 'ITAÚ UNIBANCO (ITUB4) - Fato Relevante', date: '25/07/2025', time: '08:00'}],
        shareholders: [
            { name: 'IUPAR', percentage: 47.87 }, { name: 'Itaúsa S.A.', percentage: 19.83 }, { name: 'BlackRock Inc', percentage: 3.57 }, { name: 'Outros', percentage: 28.73 },
        ],
    },
    'PETR4': {
        ticker: 'PETR4',
        name: 'PETROBRAS',
        price: '38,50',
        change: '+3,35%',
        beta: 1.2,
        volatility: '35,50%',
        freeFloat: '45,10%',
        fundamentals: {
            'Disponibilidades': 'R$ 80.5B', 'Receita Bruta': 'R$ 550B', 'Receita Líquida': 'R$ 510B', 'EBITDA': 'R$ 250B', 'Lucro Líquido': 'R$ 120B',
            'Dívida Bruta': '1.5x', 'Dívida Líquida': '0.8x', 'Ativo Circulante': 'R$ 150B', 'Passivo Circulante': 'R$ 100B', 'Margem Bruta': '45.4%', 'Margem EBIT': '40.1%',
            'P/L': 4.5, 'P/VP': 1.1, 'ROIC': '25.2%', 'LPA': '8.55', 'ROE': '24.4%', 'ROA': '12.1%', 'CAGR Receitas 5 anos': '10.2%'
        },
        insiderData: Array.from({ length: 50 }, (_, i) => ({ date: `01/${(i % 12) + 1}/24`, price: 35 + Math.sin(i/4) * 4, buyVolume: Math.random() > 0.85 ? Math.random() * 1500000 : 0, sellVolume: Math.random() > 0.85 ? Math.random() * 1200000 : 0 })),
        relevantFacts: [{id: '1', title: 'PETROBRAS (PETR4) - Anúncio de dividendos', date: '22/07/2025', time: '18:30'}],
        shareholders: [
            { name: 'União Federal', percentage: 50.26 }, { name: 'BNDESPar', percentage: 7.34 }, { name: 'Investidores Estrangeiros', percentage: 25.4 }, { name: 'Outros', percentage: 17.0 },
        ],
    },
    'VALE3': {
        ticker: 'VALE3',
        name: 'VALE',
        price: '61,20',
        change: '-1,15%',
        beta: 1.1,
        volatility: '33.20%',
        freeFloat: '98,50%',
        fundamentals: {
            'Disponibilidades': 'R$ 30B', 'Receita Bruta': 'R$ 220B', 'Receita Líquida': 'R$ 200B', 'EBITDA': 'R$ 95B', 'Lucro Líquido': 'R$ 70B',
            'Dívida Bruta': '0.5x', 'Dívida Líquida': '0.1x', 'Ativo Circulante': 'R$ 80B', 'Passivo Circulante': 'R$ 60B', 'Margem Bruta': '42.1%', 'Margem EBIT': '38.5%',
            'P/L': 6.8, 'P/VP': 1.5, 'ROIC': '22.1%', 'LPA': '9.00', 'ROE': '22.0%', 'ROA': '10.5%', 'CAGR Receitas 5 anos': '8.5%'
        },
        insiderData: Array.from({ length: 50 }, (_, i) => ({ date: `01/${(i % 12) + 1}/24`, price: 60 + Math.sin(i/6) * 8, buyVolume: Math.random() > 0.9 ? Math.random() * 2000000 : 0, sellVolume: Math.random() > 0.9 ? Math.random() * 1800000 : 0 })),
        relevantFacts: [{id: '1', title: 'VALE (VALE3) - Relatório de Produção', date: '19/07/2025', time: '09:00'}],
        shareholders: [
            { name: 'Previ', percentage: 8.7 }, { name: 'BlackRock Inc', percentage: 6.3 }, { name: 'Capital Group', percentage: 5.8 }, { name: 'Outros', percentage: 79.2 },
        ],
    }
}

const mockTechnicalSignals: TechnicalSignal[] = [
    { id: 1, type: 'COMPRA', timeframe: '1 dia', status: '21/07/25', close: 'R$ 35,58', entry: 'R$ 37,14', setup: 'TRAP URSO COMPRA', category: 'Geral' },
    { id: 2, type: 'COMPRA', timeframe: '1 dia', status: '21/07/25', close: 'R$ 35,58', entry: 'R$ 37,14', setup: 'JOE DINAPOLI COMPRA', category: '15 min' },
    { id: 3, type: 'COMPRA', timeframe: '1 dia', status: '21/07/25', close: 'R$ 34,99', entry: 'R$ 36,17', setup: 'ESTOCÁSTICO LENTO', category: '30 min' },
    { id: 4, type: 'VENDA', timeframe: '60 min', status: '22/07/25 13:00', close: 'R$ 35,58', entry: 'R$ 34,95', setup: 'TRAP RAPOSA VENDA', category: '60 min' },
    { id: 5, type: 'VENDA', timeframe: '60 min', status: '22/07/25 13:00', close: 'R$ 35,58', entry: 'R$ 34,95', setup: '9.1 VENDA', category: 'Diário' },
];

const PIE_COLORS = ['#38bdf8', '#818cf8', '#a78bfa', '#f472b6', '#fb923c', '#4ade80'];

const TabButton: React.FC<{ label: string; isActive: boolean; onClick: () => void }> = ({ label, isActive, onClick }) => (
    <button onClick={onClick} className={`px-4 py-2 text-sm font-semibold rounded-md transition-colors ${isActive ? 'bg-sky-600 text-white' : 'text-slate-300 hover:bg-slate-700'}`}>
        {label}
    </button>
);

const FundamentosTab: React.FC<{ data: any }> = ({ data }) => (
    <div className="space-y-6 mt-4">
        <div className="grid grid-cols-1 md:grid-cols-3 gap-6">
             <div className="bg-slate-800/50 p-4 rounded-lg border border-slate-700 text-center"><p className="text-sm text-slate-400">Beta</p><p className="text-xl font-bold text-white">{data.beta}</p></div>
             <div className="bg-slate-800/50 p-4 rounded-lg border border-slate-700 text-center"><p className="text-sm text-slate-400">Volatilidade</p><p className="text-xl font-bold text-white">{data.volatility}</p></div>
             <div className="bg-slate-800/50 p-4 rounded-lg border border-slate-700 text-center"><p className="text-sm text-slate-400">Free Float</p><p className="text-xl font-bold text-white">{data.freeFloat}</p></div>
        </div>
        
        <div className="bg-slate-800/50 rounded-lg p-6 border border-slate-700">
            <h3 className="text-lg font-semibold text-white mb-4">Relatórios Fundamentalistas</h3>
            <div className="grid grid-cols-1 md:grid-cols-3 gap-8">
                 <div className="space-y-3 text-sm">
                    {Object.keys(data.fundamentals).slice(0, 5).map(item => <div key={item} className="flex justify-between"><span className="text-slate-400">{item}</span><span className="font-semibold text-white">{data.fundamentals[item]}</span></div>)}
                 </div>
                 <div className="space-y-3 text-sm">
                     {Object.keys(data.fundamentals).slice(5, 12).map(item => <div key={item} className="flex justify-between"><span className="text-slate-400">{item}</span><span className="font-semibold text-white">{data.fundamentals[item]}</span></div>)}
                 </div>
                 <div className="space-y-3 text-sm">
                     {Object.keys(data.fundamentals).slice(12).map(item => <div key={item} className="flex justify-between"><span className="text-slate-400">{item}</span><span className="font-semibold text-white">{data.fundamentals[item]}</span></div>)}
                 </div>
            </div>
        </div>

        <div className="bg-slate-800/50 rounded-lg p-6 border border-slate-700">
            <h3 className="text-lg font-semibold text-white mb-4">Radar de Insiders (CVM 44)</h3>
            <ResponsiveContainer width="100%" height={300}>
                <ComposedChart data={data.insiderData}>
                    <XAxis dataKey="date" stroke="#94a3b8" fontSize={12} tickLine={false} axisLine={false} />
                    <YAxis yAxisId="left" stroke="#94a3b8" fontSize={12} tickLine={false} axisLine={false} tickFormatter={(value) => `R$${value.toFixed(2)}`}/>
                    <YAxis yAxisId="right" orientation="right" stroke="#94a3b8" fontSize={12} tickLine={false} axisLine={false} tickFormatter={(value) => `${(value / 1000000).toFixed(1)}M`} />
                    <Tooltip contentStyle={{ backgroundColor: '#1e293b', border: '1px solid #334155', color: '#cbd5e1' }}/>
                    <Legend />
                    <Bar yAxisId="right" dataKey="buyVolume" name="Compra" barSize={20} fill="#10b981" />
                    <Bar yAxisId="right" dataKey="sellVolume" name="Venda" barSize={20} fill="#f43f5e" />
                    <Line yAxisId="left" type="monotone" dataKey="price" name="Preço" stroke="#38bdf8" strokeWidth={2} dot={false} />
                </ComposedChart>
            </ResponsiveContainer>
        </div>

        <div className="grid grid-cols-1 lg:grid-cols-2 gap-6">
            <div className="bg-slate-800/50 rounded-lg p-6 border border-slate-700">
                <h3 className="text-lg font-semibold text-white mb-4">Fatos Relevantes</h3>
                <div className="space-y-3">
                    {data.relevantFacts.map((fact: RelevantFact) => (
                        <div key={fact.id} className="flex items-center text-sm p-2 rounded-md hover:bg-slate-700/50">
                            <DocumentIcon />
                            <div className="ml-3 flex-grow">
                                <p className="font-semibold text-white">{fact.title}</p>
                                <p className="text-xs text-slate-400">{fact.date} às {fact.time}</p>
                            </div>
                            <ArrowTopRightOnSquareIcon className="w-4 h-4 text-slate-400" />
                        </div>
                    ))}
                </div>
            </div>
            <div className="bg-slate-800/50 rounded-lg p-6 border border-slate-700">
                 <h3 className="text-lg font-semibold text-white mb-4">Composição Acionária</h3>
                 <ResponsiveContainer width="100%" height={250}>
                    <PieChart>
                       <Pie data={data.shareholders} dataKey="percentage" nameKey="name" cx="50%" cy="50%" outerRadius={80} label>
                          {data.shareholders.map((entry: Shareholder, index: number) => <Cell key={`cell-${index}`} fill={PIE_COLORS[index % PIE_COLORS.length]} />)}
                       </Pie>
                       <Tooltip contentStyle={{ backgroundColor: '#1e293b', border: '1px solid #334155' }} formatter={(value:number) => `${value.toFixed(2)}%`} />
                       <Legend wrapperStyle={{fontSize: "12px"}}/>
                    </PieChart>
                 </ResponsiveContainer>
            </div>
        </div>
    </div>
);

const TecnicoTab: React.FC = () => {
    const categories = ['Geral', '15 min', '30 min', '60 min', 'Diário', 'Semanal'];
    const [activeCategory, setActiveCategory] = useState('Geral');
    const [statusFilter, setStatusFilter] = useState('Em Aberto');

    const filteredSignals = mockTechnicalSignals.filter(s => {
        if (activeCategory === 'Geral') return true;
        return s.category === activeCategory;
    });

    const getCategoryCount = (category: string, type: 'COMPRA' | 'VENDA') => {
        return mockTechnicalSignals.filter(s => s.category === category && s.type === type).length;
    };

    return (
        <div className="space-y-6 mt-4">
            <div className="flex items-center gap-4 bg-slate-800/50 p-4 rounded-lg border border-slate-700">
                {['MM3', 'MM9', 'MM21'].map(mm => <div key={mm} className="text-center"><p className="text-sm text-slate-400">{mm}</p><div className="w-16 h-1 bg-red-500 rounded-full mt-1"></div><p className="text-xs text-red-400 mt-1">-24,25%</p></div>)}
                <div className="flex-grow text-center"><p className="text-sm text-slate-400">Var(%) da Ação</p><div className="w-full h-1 bg-red-500 rounded-full mt-1"></div><p className="text-xs text-red-400 mt-1">-15,46%</p></div>
                <div className="w-48 text-center"><p className="text-sm text-slate-400">Medidor de Agressão</p>
                  <div className="w-full h-4 bg-red-500 rounded-md mt-1 flex">
                    <div className="bg-green-500 h-full rounded-l-md" style={{width: '31.38%'}}></div>
                  </div>
                  <div className="flex justify-between text-xs mt-1">
                    <span className="text-green-400">31,38%</span><span className="text-red-400">68,62%</span>
                  </div>
                </div>
            </div>

            <div className="bg-slate-800/50 rounded-lg border border-slate-700">
                <div className="p-4 flex justify-between items-center border-b border-slate-700">
                    <div className="flex items-center gap-4">
                        <h3 className="text-lg font-semibold text-white">Sinais</h3>
                        {['15 min', '30 min', '60 min', 'Diário', 'Semanal'].map(tf => (
                            <label key={tf} className="flex items-center text-sm text-slate-300">
                                <input type="checkbox" className="form-checkbox h-4 w-4 rounded bg-slate-700 border-slate-600 text-sky-600 focus:ring-sky-500" defaultChecked />
                                <span className="ml-2">{tf}</span>
                            </label>
                        ))}
                    </div>
                    <div className="flex items-center bg-slate-800 p-1 rounded-lg border border-slate-600">
                        <button onClick={() => setStatusFilter('Em Aberto')} className={`px-3 py-1 text-xs rounded-md ${statusFilter === 'Em Aberto' ? 'bg-sky-600 text-white' : 'text-slate-300 hover:bg-slate-700'}`}>Em Aberto</button>
                        <button onClick={() => setStatusFilter('Histórico')} className={`px-3 py-1 text-xs rounded-md ${statusFilter === 'Histórico' ? 'bg-sky-600 text-white' : 'text-slate-300 hover:bg-slate-700'}`}>Histórico</button>
                    </div>
                </div>
                <div className="flex">
                    <div className="w-48 border-r border-slate-700 p-2">
                        <ul>
                            {categories.map(cat => (
                                <li key={cat}>
                                    <button onClick={() => setActiveCategory(cat)} className={`w-full text-left p-2 rounded-md text-sm flex justify-between items-center ${activeCategory === cat ? 'bg-slate-700 text-white' : 'text-slate-400 hover:bg-slate-700/50'}`}>
                                        <span>{cat}</span>
                                        <div className="flex items-center gap-1">
                                            <span className="text-green-400 text-xs font-mono">{getCategoryCount(cat, 'COMPRA')}</span>
                                            <span className="text-red-400 text-xs font-mono">{getCategoryCount(cat, 'VENDA')}</span>
                                        </div>
                                    </button>
                                </li>
                            ))}
                        </ul>
                    </div>
                    <div className="flex-1 p-4">
                        <div className="space-y-3">
                            {filteredSignals.map(signal => (
                                <div key={signal.id} className={`p-3 rounded-lg flex items-center gap-4 ${signal.type === 'COMPRA' ? 'bg-green-500/10 border-l-4 border-green-500' : 'bg-red-500/10 border-l-4 border-red-500'}`}>
                                    <div className="w-20 text-center"><p className="text-xs text-slate-400">Tipo</p><p className={`font-bold ${signal.type === 'COMPRA' ? 'text-green-400' : 'text-red-400'}`}>{signal.type}</p></div>
                                    <div className="w-24 text-center"><p className="text-xs text-slate-400">Time Frame</p><p className="font-semibold text-white">{signal.timeframe}</p></div>
                                    <div className="w-24 text-center"><p className="text-xs text-slate-400">Status</p><p className="font-semibold text-white">{signal.status}</p></div>
                                    <div className="w-24 text-center"><p className="text-xs text-slate-400">Fechamento</p><p className="font-semibold text-white">{signal.close}</p></div>
                                     <div className="w-24 text-center"><p className="text-xs text-slate-400">Entrada</p><p className={`font-bold p-1 rounded-md ${signal.type === 'COMPRA' ? 'bg-green-900/50 text-green-300' : 'bg-red-900/50 text-red-300'}`}>{signal.entry}</p></div>
                                    <div className="flex-grow text-left pl-4"><p className="text-xs text-slate-400">Setup</p><p className="font-semibold text-white">{signal.setup}</p></div>
                                    <ArrowRightIcon />
                                </div>
                            ))}
                        </div>
                    </div>
                </div>
            </div>
        </div>
    );
}

const DocumentIcon: React.FC = () => (
  <svg xmlns="http://www.w3.org/2000/svg" fill="none" viewBox="0 0 24 24" strokeWidth={1.5} stroke="currentColor" className="w-6 h-6 text-sky-400"><path strokeLinecap="round" strokeLinejoin="round" d="M19.5 14.25v-2.625a3.375 3.375 0 0 0-3.375-3.375h-1.5A1.125 1.125 0 0 1 13.5 7.125v-1.5a3.375 3.375 0 0 0-3.375-3.375H8.25m0 12.75h7.5m-7.5 3h7.5m-11.25-3h.008v.008H8.25v-.008Zm0 3h.008v.008H8.25v-.008Zm0-6h.008v.008H8.25v-.008Zm-3.75 0h.008v.008H4.5v-.008Zm0 3h.008v.008H4.5v-.008Zm0 3h.008v.008H4.5v-.008Z" /></svg>
);

const CompanyOverview: React.FC<{ ticker: string }> = ({ ticker }) => {
    const [activeTab, setActiveTab] = useState<'tecnico' | 'fundamentos'>('fundamentos');
    
    const companyData = mockDatabase[ticker.toUpperCase()] || mockDatabase['ITUB4'];

    if (!companyData) {
        return <div className="text-center p-8">Empresa não encontrada.</div>
    }

    return (
        <div className="space-y-6">
            <div className="flex justify-between items-center">
                <div className="flex items-center gap-4">
                    <span className="text-3xl font-bold text-white">{companyData.ticker}</span>
                    <div>
                        <h2 className="text-lg font-semibold text-white">{companyData.name}</h2>
                        <p className={`font-semibold ${companyData.change.startsWith('-') ? 'text-red-400' : 'text-green-400'}`}>
                            R$ {companyData.price} ({companyData.change})
                        </p>
                    </div>
                </div>
                <div className="flex items-center gap-2">
                    <button className="flex items-center gap-2 px-3 py-2 text-sm font-semibold text-white bg-slate-700/50 border border-slate-600 rounded-md hover:bg-slate-700">
                        <ArrowLeftIcon />
                        Voltar
                    </button>
                    <button className="flex items-center gap-2 px-3 py-2 text-sm font-semibold text-white bg-slate-700/50 border border-slate-600 rounded-md hover:bg-slate-700">
                        <BellIcon />
                        Sino do RI
                    </button>
                </div>
            </div>

            <div className="flex items-center gap-2 p-1 bg-slate-800 border border-slate-700 rounded-lg self-start">
                <TabButton label="Técnico" isActive={activeTab === 'tecnico'} onClick={() => setActiveTab('tecnico')} />
                <TabButton label="Fundamentos" isActive={activeTab === 'fundamentos'} onClick={() => setActiveTab('fundamentos')} />
            </div>

            {activeTab === 'tecnico' ? <TecnicoTab /> : <FundamentosTab data={companyData} />}
        </div>
    );
};

export default CompanyOverview;