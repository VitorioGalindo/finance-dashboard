import React, { useState } from 'react';
import { LineChart, Line, XAxis, YAxis, Tooltip, Legend, ResponsiveContainer, BarChart, Bar } from 'recharts';
import { YieldCurvePoint, CopomSimulation, SelicHistoryPoint } from '../types';
import { InformationCircleIcon, ArrowsPointingOutIcon, FunnelIcon, ChartBarIcon } from '../constants';

// --- Mock Data ---
const mockDetailedYieldCurveTable: YieldCurvePoint[] = [
    { ativo: 'DI1V25', ultimo: 14.930, ultimoChange: -0.07, bps: -1, ajusteAnterior: 14.936, dv1: 1.71, abertura: 14.940, maxima: 14.930, minima: 14.930, fechamento: 14.930 },
    { ativo: 'DI1X25', ultimo: 14.950, ultimoChange: -0.24, bps: 0, ajusteAnterior: 14.948, dv1: 2.45, abertura: 14.960, maxima: 14.950, minima: 14.950, fechamento: 14.950 },
    { ativo: 'DI1Z25', ultimo: 14.950, ultimoChange: 0.00, bps: 17, ajusteAnterior: 14.784, dv1: 3.08, abertura: 14.950, maxima: 14.960, minima: 14.950, fechamento: 14.950 },
    { ativo: 'DI1F26', ultimo: 14.945, ultimoChange: -0.10, bps: 13, ajusteAnterior: 14.817, dv1: 3.76, abertura: 14.950, maxima: 14.950, minima: 14.950, fechamento: 14.950 },
    { ativo: 'DI1G26', ultimo: 14.940, ultimoChange: -0.07, bps: 11, ajusteAnterior: 14.834, dv1: 4.38, abertura: 14.950, maxima: 14.950, minima: 14.940, fechamento: 14.940 },
    { ativo: 'DI1J26', ultimo: 14.900, ultimoChange: -0.13, bps: 7, ajusteAnterior: 14.826, dv1: 5.54, abertura: 14.930, maxima: 14.930, minima: 14.890, fechamento: 14.890 },
    { ativo: 'DI1N26', ultimo: 14.765, ultimoChange: -0.24, bps: 4, ajusteAnterior: 14.729, dv1: 7.23, abertura: 14.810, maxima: 14.810, minima: 14.750, fechamento: 14.750 },
    { ativo: 'DI1V26', ultimo: 14.520, ultimoChange: -0.41, bps: 1, ajusteAnterior: 14.514, dv1: 8.92, abertura: 14.580, maxima: 14.590, minima: 14.510, fechamento: 14.510 },
    { ativo: 'DI1F27', ultimo: 14.255, ultimoChange: -0.45, bps: 3, ajusteAnterior: 14.228, dv1: 10.47, abertura: 14.330, maxima: 14.340, minima: 14.240, fechamento: 14.240 },
    { ativo: 'DI1F28', ultimo: 13.570, ultimoChange: -0.66, bps: -3, ajusteAnterior: 15.79, dv1: 15.79, abertura: 13.670, maxima: 13.700, minima: 13.550, fechamento: 13.550 },
    { ativo: 'DI1F29', ultimo: 13.500, ultimoChange: -0.66, bps: -2, ajusteAnterior: 13.524, dv1: 19.59, abertura: 13.600, maxima: 13.620, minima: 13.540, fechamento: 13.540 },
    { ativo: 'DI1F30', ultimo: 13.610, ultimoChange: -0.73, bps: -2, ajusteAnterior: 13.575, dv1: 21.00, abertura: 13.650, maxima: 13.690, minima: 13.540, fechamento: 13.540 },
];
const mockInteractiveChartData = [
    { name: 'DI1F26', 'Hoje': 14.95, 'D-1': 14.82, 'D-5': 14.85, 'D-30': 14.90 },
    { name: 'DI1N26', 'Hoje': 14.77, 'D-1': 14.73, 'D-5': 14.80, 'D-30': 14.85 },
    { name: 'DI1F27', 'Hoje': 14.26, 'D-1': 14.23, 'D-5': 14.30, 'D-30': 14.40 },
    { name: 'DI1N27', 'Hoje': 13.84, 'D-1': 13.85, 'D-5': 13.90, 'D-30': 14.00 },
    { name: 'DI1F28', 'Hoje': 13.57, 'D-1': 13.58, 'D-5': 13.62, 'D-30': 13.75 },
    { name: 'DI1N28', 'Hoje': 13.49, 'D-1': 13.53, 'D-5': 13.58, 'D-30': 13.68 },
    { name: 'DI1F29', 'Hoje': 13.50, 'D-1': 13.52, 'D-5': 13.55, 'D-30': 13.65 },
    { name: 'DI1N29', 'Hoje': 13.55, 'D-1': 13.57, 'D-5': 13.60, 'D-30': 13.70 },
    { name: 'DI1F30', 'Hoje': 13.61, 'D-1': 13.60, 'D-5': 13.64, 'D-30': 13.72 },
    { name: 'DI1N30', 'Hoje': 13.70, 'D-1': 13.65, 'D-5': 13.68, 'D-30': 13.75 },
    { name: 'DI1F31', 'Hoje': 13.72, 'D-1': 13.68, 'D-5': 13.71, 'D-30': 13.80 },
    { name: 'DI1F32', 'Hoje': 13.79, 'D-1': 13.75, 'D-5': 13.78, 'D-30': 13.85 },
    { name: 'DI1F33', 'Hoje': 13.81, 'D-1': 13.77, 'D-5': 13.80, 'D-30': 13.88 },
];
const mockCopomSimulations: CopomSimulation[] = [
    { reuniao: '29/01/2025', ano: 2025, expectativa: '-', codigo: 'DI1N25', cv: 0, ultimo: 14.8, projetado: 14.96, diferenca: -0.1, dv1: 0.68, pnl: 0.00, dus: 20 },
    { reuniao: '19/03/2025', ano: 2025, expectativa: '-', codigo: 'DI1J25', cv: 0, ultimo: 14.61, projetado: 14.96, diferenca: -0.26, dv1: 1.45, pnl: 0.00, dus: 43 },
    { reuniao: '17/09/2025', ano: 2025, expectativa: '0,15%', codigo: 'DI1F26', cv: 0, ultimo: 14.69, projetado: 14.7, diferenca: -0.007, dv1: 8.8, pnl: 0.00, dus: 172 },
    { reuniao: '18/03/2026', ano: 2026, expectativa: '3,62%', codigo: 'DI1J26', cv: 0, ultimo: 14.7, projetado: 18.63, diferenca: -3.93, dv1: 8.14, pnl: 0.00, dus: 256 },
    { reuniao: '17/06/2026', ano: 2026, expectativa: '106,74%', codigo: 'DI1N27', cv: 0, ultimo: 13.88, projetado: 289.71, diferenca: -285.83, dv1: 13.25, pnl: 0.00, dus: 461 },
];
const mockDecisionHistory: SelicHistoryPoint[] = Array.from({ length: 20 }, (_, i) => ({ date: `18/04/${12 + i}`, value: (Math.random() - 0.5) * 4 }));
const mockSelicHistory: SelicHistoryPoint[] = [
    { date: '18/04/07', value: 18.00 }, { date: '29/04/09', value: 14.00 }, { date: '20/04/11', value: 12.00 }, { date: '17/04/13', value: 14.00 },
    { date: '12/04/17', value: 9.00 }, { date: '08/05/19', value: 3.00 }, { date: '05/05/21', value: 10.00 }, { date: '18/03/23', value: 12.00 }, { date: '18/05/24', value: 15.00 },
];
const mockExpectationsChartData = [
    { name: 'DI1F26', 'Curva de mercado': 15.0, 'Curva projetada': 15.0 },
    { name: 'DI1N26', 'Curva de mercado': 14.5, 'Curva projetada': 15.1 },
    { name: 'DI1', 'Curva de mercado': 14.0, 'Curva projetada': 62.0 },
];


// --- Sub-components ---
const TabButton: React.FC<{ label: string; isActive: boolean; onClick: () => void; }> = ({ label, isActive, onClick }) => (
    <button onClick={onClick} className={`px-4 py-1.5 text-sm font-semibold rounded-md transition-colors ${isActive ? 'bg-sky-600 text-white' : 'text-slate-300 hover:bg-slate-700'}`}>
        {label}
    </button>
);

const BpsIndicator: React.FC<{ value: number }> = ({ value }) => {
    const color = value > 0 ? 'bg-green-500/30 text-green-300' : 'bg-red-500/30 text-red-300';
    return <span className={`font-semibold px-2 py-0.5 rounded text-xs ${color}`}>{value > 0 ? '+' : ''}{value}</span>;
}

// --- Main Component ---
const YieldCurve: React.FC = () => {
    const [activeTab, setActiveTab] = useState<'curva' | 'copom'>('curva');
    const [visibleCurves, setVisibleCurves] = useState({ 'Hoje': true, 'D-1': true, 'D-5': true, 'D-30': true });

    const toggleCurve = (curve: string) => {
        setVisibleCurves(prev => ({ ...prev, [curve]: !prev[curve] }));
    };

    const curveFilters = [
        { name: 'Hoje', color: '#38bdf8' },
        { name: 'D-1', color: '#a78bfa' },
        { name: 'D-5', color: '#f472b6' },
        { name: 'D-30', color: '#fb923c' },
    ];
    
    const groupedSimulations = mockCopomSimulations.reduce((acc, sim) => {
        (acc[sim.ano] = acc[sim.ano] || []).push(sim);
        return acc;
    }, {} as Record<number, CopomSimulation[]>);

    return (
        <div className="space-y-6">
             <div className="flex justify-between items-center">
                <h2 className="text-xl font-semibold text-white flex items-center gap-2">Curva de Juros <InformationCircleIcon className="text-slate-500" /></h2>
                 <div className="flex items-center bg-slate-800 p-1 rounded-lg border border-slate-700">
                    <TabButton label="Curva de Juros" isActive={activeTab === 'curva'} onClick={() => setActiveTab('curva')} />
                    <TabButton label="Decisões do COPOM" isActive={activeTab === 'copom'} onClick={() => setActiveTab('copom')} />
                 </div>
            </div>

            {activeTab === 'curva' && (
                <div className="space-y-6">
                     <div className="bg-slate-800/50 rounded-lg p-4 border border-slate-700">
                         <div className="flex justify-between items-center mb-4">
                             <h3 className="text-lg font-semibold text-white">Tabela de DIs</h3>
                             <div className="flex items-center gap-2">
                                <button className="p-2 rounded-md hover:bg-slate-700 text-slate-400"><FunnelIcon className="w-5 h-5" /></button>
                             </div>
                         </div>
                         <div className="overflow-x-auto">
                            <table className="w-full text-sm text-left text-slate-300">
                                <thead className="text-xs text-slate-400 uppercase bg-slate-700/50">
                                    <tr>
                                        {['Ativo', 'Último', 'BPS', 'Ajuste anterior', 'DV1', 'Abertura', 'Máxima', 'Mínima', 'Fechamento'].map(h => <th key={h} className="px-3 py-2 font-medium whitespace-nowrap">{h}</th>)}
                                    </tr>
                                </thead>
                                <tbody>
                                    {mockDetailedYieldCurveTable.map(item => (
                                        <tr key={item.ativo} className="border-b border-slate-700 hover:bg-slate-700/30">
                                            <td className="px-3 py-2 font-medium text-white flex items-center gap-2"><ChartBarIcon />{item.ativo}</td>
                                            <td className="px-3 py-2">{item.ultimo.toFixed(3)} <span className={`text-xs ${item.ultimoChange > 0 ? 'text-green-400' : 'text-red-400'}`}>({item.ultimoChange.toFixed(2)}%)</span></td>
                                            <td className="px-3 py-2"><BpsIndicator value={item.bps} /></td>
                                            <td className="px-3 py-2">{item.ajusteAnterior.toFixed(3)}</td>
                                            <td className="px-3 py-2">{`R$ ${item.dv1.toFixed(2)}`}</td>
                                            <td className="px-3 py-2">{item.abertura.toFixed(3)}</td>
                                            <td className="px-3 py-2">{item.maxima.toFixed(3)}</td>
                                            <td className="px-3 py-2">{item.minima.toFixed(3)}</td>
                                            <td className="px-3 py-2">{item.fechamento.toFixed(3)}</td>
                                        </tr>
                                    ))}
                                </tbody>
                            </table>
                        </div>
                    </div>
                     <div className="bg-slate-800/50 rounded-lg p-4 border border-slate-700">
                        <div className="flex justify-between items-center mb-4">
                            <h3 className="text-lg font-semibold text-white">Curva de juros</h3>
                            <div className="flex items-center gap-2">
                                <span className="text-xs font-semibold bg-slate-700 px-2 py-1 rounded">Selic: 15,00%</span>
                                <span className="text-xs font-semibold bg-slate-700 px-2 py-1 rounded">CDI: 14,90%</span>
                            </div>
                        </div>
                        <div className="flex items-center gap-2 mb-4">
                            {curveFilters.map(cf => (
                                <button key={cf.name} onClick={() => toggleCurve(cf.name)} className={`flex items-center gap-2 px-3 py-1 text-sm rounded-full transition-all ${visibleCurves[cf.name] ? 'bg-slate-700' : 'bg-transparent text-slate-500'}`}>
                                    <div className="w-3 h-3 rounded-full" style={{ backgroundColor: visibleCurves[cf.name] ? cf.color : '#475569' }}></div>
                                    <span>{cf.name}</span>
                                    <div className="w-4 h-4 text-slate-500">{visibleCurves[cf.name] ? '👁️' : '👁️‍🗨️'}</div>
                                </button>
                            ))}
                             <button className="p-2 rounded-full hover:bg-slate-700 text-slate-400 ml-auto"><ArrowsPointingOutIcon /></button>
                        </div>
                        <ResponsiveContainer width="100%" height={350}>
                            <LineChart data={mockInteractiveChartData} margin={{ top: 5, right: 20, left: -10, bottom: 5 }}>
                                <XAxis dataKey="name" stroke="#94a3b8" fontSize={12} tickLine={false} axisLine={false} />
                                <YAxis stroke="#94a3b8" fontSize={12} tickLine={false} axisLine={false} domain={['dataMin - 0.2', 'dataMax + 0.2']} tickFormatter={(val) => val.toFixed(2)} />
                                <Tooltip contentStyle={{ backgroundColor: '#1e293b', border: '1px solid #334155', color: '#cbd5e1' }} />
                                {curveFilters.map(cf => visibleCurves[cf.name] && <Line key={cf.name} type="monotone" dataKey={cf.name} stroke={cf.color} strokeWidth={2} dot={false} />)}
                            </LineChart>
                        </ResponsiveContainer>
                    </div>
                </div>
            )}
            
            {activeTab === 'copom' && (
                 <div className="space-y-6">
                    <div className="bg-slate-800/50 rounded-lg p-4 border border-slate-700">
                         <h3 className="text-lg font-semibold text-white mb-4">Expectativas para a Selic</h3>
                         <ResponsiveContainer width="100%" height={250}>
                            <LineChart data={mockExpectationsChartData}>
                                <XAxis dataKey="name" stroke="#94a3b8" fontSize={12} tickLine={false} axisLine={false} />
                                <YAxis stroke="#94a3b8" fontSize={12} tickLine={false} axisLine={false} tickFormatter={(val) => `${val.toFixed(2)}%`} domain={[0, 'dataMax + 10']}/>
                                <Tooltip contentStyle={{ backgroundColor: '#1e293b', border: '1px solid #334155' }} formatter={(val: string | number) => `${Number(val).toFixed(2)}%`} />
                                <Legend />
                                <Line type="monotone" dataKey="Curva de mercado" stroke="#f59e0b" strokeWidth={2} dot={false} />
                                <Line type="monotone" dataKey="Curva projetada" stroke="#22c55e" strokeWidth={2} dot={false} />
                            </LineChart>
                         </ResponsiveContainer>
                    </div>

                     <div className="bg-slate-800/50 rounded-lg p-4 border border-slate-700">
                        <h3 className="text-lg font-semibold text-white mb-4">Simulações do COPOM</h3>
                        <div className="overflow-x-auto">
                        <table className="w-full text-sm text-left text-slate-300">
                           <thead className="text-xs text-slate-400 uppercase bg-slate-700/50">
                                <tr>
                                    <th className="px-3 py-2 font-medium">Reunião</th>
                                    <th className="px-3 py-2 font-medium">Expectativa</th>
                                    <th className="px-3 py-2 font-medium">Código</th>
                                    <th className="px-3 py-2 font-medium">C/V</th>
                                    <th className="px-3 py-2 font-medium">Último</th>
                                    <th className="px-3 py-2 font-medium">Projetado</th>
                                    <th className="px-3 py-2 font-medium">Diferença</th>
                                    <th className="px-3 py-2 font-medium">DV1</th>
                                    <th className="px-3 py-2 font-medium">PnL</th>
                                    <th className="px-3 py-2 font-medium">DUs</th>
                                </tr>
                           </thead>
                           {Object.entries(groupedSimulations).map(([year, sims]) => (
                               <tbody key={year}>
                                   <tr className="bg-slate-900/40">
                                       <td className="px-3 py-4 font-bold text-lg text-white" rowSpan={sims.length + 1}>
                                            <div className="-rotate-90 whitespace-nowrap">{year}</div>
                                       </td>
                                   </tr>
                                   {sims.map((sim, index) => (
                                       <tr key={index} className="border-b border-slate-700 hover:bg-slate-700/30">
                                           <td className="px-3 py-2 font-medium">{sim.reuniao}</td>
                                           <td className="px-3 py-2">{sim.expectativa}</td>
                                           <td className="px-3 py-2 font-semibold text-white">{sim.codigo}</td>
                                           <td className="px-3 py-2">{sim.cv}</td>
                                           <td className="px-3 py-2">{sim.ultimo.toFixed(2)}%</td>
                                           <td className="px-3 py-2">{sim.projetado.toFixed(2)}%</td>
                                           <td className={`px-3 py-2 ${sim.diferenca > 0 ? 'text-green-400' : 'text-red-400'}`}>{sim.diferenca.toFixed(3)}%</td>
                                           <td className="px-3 py-2">R$ {sim.dv1.toFixed(2)}</td>
                                           <td className="px-3 py-2">R$ {sim.pnl.toFixed(2)}</td>
                                           <td className="px-3 py-2">{sim.dus}</td>
                                       </tr>
                                   ))}
                               </tbody>
                           ))}
                        </table>
                        </div>
                    </div>
                    
                    <div className="grid grid-cols-1 md:grid-cols-2 gap-6">
                        <div className="bg-slate-800/50 rounded-lg p-4 border border-slate-700">
                             <h3 className="text-lg font-semibold text-white mb-4">Histórico de Decisões</h3>
                             <ResponsiveContainer width="100%" height={250}>
                                <BarChart data={mockDecisionHistory}>
                                    <XAxis dataKey="date" stroke="#94a3b8" fontSize={10} tickLine={false} axisLine={false} />
                                    <YAxis stroke="#94a3b8" fontSize={10} tickLine={false} axisLine={false} tickFormatter={(v) => `${v.toFixed(2)}%`} />
                                    <Tooltip contentStyle={{ backgroundColor: '#1e293b', border: '1px solid #334155' }} formatter={(v: number) => `${v.toFixed(2)}%`} />
                                    <Bar dataKey="value" name="Variação na Selic" fill="#38bdf8" />
                                </BarChart>
                             </ResponsiveContainer>
                        </div>
                         <div className="bg-slate-800/50 rounded-lg p-4 border border-slate-700">
                             <h3 className="text-lg font-semibold text-white mb-4">Selic: 15,00%</h3>
                              <ResponsiveContainer width="100%" height={250}>
                                <LineChart data={mockSelicHistory}>
                                    <XAxis dataKey="date" stroke="#94a3b8" fontSize={10} tickLine={false} axisLine={false} />
                                    <YAxis stroke="#94a3b8" fontSize={10} tickLine={false} axisLine={false} domain={['dataMin - 2', 'dataMax + 2']} tickFormatter={(v) => `${v.toFixed(2)}%`} />
                                    <Tooltip contentStyle={{ backgroundColor: '#1e293b', border: '1px solid #334155' }} formatter={(v: number) => `${v.toFixed(2)}%`} />
                                    <Line type="stepAfter" dataKey="value" name="Taxa Selic" stroke="#38bdf8" strokeWidth={2} dot={false} />
                                </LineChart>
                             </ResponsiveContainer>
                        </div>
                    </div>
                 </div>
            )}
        </div>
    );
};

export default YieldCurve;
