import React, { useState } from 'react';
import { ResponsiveContainer, ComposedChart, Line, Bar, XAxis, YAxis, Tooltip, Legend, Scatter } from 'recharts';
import { ConsolidatedInsiderTrade, InsiderTransaction, InsiderPricePoint, AnalyticalSummaryItem } from '../types';
import { MagnifyingGlassIcon, CalendarDaysIcon, InformationCircleIcon, ArrowRightIcon } from '../constants';

// --- Mock Data ---
const mockConsolidatedData: ConsolidatedInsiderTrade[] = [
    { ticker: 'MRFG3', buyAbsolute: 834480312, sellAbsolute: 0, buyMarketCap: 0, sellMarketCap: 0 },
    { ticker: 'AURE3', buyAbsolute: 520202219, sellAbsolute: 0, buyMarketCap: 0, sellMarketCap: 0 },
    { ticker: 'VVTT3', buyAbsolute: 400416200, sellAbsolute: 0, buyMarketCap: 0, sellMarketCap: 0 },
    { ticker: 'GGBR4', buyAbsolute: 178114659, sellAbsolute: 0, buyMarketCap: 0, sellMarketCap: 0 },
    { ticker: 'ELET3', buyAbsolute: 138420671, sellAbsolute: 0, buyMarketCap: 0, sellMarketCap: 0 },
];
const mockConsolidatedMarketCapData: ConsolidatedInsiderTrade[] = [
    { ticker: 'IFCM3', buyAbsolute: 0, sellAbsolute: 0, buyMarketCap: 3.45, sellMarketCap: 0 },
    { ticker: 'MRFG3', buyAbsolute: 0, sellAbsolute: 0, buyMarketCap: 3.05, sellMarketCap: 0 },
    { ticker: 'TEND3', buyAbsolute: 0, sellAbsolute: 0, buyMarketCap: 2.65, sellMarketCap: 0 },
    { ticker: 'LAND3', buyAbsolute: 0, sellAbsolute: 0, buyMarketCap: 2.21, sellMarketCap: 0 },
    { ticker: 'BRPR3', buyAbsolute: 0, sellAbsolute: 0, buyMarketCap: 2.10, sellMarketCap: 0 },
];
const mockAnalyticalTransactions: InsiderTransaction[] = [
    { id: '1', date: '2025-05-08', price: 42.07, quantity: 4524000, balance: 112400000, player: 'Conselho de Administração', volumePercent: 12.54, broker: 'BTG', modality: 'Compra a Vista', freeFloatPercent: 3.31, capitalPercent: 7.00, type: 'Compra' },
    { id: '2', date: '2025-05-09', price: 42.15, quantity: 4840000, balance: 110055000, player: 'Conselho de Administração', volumePercent: 13.04, broker: 'BTG', modality: 'Compra a Vista', freeFloatPercent: 3.30, capitalPercent: 6.98, type: 'Compra' },
    { id: '3', date: '2025-06-02', price: 41.80, quantity: 3171700, balance: 112182000, player: 'Tesouraria', volumePercent: 88.67, broker: 'BTG', modality: 'Venda a Vista', freeFloatPercent: 2.20, capitalPercent: 4.91, type: 'Venda' },
    { id: '4', date: '2025-06-10', price: 42.50, quantity: 8897000, balance: 21416000, player: 'Conselho de Administração', volumePercent: 0.47, broker: 'BTG', modality: 'Compra a Vista', freeFloatPercent: 0.12, capitalPercent: 0.28, type: 'Compra' },
];
const mockPriceData: InsiderPricePoint[] = [
    { date: '08/05/25', price: 42.07, transactionType: 'Compra' }, { date: '09/05/25', price: 42.15, transactionType: 'Compra' }, { date: '12/05/25', price: 42.10 },
    { date: '14/05/25', price: 42.30 }, { date: '16/05/25', price: 42.25 }, { date: '20/05/25', price: 42.00 }, { date: '28/05/25', price: 41.95, transactionType: 'Venda' },
    { date: '30/05/25', price: 41.88, transactionType: 'Venda' }, { date: '03/06/25', price: 42.20, transactionType: 'Venda' }, { date: '05/06/25', price: 42.40 }, { date: '09/06/25', price: 42.60, transactionType: 'Compra' },
    { date: '11/06/25', price: 42.55 }, { date: '13/06/25', price: 42.80 },
];
const mockAnalyticalSummary = {
    topTraders: [{ name: 'BTG', percentage: 100 }],
    modalities: [
        { name: 'Compra a vista', balance: 245971000, freeFloat: 7.21, capital: 9.14 },
        { name: 'Venda a vista', balance: -14214000, freeFloat: 0.40, capital: 0.88 },
    ]
};


// --- Sub-components ---
const TabButton: React.FC<{ label: string; isActive: boolean; onClick: () => void }> = ({ label, isActive, onClick }) => (
    <button onClick={onClick} className={`px-4 py-1.5 text-sm font-semibold rounded-md transition-colors ${isActive ? 'bg-sky-600 text-white' : 'text-slate-300 hover:bg-slate-700'}`}>
        {label}
    </button>
);

const CustomTooltip = ({ active, payload, label }: any) => {
  if (active && payload && payload.length) {
    const data = payload[0].payload;
    return (
      <div className="bg-slate-800 border border-slate-700 rounded-lg p-3 text-sm">
        <p className="label text-slate-300">{`Data: ${label}`}</p>
        <p className="intro text-sky-400">{`Preço: R$ ${data.price.toFixed(2)}`}</p>
        {data.transactionType && (
             <p className={`intro ${data.transactionType === 'Compra' ? 'text-green-400' : 'text-red-400'}`}>
                {`Transação: ${data.transactionType}`}
            </p>
        )}
      </div>
    );
  }
  return null;
};

const CustomScatterDot = (props: any) => {
    const { cx, cy, payload } = props;
    if (payload.transactionType) {
        const color = payload.transactionType === 'Compra' ? '#22c55e' : '#ef4444';
        return <circle cx={cx} cy={cy} r={5} fill={color} stroke="#0d1117" strokeWidth={2}/>;
    }
    return null;
};


// --- Main Component ---
const InsiderRadar: React.FC = () => {
    const [activeTab, setActiveTab] = useState<'consolidado' | 'analitico'>('analitico');
    const [showReport, setShowReport] = useState(false);

    const renderConsolidado = () => {
        const maxAbsolute = Math.max(...mockConsolidatedData.map(d => d.buyAbsolute));
        const maxMarketCap = Math.max(...mockConsolidatedMarketCapData.map(d => d.buyMarketCap));

        const renderTradeList = (data: ConsolidatedInsiderTrade[], isAbsolute: boolean) => (
            data.map(trade => {
                const value = isAbsolute ? trade.buyAbsolute : trade.buyMarketCap;
                const maxValue = isAbsolute ? maxAbsolute : maxMarketCap;
                const displayValue = isAbsolute ? `R$ ${(value / 1_000_000).toFixed(2)}M` : `${value.toFixed(2)}%`;
                const width = `${(value / maxValue) * 100}%`;
                
                return (
                    <div key={trade.ticker} className="flex items-center gap-4 py-1.5 px-2 hover:bg-slate-700/30 rounded-md">
                        <span className="w-16 font-medium text-white">{trade.ticker}</span>
                        <div className="flex-1">
                            <div className="w-full bg-slate-700 rounded-full h-2.5">
                                <div className="bg-green-500 h-2.5 rounded-full" style={{ width }}></div>
                            </div>
                        </div>
                        <span className="w-24 text-right text-sm text-green-400">{displayValue}</span>
                        <ArrowRightIcon />
                    </div>
                );
            })
        );

        return (
            <div className="space-y-4">
                <div className="flex items-center justify-between gap-4">
                    <div className="flex items-center gap-2">
                        <span className="text-sm font-semibold text-slate-300">Período</span>
                        <div className="relative">
                           <input type="text" defaultValue="06/2025" className="bg-slate-700 border border-slate-600 rounded-md py-1.5 px-3 pl-8 text-sm w-32"/>
                           <CalendarDaysIcon />
                        </div>
                         <span className="text-slate-400">até</span>
                         <div className="relative">
                           <input type="text" defaultValue="06/2025" className="bg-slate-700 border border-slate-600 rounded-md py-1.5 px-3 pl-8 text-sm w-32"/>
                           <CalendarDaysIcon />
                        </div>
                    </div>
                    <div className="relative w-72">
                        <input type="search" placeholder="Pesquisar ativo" className="block w-full rounded-md border-0 bg-slate-800 py-2 pl-10 pr-3 text-slate-300 ring-1 ring-inset ring-slate-700 placeholder:text-slate-500 focus:ring-2 focus:ring-inset focus:ring-sky-500 sm:text-sm"/>
                        <div className="pointer-events-none absolute inset-y-0 left-0 flex items-center pl-3"><MagnifyingGlassIcon /></div>
                    </div>
                </div>

                <div className="grid grid-cols-1 lg:grid-cols-2 gap-8">
                    {/* Valores Absolutos */}
                    <div>
                        <h3 className="text-lg font-semibold text-white mb-4 flex items-center gap-2">Valores Absolutos <InformationCircleIcon className="text-slate-500"/></h3>
                        <div className="flex justify-between text-xs text-slate-400 mb-2 px-2">
                            <span>Ticker</span>
                            <div className="flex gap-4">
                                <span className="w-24 text-right">Compra</span>
                            </div>
                        </div>
                        <div className="space-y-2">{renderTradeList(mockConsolidatedData, true)}</div>
                    </div>
                    {/* % do Valor de Mercado */}
                    <div>
                        <h3 className="text-lg font-semibold text-white mb-4 flex items-center gap-2">% de valor de Mercado <InformationCircleIcon className="text-slate-500"/></h3>
                        <div className="flex justify-between text-xs text-slate-400 mb-2 px-2">
                            <span>Ticker</span>
                            <div className="flex gap-4">
                                <span className="w-16 text-right">Compra</span>
                            </div>
                        </div>
                         <div className="space-y-2">{renderTradeList(mockConsolidatedMarketCapData, false)}</div>
                    </div>
                </div>
            </div>
        );
    };
    
    const renderAnalitico = () => {
        const groupedTransactions: { [key: string]: InsiderTransaction[] } = mockAnalyticalTransactions.reduce((acc, tx) => {
            const month = new Date(tx.date).toLocaleString('pt-BR', { month: 'long', year: 'numeric' });
            if (!acc[month]) acc[month] = [];
            acc[month].push(tx);
            return acc;
        }, {} as { [key: string]: InsiderTransaction[] });
        
        return (
            <div className="space-y-6">
                <div className="bg-slate-800/50 border border-slate-700 rounded-lg p-4 flex items-center justify-between">
                     <div className="flex items-center gap-2">
                        <div className="flex-1">
                            <label className="text-xs text-slate-400">Ativo</label>
                            <input type="text" defaultValue="ITUB4" className="block w-32 mt-1 rounded-md border-0 bg-slate-700 py-1.5 px-3 text-slate-200 ring-1 ring-inset ring-slate-600 focus:ring-2 focus:ring-inset focus:ring-sky-500 sm:text-sm"/>
                        </div>
                         <div className="flex-1">
                            <label className="text-xs text-slate-400">Período</label>
                            <div className="flex items-center gap-2 mt-1">
                               <input type="text" defaultValue="05/2025" className="block w-28 rounded-md border-0 bg-slate-700 py-1.5 px-3 text-slate-200 ring-1 ring-inset ring-slate-600 focus:ring-2 focus:ring-inset focus:ring-sky-500 sm:text-sm"/>
                               <span className="text-slate-400">até</span>
                               <input type="text" defaultValue="06/2025" className="block w-28 rounded-md border-0 bg-slate-700 py-1.5 px-3 text-slate-200 ring-1 ring-inset ring-slate-600 focus:ring-2 focus:ring-inset focus:ring-sky-500 sm:text-sm"/>
                            </div>
                        </div>
                    </div>
                     <button onClick={() => setShowReport(true)} className="self-end bg-sky-600 text-white px-4 py-2 rounded-md text-sm font-semibold hover:bg-sky-500">
                        Gerar Relatório
                    </button>
                </div>
                
                {!showReport && (
                    <div className="flex flex-col items-center justify-center h-96 text-center text-slate-500 bg-slate-800/30 rounded-lg border border-dashed border-slate-700">
                         <div className="bg-slate-700/50 p-6 rounded-full mb-4">
                            <MagnifyingGlassIcon />
                         </div>
                        <p className="text-lg font-semibold text-slate-300">Aguardando análise</p>
                        <p className="text-sm">Preencha os campos acima para iniciar a análise.</p>
                    </div>
                )}
                
                {showReport && (
                    <div className="space-y-6">
                        {/* Summary */}
                        <div className="bg-slate-800/50 border border-slate-700 rounded-lg p-4">
                            <h3 className="font-semibold text-white mb-3">Total do Período</h3>
                            <div className="grid grid-cols-2 gap-8">
                                <div>
                                    <p className="text-sm font-medium text-slate-400 mb-2">Top Compradores</p>
                                    <div className="flex items-center justify-between text-sm p-2 bg-slate-700/50 rounded">
                                        <span>{mockAnalyticalSummary.topTraders[0].name}</span>
                                        <span className="font-semibold text-white">{mockAnalyticalSummary.topTraders[0].percentage.toFixed(2)}%</span>
                                    </div>
                                </div>
                                <div>
                                    <p className="text-sm font-medium text-slate-400 mb-2">Modalidade</p>
                                    <table className="w-full text-xs text-left">
                                      <thead><tr className="text-slate-400"><th></th><th className="text-right">Saldo Líquido</th><th className="text-right">% Free Float</th><th className="text-right">% Capital</th></tr></thead>
                                      <tbody>
                                        {mockAnalyticalSummary.modalities.map(m => (
                                          <tr key={m.name} className="text-slate-200">
                                            <td className="py-1">{m.name}</td>
                                            <td className={`text-right font-mono ${m.balance > 0 ? 'text-green-400' : 'text-red-400'}`}>R$ {(m.balance/1_000_000).toFixed(2)}M</td>
                                            <td className="text-right font-mono">{m.freeFloat.toFixed(2)}%</td>
                                            <td className="text-right font-mono">{m.capital.toFixed(2)}%</td>
                                          </tr>
                                        ))}
                                      </tbody>
                                    </table>
                                </div>
                            </div>
                        </div>

                        {/* Chart */}
                        <div className="bg-slate-800/50 border border-slate-700 rounded-lg p-6">
                            <h3 className="font-semibold text-white mb-4">Movimentações e Preço da Ação</h3>
                            <ResponsiveContainer width="100%" height={300}>
                                <ComposedChart data={mockPriceData} margin={{ top: 5, right: 20, left: 0, bottom: 5 }}>
                                    <XAxis dataKey="date" stroke="#94a3b8" fontSize={12} tickLine={false} axisLine={false} />
                                    <YAxis stroke="#94a3b8" fontSize={12} tickLine={false} axisLine={false} domain={['dataMin - 1', 'dataMax + 1']} />
                                    <Tooltip content={<CustomTooltip />} />
                                    <Legend />
                                    <Line type="monotone" dataKey="price" name="Preço" stroke="#38bdf8" strokeWidth={2} dot={false} />
                                    <Scatter name="Transações" dataKey="price" fill="red" shape={<CustomScatterDot />} />
                                </ComposedChart>
                            </ResponsiveContainer>
                        </div>
                        
                        {/* Table */}
                         <div className="bg-slate-800/50 border border-slate-700 rounded-lg">
                            <h3 className="font-semibold text-white p-4">Movimentações</h3>
                            <div className="overflow-x-auto">
                                <table className="w-full text-xs text-left text-slate-300">
                                    <thead className="text-slate-400 bg-slate-700/50">
                                        <tr>
                                            {['Preço Médio', 'Quantidade', 'Saldo Líquido', 'Player', '% de Volume Total', 'Corretora', 'Data', 'Modalidade', '% do Free Float', '% Capital', ''].map(h => 
                                                <th key={h} className="px-3 py-2 font-medium whitespace-nowrap">{h}</th>)}
                                        </tr>
                                    </thead>
                                    {Object.entries(groupedTransactions).map(([month, transactions]) => (
                                        <tbody key={month}>
                                            <tr className="bg-slate-700/30">
                                                <td colSpan={11} className="px-3 py-1 font-semibold text-white">{month}</td>
                                            </tr>
                                            {transactions.map(tx => (
                                                <tr key={tx.id} className="border-b border-slate-700/50 hover:bg-slate-700/20">
                                                    <td className="px-3 py-2 whitespace-nowrap">R$ {tx.price.toFixed(2)}</td>
                                                    <td className="px-3 py-2 whitespace-nowrap">{(tx.quantity/1_000).toFixed(2)}K</td>
                                                    <td className={`px-3 py-2 whitespace-nowrap font-mono ${tx.type === 'Compra' ? 'text-green-400' : 'text-red-400'}`}>R$ {(tx.balance/1_000_000).toFixed(2)}M</td>
                                                    <td className="px-3 py-2 whitespace-nowrap">{tx.player}</td>
                                                    <td className="px-3 py-2 whitespace-nowrap">{tx.volumePercent.toFixed(2)}%</td>
                                                    <td className="px-3 py-2"><div className="bg-blue-500 text-white text-center rounded px-2 py-0.5">{tx.broker}</div></td>
                                                    <td className="px-3 py-2 whitespace-nowrap">{new Date(tx.date).toLocaleDateString('pt-BR')}</td>
                                                    <td className="px-3 py-2 whitespace-nowrap">{tx.modality}</td>
                                                    <td className="px-3 py-2 whitespace-nowrap">{tx.freeFloatPercent.toFixed(2)}%</td>
                                                    <td className="px-3 py-2 whitespace-nowrap">{tx.capitalPercent.toFixed(2)}%</td>
                                                    <td className="px-3 py-2"><button><ArrowRightIcon /></button></td>
                                                </tr>
                                            ))}
                                        </tbody>
                                    ))}
                                </table>
                            </div>
                         </div>
                    </div>
                )}
            </div>
        );
    };

    return (
        <div className="space-y-4">
            <div className="flex justify-between items-center">
                <h2 className="text-xl font-semibold text-white flex items-center gap-2">Radar de Insiders (CVM 44) <InformationCircleIcon className="text-slate-500" /></h2>
                 <div className="flex items-center bg-slate-800 p-1 rounded-lg border border-slate-700">
                    <TabButton label="Consolidado" isActive={activeTab === 'consolidado'} onClick={() => setActiveTab('consolidado')} />
                    <TabButton label="Analítico" isActive={activeTab === 'analitico'} onClick={() => setActiveTab('analitico')} />
                 </div>
            </div>
            
            {activeTab === 'consolidado' ? renderConsolidado() : renderAnalitico()}
        </div>
    );
};

export default InsiderRadar;
