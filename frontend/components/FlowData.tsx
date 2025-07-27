import React, { useState } from 'react';
import { ResponsiveContainer, LineChart, Line, BarChart, Bar, AreaChart, Area, ComposedChart, XAxis, YAxis, Tooltip, Legend } from 'recharts';
import { DailyFlow, AccumulatedFlowPoint, MonthlyFlow, DetailedDailyFlow, DetailedMonthlyFlow, FlowChartPoint, AccumulatedAnnualFlowPoint } from '../types';

// Mock Data
const mockResumoDailyFlow: DailyFlow[] = Array.from({ length: 10 }, (_, i) => ({
    date: `18/07/${25-i}`,
    estrangeiro: (Math.random() - 0.6) * 1000,
    institucional: (Math.random() - 0.4) * 500,
    instituicoesFinanceiras: (Math.random() - 0.5) * 400,
    pessoasFisicas: (Math.random() - 0.5) * 300,
    outros: (Math.random() - 0.5) * 100,
}));

const mockAccumulatedFlow: AccumulatedFlowPoint[] = Array.from({ length: 50 }, (_, i) => ({
    date: `D-${50-i}`,
    Estrangeiro: 10 + Math.sin(i / 5) * 20,
    Institucional: 5 + Math.sin(i / 6) * 15,
    'Instituições Financeiras': -5 + Math.sin(i/7) * 10,
    'Pessoas Físicas': 2 + Math.sin(i/8) * 5,
    Outros: 1 + Math.sin(i/9) * 2,
    IBOV: 120000 + Math.sin(i/4) * 5000
}));

const mockMonthlyFlow: MonthlyFlow[] = [
    { month: 'Estrangeiro', value: -1.39 }, { month: 'Institucional', value: 0.20 },
    { month: 'Instituições Financeiras', value: 1.99 }, { month: 'Pessoas Físicas', value: 1.44 },
    { month: 'Outros', value: 0.23 },
];

const mockAnnualFlow: { name: string, aVista: number, futuro: number }[] = [
  { name: 'Estrangeiro', aVista: 22.14, futuro: 9.78 },
];

const mockDetailedDaily: DetailedDailyFlow[] = Array.from({ length: 10 }, (_, i) => ({
  date: `18/07/${25 - i}`,
  aVista: (Math.random() - 0.6) * 1000,
  futuro: (Math.random() - 0.5) * 500,
  total: (Math.random() - 0.55) * 1500,
}));

const mockDetailedMonthly: DetailedMonthlyFlow[] = [
  { date: 'JAN', aVista: '-', futuro: '-', total: '-' },
  { date: 'FEV', aVista: -4.8, futuro: 3.5, total: -1.3 },
  { date: 'MAR', aVista: 5.2, futuro: 1.2, total: 6.4 },
  { date: 'ABR', aVista: -2.1, futuro: -0.5, total: -2.6 },
];

const mockFlowChart: FlowChartPoint[] = Array.from({ length: 30 }, (_, i) => ({
  date: `D-${30-i}`,
  'Fluxo R$': (Math.random() - 0.5) * 2000,
  'Fechamento IBOV': 120000 + Math.sin(i/3) * 2000,
}));

const mockAccumulatedChart: {date: string, aVista: number, futuro: number}[] = Array.from({ length: 30 }, (_, i) => ({
  date: `D-${30-i}`,
  aVista: 20 + Math.sin(i/3) * 15,
  futuro: 10 + Math.sin(i/4) * 10,
}));

const mockAnnualAccumulated: AccumulatedAnnualFlowPoint[] = Array.from({ length: 12 }, (_, i) => ({
  date: ['JAN', 'FEV', 'MAR', 'ABR', 'MAI', 'JUN', 'JUL', 'AGO', 'SET', 'OUT', 'NOV', 'DEZ'][i],
  y2025: -10 + Math.sin(i / 1.5) * 15,
  y2024: 5 + Math.sin(i / 2) * 20,
  y2023: 15 + Math.sin(i / 2.5) * 10,
  y2022: 25 + Math.sin(i / 3) * 5,
  y2021: -5 + Math.sin(i / 3.5) * 12,
}));

const renderColorfulText = (value: number) => (
    <span className={value > 0 ? 'text-green-400' : 'text-red-400'}>
        {value.toLocaleString('pt-BR', { minimumFractionDigits: 2 })}
    </span>
);

const ChartCard: React.FC<{ title: string; children: React.ReactNode }> = ({ title, children }) => (
    <div className="bg-slate-800/50 p-4 rounded-lg border border-slate-700 h-full flex flex-col">
        <h3 className="text-base font-semibold text-white mb-4">{title}</h3>
        <div className="flex-grow">
            {children}
        </div>
    </div>
);


const FlowData = () => {
    const tabs = ['Resumo', 'Estrangeiros', 'Institucional', 'Instituições Financeiras', 'Pessoas Físicas', 'Outros'];
    const [activeTab, setActiveTab] = useState(tabs[0]);

    const renderResumoTab = () => (
      <div className="space-y-4">
        <div className="grid grid-cols-1 lg:grid-cols-3 gap-4">
            <ChartCard title="Fluxo à vista (acumulado)"><ResponsiveContainer width="100%" height={200}><LineChart data={mockAccumulatedFlow}><Tooltip /><Line type="monotone" dataKey="Estrangeiro" stroke="#8884d8" dot={false} /><Line type="monotone" dataKey="Institucional" stroke="#82ca9d" dot={false} /><Line type="monotone" dataKey="Outros" stroke="#ffc658" dot={false} /></LineChart></ResponsiveContainer></ChartCard>
            <ChartCard title="Fluxo futuro (acumulado)"><ResponsiveContainer width="100%" height={200}><LineChart data={mockAccumulatedFlow}><Tooltip /><Line type="monotone" dataKey="Estrangeiro" stroke="#8884d8" dot={false} /><Line type="monotone" dataKey="Institucional" stroke="#82ca9d" dot={false} /></LineChart></ResponsiveContainer></ChartCard>
            <ChartCard title="Fluxo total (acumulado)"><ResponsiveContainer width="100%" height={200}><LineChart data={mockAccumulatedFlow}><Tooltip /><Line type="monotone" dataKey="Estrangeiro" stroke="#8884d8" dot={false} /><Line type="monotone" dataKey="Institucional" stroke="#82ca9d" dot={false} /></LineChart></ResponsiveContainer></ChartCard>
        </div>
        <div className="bg-slate-800/50 p-4 rounded-lg border border-slate-700">
            <h3 className="text-base font-semibold text-white mb-4">Fluxo diário (R$ milhões)</h3>
            <table className="w-full text-sm text-left text-slate-300">
                <thead className="text-xs text-slate-400 uppercase"><tr><th>Data</th><th>Estrangeiro</th><th>Institucional</th><th>Instituições Financeiras</th><th>Pessoas Físicas</th><th>Outros</th></tr></thead>
                <tbody>{mockResumoDailyFlow.map(d => <tr key={d.date} className="border-b border-slate-700/50"><td>{d.date}</td><td>{renderColorfulText(d.estrangeiro)}</td><td>{renderColorfulText(d.institucional)}</td><td>{renderColorfulText(d.instituicoesFinanceiras)}</td><td>{renderColorfulText(d.pessoasFisicas)}</td><td>{renderColorfulText(d.outros)}</td></tr>)}</tbody>
            </table>
        </div>
        <div className="grid grid-cols-1 lg:grid-cols-2 gap-4">
             <ChartCard title="Fluxo mensal acumulado (à vista)"><ResponsiveContainer width="100%" height={250}><BarChart data={mockMonthlyFlow}><Tooltip />{mockMonthlyFlow.map(item => <Bar key={item.month} dataKey="value" fill={item.value > 0 ? '#22c55e' : '#ef4444'} name={item.month} />)}<XAxis dataKey="month" /></BarChart></ResponsiveContainer></ChartCard>
             <ChartCard title="Fluxo anual acumulado (à vista)"><ResponsiveContainer width="100%" height={250}><BarChart layout="vertical" data={mockAnnualFlow}><Tooltip /><YAxis type="category" dataKey="name" width={80} /><XAxis type="number" /><Bar dataKey="aVista" fill="#8884d8" /></BarChart></ResponsiveContainer></ChartCard>
        </div>
        <div className="grid grid-cols-1 lg:grid-cols-2 gap-4">
            <ChartCard title="Fluxo mensal acumulado (futuro)"><ResponsiveContainer width="100%" height={250}><BarChart data={mockMonthlyFlow}><Tooltip />{mockMonthlyFlow.map(item => <Bar key={item.month} dataKey="value" fill={item.value > 0 ? '#22c55e' : '#ef4444'} name={item.month} />)}<XAxis dataKey="month" /></BarChart></ResponsiveContainer></ChartCard>
            <ChartCard title="Fluxo anual acumulado (futuro)"><ResponsiveContainer width="100%" height={250}><BarChart layout="vertical" data={mockAnnualFlow}><Tooltip /><YAxis type="category" dataKey="name" width={80} /><XAxis type="number" /><Bar dataKey="futuro" fill="#82ca9d" /></BarChart></ResponsiveContainer></ChartCard>
        </div>
      </div>
    );

    const renderDetalheTab = (investorType: string) => (
        <div className="space-y-4">
            <div className="grid grid-cols-1 lg:grid-cols-2 gap-4">
                <ChartCard title="Evolução diária (Consolidado)">
                    <table className="w-full text-xs">
                        <thead><tr><th>Data</th><th>À vista</th><th>Futuro</th><th>Total</th></tr></thead>
                        <tbody>{mockDetailedDaily.map(d=><tr key={d.date}><td>{d.date}</td><td>{renderColorfulText(d.aVista)}</td><td>{renderColorfulText(d.futuro)}</td><td>{renderColorfulText(d.total)}</td></tr>)}</tbody>
                    </table>
                </ChartCard>
                <ChartCard title="Fluxo à vista"><ResponsiveContainer width="100%" height={200}><ComposedChart data={mockFlowChart}><Tooltip /><Bar dataKey="Fluxo R$" fill="#8884d8" /><Line type="monotone" dataKey="Fechamento IBOV" stroke="#ff7300" dot={false} /></ComposedChart></ResponsiveContainer></ChartCard>
            </div>
            <div className="grid grid-cols-1 lg:grid-cols-2 gap-4">
                 <ChartCard title="Fluxo mensal (à vista)"><ResponsiveContainer width="100%" height={200}><BarChart data={mockMonthlyFlow.slice(0, 3)}><Tooltip /><XAxis dataKey="month" /><Bar dataKey="value" fill="#8884d8" /></BarChart></ResponsiveContainer></ChartCard>
                 <ChartCard title="Fluxo no ano (à vista)"><ResponsiveContainer width="100%" height={200}><BarChart data={mockMonthlyFlow.slice(0, 3)}><Tooltip /><XAxis dataKey="month" /><Bar dataKey="value" fill="#82ca9d" /></BarChart></ResponsiveContainer></ChartCard>
            </div>
            <div className="grid grid-cols-1 lg:grid-cols-2 gap-4">
                <ChartCard title="Evolução mensal (Consolidado)">
                    <table className="w-full text-xs">
                        <thead><tr><th>Data</th><th>À vista</th><th>Futuro</th><th>Total</th></tr></thead>
                        <tbody>{mockDetailedMonthly.map(d=><tr key={d.date}><td>{d.date}</td><td>{d.aVista}</td><td>{d.futuro}</td><td>{d.total}</td></tr>)}</tbody>
                    </table>
                </ChartCard>
                <ChartCard title="Fluxo Total (à vista e Futuro)"><ResponsiveContainer width="100%" height={200}><BarChart data={mockFlowChart}><Tooltip /><Bar dataKey="Fluxo à vista" stackId="a" fill="#8884d8" /><Bar dataKey="Fluxo Futuro" stackId="a" fill="#82ca9d" /></BarChart></ResponsiveContainer></ChartCard>
            </div>
             <div className="grid grid-cols-1 lg:grid-cols-2 gap-4">
                <ChartCard title="Acumulado 2025 (Futuro)"><ResponsiveContainer width="100%" height={200}><AreaChart data={mockAccumulatedChart}><Tooltip /><Area type="monotone" dataKey="aVista" stackId="1" stroke="#8884d8" fill="#8884d8" /><Area type="monotone" dataKey="futuro" stackId="1" stroke="#82ca9d" fill="#82ca9d" /></AreaChart></ResponsiveContainer></ChartCard>
                <ChartCard title="Fluxo anual acumulado (à vista - R$ bi/ano)"><ResponsiveContainer width="100%" height={200}><LineChart data={mockAnnualAccumulated}><Tooltip /><Legend /><Line dataKey="y2025" stroke="#8884d8" dot={false} /><Line dataKey="y2024" stroke="#82ca9d" dot={false} /><Line dataKey="y2023" stroke="#ffc658" dot={false} /></LineChart></ResponsiveContainer></ChartCard>
            </div>
        </div>
    );

    return (
        <div className="space-y-4">
            <div className="flex items-center gap-1 bg-slate-800 p-1 rounded-lg border border-slate-700 self-start">
                {tabs.map(tab => (
                    <button key={tab} onClick={() => setActiveTab(tab)} className={`px-4 py-1.5 text-sm font-semibold rounded-md transition-colors ${activeTab === tab ? 'bg-sky-600 text-white' : 'text-slate-300 hover:bg-slate-700'}`}>
                        {tab}
                    </button>
                ))}
            </div>
            {activeTab === 'Resumo' ? renderResumoTab() : renderDetalheTab(activeTab)}
        </div>
    );
};

export default FlowData;
