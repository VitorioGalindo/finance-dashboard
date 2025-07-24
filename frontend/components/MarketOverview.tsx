import React, { useState } from 'react';
import { LineChart, Line, BarChart, Bar, XAxis, YAxis, Tooltip, Legend, ResponsiveContainer, ReferenceLine } from 'recharts';
import { MarketPerformanceItem, StockPerformanceItem, TopMover, SectorParticipation, SentimentData, Page } from '../types';
import { InformationCircleIcon, ChartBarSquareIcon, ChevronDownIcon, MagnifyingGlassIcon } from '../constants';


// --- Mock Data ---
const mockPerformanceData: MarketPerformanceItem[] = [
    { name: 'IBOV Ponderado', lastPrice: 124164.24, ytd: -0.05, ifr: 38.13, m1: -2.15, m3: 2.94, m6: 8.16, m12: 5.10, ytd2: 11.54 },
    { name: 'IBOV Equal-Weighted', lastPrice: 109803.79, ytd: 0.05, ifr: 42.13, m1: 0.33, m3: -5.96, m6: 4.12, m12: -0.15, ytd2: -17.56 },
    { name: 'Small Caps', lastPrice: 2194.42, ytd: -0.16, ifr: 34.94, m1: -4.22, m3: 4.41, m6: 16.10, m12: 1.87, ytd2: 19.38 },
];
const mockStockPerformanceData: StockPerformanceItem[] = [
    { ticker: 'USIM5', lastPrice: 4.27, change: 6.46, ifr: 31.06, m1: -2.95, m3: -25.23, m6: -12.26, m12: -49.44, ytd: -16.74 },
    { ticker: 'GFSA3', lastPrice: 17.98, change: 5.26, ifr: 31.71, m1: -34.42, m3: -46.33, m6: -31.37, m12: -74.93, ytd: -33.81 },
    { ticker: 'CSNA3', lastPrice: 8.46, change: 5.23, ifr: 41.89, m1: 7.88, m3: -4.17, m6: 8.15, m12: -29.44, ytd: -4.18 },
    { ticker: 'BRMS', lastPrice: 8.70, change: 3.93, ifr: 33.01, m1: -11.19, m3: -20.92, m6: -37.78, m12: -52.25, ytd: -24.61 },
    { ticker: 'VALE3', lastPrice: 57.64, change: 2.87, ifr: 53.14, m1: 15.50, m3: 7.18, m6: 1.81, m12: 18.11, ytd: 1.83 },
    { ticker: 'BRAP4', lastPrice: 17.05, change: 2.65, ifr: 53.32, m1: 13.14, m3: 10.24, m6: 4.17, m12: 8.17, ytd: 6.81 },
];
const mockTopGainers: TopMover[] = [
    { ticker: 'USIM5', lastPrice: 4.27, change: 6.46, volume: 50292695 },
    { ticker: 'CSNA3', lastPrice: 8.46, change: 5.88, volume: 83571876 },
    { ticker: 'AURE3', lastPrice: 9.35, change: 3.31, volume: 23335081 },
];
const mockTopLosers: TopMover[] = [
    { ticker: 'VIVA3', lastPrice: 24.98, change: -2.80, volume: 122164139 },
    { ticker: 'CPFE3', lastPrice: 37.39, change: -2.40, volume: 57627437 },
    { ticker: 'TIMS3', lastPrice: 19.80, change: -2.22, volume: 92390663 },
];
const mockMainChartData = Array.from({ length: 120 }, (_, i) => ({
  name: `D-${120 - i}`,
  'IBOV Ponderado': 12000 + Math.sin(i / 20) * 1000 + Math.random() * 500,
  'IBOV Equal-Weighted': 11500 + Math.sin(i / 15) * 800 + Math.random() * 600,
}));
const mockSentimentData: { [key: string]: SentimentData } = {
    IBOV: { value: 60.71, history: Array.from({length: 30}, (_, i) => ({date: `D-${30-i}`, value: 40 + Math.sin(i/3)*20 + Math.random()*10})) },
    'Small Caps': { value: 61.40, history: Array.from({length: 30}, (_, i) => ({date: `D-${30-i}`, value: 45 + Math.sin(i/4)*15 + Math.random()*12})) },
    Geral: { value: 60.62, history: Array.from({length: 30}, (_, i) => ({date: `D-${30-i}`, value: 42 + Math.sin(i/3.5)*18 + Math.random()*11})) },
};
const mockSectorData: SectorParticipation[] = [
    { name: 'Financeiro', weight: 24.81, change: -0.66, companies: 11, color: '#38bdf8' },
    { name: 'Materiais Básicos', weight: 16.24, change: 2.56, companies: 10, color: '#818cf8' },
    { name: 'Petróleo, Gás e Biocombustíveis', weight: 15.32, change: -0.12, companies: 7, color: '#a78bfa' },
    { name: 'Utilidade Pública', weight: 14.95, change: -0.65, companies: 12, color: '#f472b6' },
    { name: 'Bens Industriais', weight: 5.86, change: -0.54, companies: 3, color: '#fb923c' },
    { name: 'Consumo não Cíclico', weight: 4.80, change: 0.22, companies: 7, color: '#facc15' },
    { name: 'Saúde', weight: 3.85, change: -0.16, companies: 5, color: '#4ade80' },
];
const mockSectorDataEqualWeighted: SectorParticipation[] = [
    { name: 'Utilidade Pública', weight: 13.84, change: -0.76, companies: 12, color: '#38bdf8' },
    { name: 'Financeiro', weight: 13.75, change: -0.75, companies: 11, color: '#818cf8' },
    { name: 'Materiais Básicos', weight: 12.84, change: 2.66, companies: 10, color: '#a78bfa' },
    { name: 'Consumo Cíclico', weight: 10.80, change: -0.26, companies: 8, color: '#f472b6' },
    { name: 'Petróleo, Gás e Biocombustíveis', weight: 8.74, change: -0.18, companies: 7, color: '#fb923c' },
    { name: 'Consumo não Cíclico', weight: 8.75, change: 0.15, companies: 7, color: '#facc15' },
    { name: 'Saúde', weight: 6.25, change: -0.19, companies: 5, color: '#4ade80' },
];


// --- Sub-components ---
const TabButton: React.FC<{ label: string; isActive: boolean; onClick: () => void; small?: boolean; }> = ({ label, isActive, onClick, small=false }) => (
    <button onClick={onClick} className={`font-semibold rounded-md transition-colors ${small ? 'px-3 py-1 text-xs' : 'px-4 py-1.5 text-sm'} ${isActive ? 'bg-sky-600 text-white' : 'text-slate-300 hover:bg-slate-700'}`}>
        {label}
    </button>
);

const GaugeChart: React.FC<{ value: number }> = ({ value }) => {
    const percentage = Math.min(Math.max(value, 0), 100);
    const angle = -90 + (percentage / 100) * 180;
    
    return (
        <div className="relative w-48 h-24 mx-auto">
            <svg viewBox="0 0 100 50" className="w-full h-full">
                <path d="M 10 50 A 40 40 0 0 1 90 50" stroke="#ef4444" strokeWidth="8" fill="none" />
                <path d="M 10 50 A 40 40 0 0 1 50 10" stroke="#f59e0b" strokeWidth="8" fill="none" />
                <path d="M 50 10 A 40 40 0 0 1 90 50" stroke="#22c55e" strokeWidth="8" fill="none" />
            </svg>
            <div
                className="absolute bottom-0 left-1/2 w-0.5 h-20 bg-white origin-bottom transition-transform duration-500"
                style={{ transform: `translateX(-50%) rotate(${angle}deg)` }}
            >
                <div className="w-2 h-2 bg-white rounded-full absolute -top-1 -left-0.5"></div>
            </div>
            <div className="absolute bottom-0 left-1/2 -translate-x-1/2 text-2xl font-bold text-white">
                {percentage.toFixed(2)}%
            </div>
        </div>
    );
};

// --- Main Component ---
const MarketOverview: React.FC = () => {
    const [performanceTab, setPerformanceTab] = useState('Índices');
    const [stockSearchTerm, setStockSearchTerm] = useState('');
    const [topMoversTab, setTopMoversTab] = useState('Maiores Altas');
    const [sentimentTab, setSentimentTab] = useState('IBOV');
    const [sectorWeightTab, setSectorWeightTab] = useState<'Ponderadas' | 'Equal-Weighted'>('Ponderadas');
    const [mainChartPeriod, setMainChartPeriod] = useState('YTD');

    const filteredStocks = mockStockPerformanceData.filter(stock =>
        stock.ticker.toLowerCase().includes(stockSearchTerm.toLowerCase())
    );

    return (
        <div className="space-y-6">
            <div className="bg-slate-800/50 rounded-lg p-4 sm:p-6 border border-slate-700">
                <div className="flex justify-between items-center mb-4">
                    <h3 className="text-lg font-semibold text-white">IBOV Ponderado x IBOV Equal-Weighted</h3>
                    <div className="flex items-center bg-slate-800 p-1 rounded-lg border border-slate-700">
                        {['1M', '6M', '1A', '5A', 'Max', 'YTD'].map(p => (
                            <TabButton key={p} label={p} small isActive={mainChartPeriod === p} onClick={() => setMainChartPeriod(p)} />
                        ))}
                    </div>
                </div>
                <ResponsiveContainer width="100%" height={300}>
                    <LineChart data={mockMainChartData} margin={{ top: 5, right: 20, left: -10, bottom: 5 }}>
                        <XAxis dataKey="name" stroke="#94a3b8" fontSize={12} tickLine={false} axisLine={false} />
                        <YAxis stroke="#94a3b8" fontSize={12} tickLine={false} axisLine={false} tickFormatter={(value) => `${(value / 1000).toFixed(0)}k`} />
                        <Tooltip contentStyle={{ backgroundColor: '#1e293b', border: '1px solid #334155' }} />
                        <Legend wrapperStyle={{ fontSize: "12px", paddingTop: '10px' }} />
                        <Line type="monotone" dataKey="IBOV Ponderado" stroke="#fbbf24" strokeWidth={2} dot={false} />
                        <Line type="monotone" dataKey="IBOV Equal-Weighted" stroke="#38bdf8" strokeWidth={2} dot={false} />
                    </LineChart>
                </ResponsiveContainer>
            </div>

            <div className="grid grid-cols-1 lg:grid-cols-2 gap-6">
                <div className="bg-slate-800/50 rounded-lg p-4 sm:p-6 border border-slate-700">
                    <h3 className="text-lg font-semibold text-white mb-4">Indicadores de Sentimento de Mercado</h3>
                     <div className="flex items-center gap-2 border-b border-slate-700 mb-4 pb-2">
                        {Object.keys(mockSentimentData).map(key => (
                            <TabButton key={key} label={key} small isActive={sentimentTab === key} onClick={() => setSentimentTab(key)} />
                        ))}
                         <InformationCircleIcon className="w-5 h-5 text-slate-400 ml-auto" />
                    </div>
                    <div className="grid grid-cols-1 md:grid-cols-2 gap-4 items-center">
                        <div className="flex flex-col items-center">
                           <p className="text-sm font-semibold text-slate-300 mb-2">Ativos {'>'} MM200 <InformationCircleIcon className="inline w-4 h-4 text-slate-500" /></p>
                           <GaugeChart value={mockSentimentData[sentimentTab].value} />
                        </div>
                         <div>
                            <div className="flex justify-between items-center mb-2">
                                <h4 className="text-sm font-semibold text-slate-300">Histórico <InformationCircleIcon className="inline w-4 h-4 text-slate-500" /></h4>
                                <label className="flex items-center text-xs text-slate-400 cursor-pointer">
                                    <input type="checkbox" className="form-checkbox h-4 w-4 rounded bg-slate-700 border-slate-600 text-sky-600 focus:ring-sky-500" />
                                    <span className="ml-2">Mostrar preços</span>
                                    <ChartBarSquareIcon />
                                </label>
                            </div>
                            <ResponsiveContainer width="100%" height={200}>
                                <LineChart data={mockSentimentData[sentimentTab].history}>
                                    <XAxis dataKey="date" hide />
                                    <YAxis domain={[0, 100]} hide />
                                    <Tooltip contentStyle={{ backgroundColor: '#1e293b', border: '1px solid #334155' }} />
                                    <Legend iconSize={10} wrapperStyle={{fontSize: '10px'}} verticalAlign="bottom" />
                                    <ReferenceLine y={90} label={{ value: 'Euforia extrema', position: 'insideTopLeft', fill: '#16a34a', fontSize: 10 }} stroke="#16a34a" strokeDasharray="3 3" />
                                    <ReferenceLine y={75} label={{ value: 'Otimismo Elevado', position: 'insideTopLeft', fill: '#22c55e', fontSize: 10 }} stroke="#22c55e" strokeDasharray="3 3" />
                                    <ReferenceLine y={25} label={{ value: 'Medo elevado', position: 'insideBottomLeft', fill: '#f97316', fontSize: 10 }} stroke="#f97316" strokeDasharray="3 3" />
                                    <ReferenceLine y={10} label={{ value: 'Pânico extremo', position: 'insideBottomLeft', fill: '#ef4444', fontSize: 10 }} stroke="#ef4444" strokeDasharray="3 3" />
                                    <Line type="monotone" dataKey="value" name="Ativos > MM200" stroke="#fbbf24" strokeWidth={2} dot={false} />
                                </LineChart>
                            </ResponsiveContainer>
                        </div>
                    </div>
                </div>

                <div className="bg-slate-800/50 rounded-lg p-4 sm:p-6 border border-slate-700">
                    <h3 className="text-lg font-semibold text-white mb-4">Top 5 - Variações IBOV</h3>
                     <div className="flex items-center gap-2 border-b border-slate-700 mb-4 pb-2">
                        <TabButton label="Maiores Altas" small isActive={topMoversTab === 'Maiores Altas'} onClick={() => setTopMoversTab('Maiores Altas')} />
                        <TabButton label="Maiores Baixas" small isActive={topMoversTab === 'Maiores Baixas'} onClick={() => setTopMoversTab('Maiores Baixas')} />
                    </div>
                    <table className="w-full text-sm text-left">
                        <thead className="text-xs text-slate-400 uppercase">
                            <tr>
                                <th className="py-2">Ticker</th>
                                <th className="py-2 text-right">Últ. Preço</th>
                                <th className="py-2 text-right">Variação</th>
                                <th className="py-2 text-right">Volume (R$)</th>
                            </tr>
                        </thead>
                        <tbody className="text-slate-200">
                            {(topMoversTab === 'Maiores Altas' ? mockTopGainers : mockTopLosers).map(item => (
                                <tr key={item.ticker} className="border-t border-slate-700">
                                    <td className="py-2.5 font-semibold">{item.ticker}</td>
                                    <td className="py-2.5 text-right">{item.lastPrice.toFixed(2)}</td>
                                    <td className={`py-2.5 text-right font-semibold ${item.change > 0 ? 'text-green-400' : 'text-red-400'}`}>{item.change.toFixed(2)}%</td>
                                    <td className="py-2.5 text-right">{item.volume.toLocaleString('pt-BR', {style: 'currency', currency: 'BRL'})}</td>
                                </tr>
                            ))}
                        </tbody>
                    </table>
                </div>
            </div>

            <div className="bg-slate-800/50 rounded-lg p-4 sm:p-6 border border-slate-700">
                <h3 className="text-lg font-semibold text-white mb-4">Participações dos Setores no IBOV</h3>
                <div className="flex items-center bg-slate-800 p-1 rounded-lg border border-slate-700 self-start mb-4">
                    <TabButton label="Ponderadas" small isActive={sectorWeightTab === 'Ponderadas'} onClick={() => setSectorWeightTab('Ponderadas')} />
                    <TabButton label="Simples (Equal-Weighted)" small isActive={sectorWeightTab === 'Equal-Weighted'} onClick={() => setSectorWeightTab('Equal-Weighted')} />
                </div>
                <div className="w-full h-3 rounded-lg flex overflow-hidden mb-4">
                   {(sectorWeightTab === 'Ponderadas' ? mockSectorData : mockSectorDataEqualWeighted).map(s => <div key={s.name} className="h-full" style={{width: `${s.weight}%`, backgroundColor: s.color}}></div>)}
                </div>
                 <div className="space-y-1">
                    {(sectorWeightTab === 'Ponderadas' ? mockSectorData : mockSectorDataEqualWeighted).map(sector => (
                        <div key={sector.name} className="flex items-center justify-between p-2 rounded-md hover:bg-slate-700/50">
                            <div className="flex items-center gap-3">
                                <div className="w-2 h-2 rounded-full" style={{backgroundColor: sector.color}}></div>
                                <span className="font-semibold text-white text-sm">{sector.name}</span>
                                <span className="text-xs text-slate-400">{sector.weight.toFixed(2)}%</span>
                            </div>
                            <div className="flex items-center gap-4">
                                <span className={`text-sm font-semibold ${sector.change > 0 ? 'text-green-400' : 'text-red-400'}`}>{sector.change.toFixed(2)}%</span>
                                <span className="text-xs text-slate-400">{sector.companies} empresas <ChevronDownIcon className="inline w-4 h-4" /></span>
                            </div>
                        </div>
                    ))}
                 </div>
            </div>

            <div className="bg-slate-800/50 rounded-lg p-4 sm:p-6 border border-slate-700">
                 <div className="flex justify-between items-center mb-4">
                    <h3 className="text-lg font-semibold text-white">Monitoramento de Performances</h3>
                    <div className="flex items-center bg-slate-800 p-1 rounded-lg border border-slate-700 self-start">
                        <TabButton label="Índices" small isActive={performanceTab === 'Índices'} onClick={() => setPerformanceTab('Índices')} />
                        <TabButton label="Ações" small isActive={performanceTab === 'Ações'} onClick={() => setPerformanceTab('Ações')} />
                    </div>
                </div>
                 {performanceTab === 'Ações' && (
                    <div className="mb-4">
                         <div className="relative w-full max-w-xs">
                            <input
                                type="search"
                                placeholder="Pesquisar ativo"
                                value={stockSearchTerm}
                                onChange={(e) => setStockSearchTerm(e.target.value)}
                                className="block w-full rounded-md border-0 bg-slate-800 py-2 pl-10 pr-3 text-slate-300 ring-1 ring-inset ring-slate-700 placeholder:text-slate-500 focus:ring-2 focus:ring-inset focus:ring-sky-500 sm:text-sm"
                            />
                            <div className="pointer-events-none absolute inset-y-0 left-0 flex items-center pl-3">
                                <MagnifyingGlassIcon />
                            </div>
                        </div>
                    </div>
                )}
                 <div className="overflow-x-auto">
                    {performanceTab === 'Índices' ? (
                        <table className="w-full text-sm text-left">
                            <thead className="text-xs text-slate-400 uppercase">
                                <tr>
                                    <th className="p-2">Nome</th>
                                    <th className="p-2 text-right">Últ. Preço</th>
                                    <th className="p-2 text-right">%YTD</th>
                                    <th className="p-2 text-right">IFR</th>
                                    <th className="p-2 text-right">1M</th>
                                    <th className="p-2 text-right">3M</th>
                                    <th className="p-2 text-right">6M</th>
                                    <th className="p-2 text-right">12M</th>
                                    <th className="p-2 text-right">YTD</th>
                                </tr>
                            </thead>
                            <tbody className="text-slate-200">
                                {mockPerformanceData.map(item => (
                                    <tr key={item.name} className="border-t border-slate-700">
                                        <td className="p-2.5 font-semibold flex items-center gap-2"><div className="w-2 h-2 rounded-full bg-sky-400"></div>{item.name}</td>
                                        <td className="p-2.5 text-right">{item.lastPrice.toLocaleString('pt-BR', {minimumFractionDigits: 2})}</td>
                                        {[item.ytd, item.ifr, item.m1, item.m3, item.m6, item.m12, item.ytd2].map((val, i) => (
                                            <td key={i} className={`p-2.5 text-right font-semibold ${val > 0 ? 'text-green-400' : 'text-red-400'}`}>{val.toFixed(2)}%</td>
                                        ))}
                                    </tr>
                                ))}
                            </tbody>
                        </table>
                    ) : (
                         <table className="w-full text-sm text-left">
                            <thead className="text-xs text-slate-400 uppercase">
                                <tr>
                                    <th className="p-2">Item</th>
                                    <th className="p-2 text-right">Últ. Preço</th>
                                    <th className="p-2 text-right">%VAR</th>
                                    <th className="p-2 text-right">IFR</th>
                                    <th className="p-2 text-right">1M</th>
                                    <th className="p-2 text-right">3M</th>
                                    <th className="p-2 text-right">6M</th>
                                    <th className="p-2 text-right">12M</th>
                                    <th className="p-2 text-right">YTD</th>
                                </tr>
                            </thead>
                            <tbody className="text-slate-200">
                                {filteredStocks.map(item => (
                                    <tr key={item.ticker} className="border-t border-slate-700">
                                        <td className="p-2.5 font-semibold">{item.ticker}</td>
                                        <td className="p-2.5 text-right">{item.lastPrice.toLocaleString('pt-BR', {minimumFractionDigits: 2})}</td>
                                        <td className={`p-2.5 text-right font-semibold ${item.change > 0 ? 'text-green-400' : 'text-red-400'}`}>{item.change.toFixed(2)}%</td>
                                        <td className="p-2.5 text-right">{item.ifr.toFixed(2)}</td>
                                        {[item.m1, item.m3, item.m6, item.m12, item.ytd].map((val, i) => (
                                            <td key={i} className={`p-2.5 text-right font-semibold ${val > 0 ? 'text-green-400' : 'text-red-400'}`}>{val.toFixed(2)}%</td>
                                        ))}
                                    </tr>
                                ))}
                            </tbody>
                        </table>
                    )}
                </div>
            </div>
        </div>
    );
};

export default MarketOverview;