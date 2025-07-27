
import React, { useState } from 'react';
import { FundamentalIndicator, FinancialStatementItem } from '../types';

const mockIndicators: FundamentalIndicator[] = [
    { label: 'P/L', value: 6.5 },
    { label: 'P/VP', value: 1.3 },
    { label: 'Dividend Yield', value: '12.5%' },
    { label: 'ROE', value: '20.0%' },
    { label: 'ROIC', value: '15.5%' },
    { label: 'Dív. Líquida/EBITDA', value: 0.8 },
    { label: 'Margem Bruta', value: '35.2%' },
    { label: 'Margem Líquida', value: '18.9%' },
];

const mockDRE: FinancialStatementItem[] = [
    { item: 'Receita Líquida', value: 'R$ 150.0B', change: '+5.2%', changeType: 'positive' },
    { item: 'Lucro Bruto', value: 'R$ 52.8B', change: '+8.1%', changeType: 'positive' },
    { item: 'EBITDA', value: 'R$ 65.0B', change: '+10.3%', changeType: 'positive' },
    { item: 'Lucro Líquido', value: 'R$ 28.4B', change: '+15.7%', changeType: 'positive' },
];

const mockBalanceSheet: FinancialStatementItem[] = [
    { item: 'Ativo Total', value: 'R$ 1.2T' },
    { item: 'Ativo Circulante', value: 'R$ 300.0B' },
    { item: 'Passivo Total', value: 'R$ 700.0B' },
    { item: 'Dívida Bruta', value: 'R$ 450.0B' },
    { item: 'Patrimônio Líquido', value: 'R$ 500.0B' },
];

const IndicatorGrid: React.FC<{ indicators: FundamentalIndicator[] }> = ({ indicators }) => (
    <div className="grid grid-cols-2 sm:grid-cols-4 gap-4">
        {indicators.map(ind => (
            <div key={ind.label} className="bg-slate-700/50 p-4 rounded-lg text-center">
                <p className="text-sm text-slate-400">{ind.label}</p>
                <p className="text-xl font-bold text-white">{ind.value}</p>
            </div>
        ))}
    </div>
);

const StatementTable: React.FC<{ title: string; data: FinancialStatementItem[] }> = ({ title, data }) => (
    <div className="bg-slate-800/50 rounded-lg p-6 border border-slate-700">
        <h3 className="text-lg font-semibold text-white mb-4">{title}</h3>
        <table className="w-full text-sm text-left text-slate-300">
            <tbody>
                {data.map(item => {
                    const changeColor = item.changeType === 'positive' ? 'text-green-400' : item.changeType === 'negative' ? 'text-red-400' : 'text-slate-400';
                    return (
                        <tr key={item.item} className="border-b border-slate-700 last:border-b-0">
                            <td className="py-3 pr-4 font-medium">{item.item}</td>
                            <td className="py-3 text-right font-semibold text-white">{item.value}</td>
                            {item.change && <td className={`py-3 pl-4 w-24 text-right ${changeColor}`}>{item.change}</td>}
                        </tr>
                    )
                })}
            </tbody>
        </table>
    </div>
);


const Fundamentalist: React.FC = () => {
    const [ticker, setTicker] = useState('PETR4');

    return (
        <div className="space-y-6">
            <div className="flex flex-wrap justify-between items-center gap-4">
                <h2 className="text-xl font-semibold text-white">Análise Fundamentalista</h2>
                <div className="flex items-center gap-2">
                    <input 
                        type="text" 
                        value={ticker}
                        onChange={(e) => setTicker(e.target.value.toUpperCase())}
                        placeholder="PETR4"
                        className="bg-slate-700 border border-slate-600 rounded-md py-1.5 px-3 w-32 text-white placeholder-slate-400 focus:outline-none focus:ring-1 focus:ring-sky-500"
                    />
                    <button className="bg-sky-600 text-white px-4 py-1.5 rounded-md text-sm font-semibold hover:bg-sky-500">
                        Analisar
                    </button>
                </div>
            </div>

            <div className="bg-slate-800/50 rounded-lg p-6 border border-slate-700">
                <div className="flex justify-between items-start mb-4">
                    <div>
                        <h3 className="text-2xl font-bold text-white">Petrobras (PETR4)</h3>
                        <p className="text-slate-400">Petroleo Brasileiro S.A. - Petrobras</p>
                    </div>
                    <div className="text-right">
                         <p className="text-3xl font-bold text-white">R$ 38.50</p>
                         <p className="text-md font-semibold text-green-400">+1.25 (3.35%)</p>
                    </div>
                </div>
                <IndicatorGrid indicators={mockIndicators} />
            </div>

            <div className="grid grid-cols-1 lg:grid-cols-2 gap-6">
                <StatementTable title="DRE Consolidado (Últimos 12M)" data={mockDRE} />
                <StatementTable title="Balanço Patrimonial" data={mockBalanceSheet} />
            </div>
        </div>
    );
};

export default Fundamentalist;
