import React, { useState } from 'react';
import { ScreeningFormula, ScreeningResultCompany, MetricCategory } from '../types';
import { 
    Cog6ToothIcon, SparklesIcon, ScaleIcon, ChartTrendingUpIcon, LightBulbIcon, PresentationChartBarIcon, 
    CircleStackIcon, BanknotesIcon, WrenchScrewdriverIcon, PlusIcon, XMarkIcon, InformationCircleIcon,
    MagnifyingGlassIcon
} from '../constants';

// --- Mock Data ---
const screeningFormulas: ScreeningFormula[] = [
    { id: 'personalizado', name: 'Personalizado', icon: <Cog6ToothIcon /> },
    { id: 'magic', name: 'Fórmula Mágica', author: 'Joel Greenblatt', icon: <SparklesIcon /> },
    { id: 'graham', name: 'Fórmula de Graham', icon: <ScaleIcon /> },
    { id: 'anualizado', name: 'Resultado anualizado', icon: <ChartTrendingUpIcon /> },
    { id: 'peg', name: 'Indicador PEG', icon: <LightBulbIcon /> },
    { id: 'pl_media', name: 'P/L abaixo da média', icon: <PresentationChartBarIcon /> },
    { id: 'ev_ebitda_media', name: 'EV/EBITDA abaixo da média', icon: <CircleStackIcon /> },
    { id: 'roe_investidor', name: 'ROE do investidor', icon: <BanknotesIcon /> },
    { id: 'magic_ajustada', name: 'Fórmula mágica ajustada', icon: <WrenchScrewdriverIcon /> },
];

const mockResults: { [key: string]: ScreeningResultCompany[] } = {
    'magic': Array.from({ length: 25 }, (_, i) => ({ rank: i + 1, ticker: `TICK${i+1}`, cota: 15.20 + Math.random()*5, valorMercado: 13586523652, ebit: 7.04, roic: 28, rankingEbit: 32, rankingRoic: 32, pvp: 0.9, dy: 1.5, evEbitda: 3.8, margemBruta: 18.1, dividaLiquidaEbitda: -0.44 })),
    'graham': Array.from({ length: 20 }, (_, i) => ({ rank: i + 1, ticker: `GRHM${i+1}`, cota: 25.00 + Math.random()*10, formulaGraham: 14.13, valorMercado: 2153386523, pl: 0.14, pvp: 0.22, dy: 8.99, roe: 10.9, roic: -38.4 })),
    'anualizado': Array.from({ length: 15 }, (_, i) => ({ rank: i + 1, ticker: `ANU${i+1}`, cota: 87.46, resultadoAnualizado: 495625754, valorMercado: 405625754, pl: 6.7, evEbitda: 4.9, pvp: 1.63, roe: 23.4, roic: 17.4, margemBruta: 41.0, margemLiquida: 15.1 })),
};

const metricCategories: MetricCategory[] = [
    { id: 'geral', name: 'Todas as métricas', metrics: [] },
    { id: 'demonstracao', name: 'Demonstração', metrics: [ {id: 'total_despesas', name: 'Total de despesas/receitas operacionais (SG&A)'}, {id: 'receita_liquida', name: 'Receita líquida de vendas'} ]},
    { id: 'balanco', name: 'Balanço patrimonial', metrics: [ {id: 'ativo_total', name: 'Ativo total'}, {id: 'ativo_circulante', name: 'Ativo circulante'}, {id: 'caixa', name: 'Caixa'}, {id: 'contas_receber', name: 'Contas a receber'} ] },
    { id: 'fluxo_caixa', name: 'Fluxo de caixa', metrics: [] },
];

const formulaColumns: { [key: string]: string[] } = {
    'magic': ['Ranking', 'Empresa', 'Cotação', 'Valor de mercado', 'EBIT', 'ROIC', 'Ranking de EBIT', 'Ranking de ROIC', 'P/VP', 'DY', 'EV/EBITDA', 'Margem Bruta', 'Dívida Líquida/EBITDA'],
    'graham': ['Ranking', 'Empresa', 'Cotação', 'Fórmula de Graham', 'Valor de mercado', 'P/L', 'P/VP', 'DY', 'ROE', 'ROIC'],
    'anualizado': ['Ranking', 'Empresa', 'Cotação', 'Resultado anualizado', 'Valor de mercado', 'P/L', 'EV/EBITDA', 'P/VP', 'ROE', 'ROIC', 'Margem Bruta', 'Margem Líquida'],
    'default': ['Ranking', 'Empresa', 'Cotação', 'Valor de mercado', 'P/L', 'P/VP', 'DY', 'ROE'],
};

// --- Sub Components ---

const FormulaCard: React.FC<{ formula: ScreeningFormula; onClick: () => void; }> = ({ formula, onClick }) => (
    <button onClick={onClick} className="bg-slate-800/50 p-4 rounded-lg border border-slate-700 text-left hover:bg-slate-700/50 hover:border-sky-500 transition-colors w-full">
        <div className="flex justify-between items-start">
            <div className="w-10 h-10 bg-slate-700 rounded-md flex items-center justify-center text-sky-400">
                {formula.icon}
            </div>
            <InformationCircleIcon className="w-5 h-5 text-slate-500" />
        </div>
        <h3 className="text-white font-semibold mt-3">{formula.name}</h3>
        {formula.author && <p className="text-xs text-slate-400">{formula.author}</p>}
    </button>
);


const Screening: React.FC = () => {
    const [view, setView] = useState<'selection' | 'results'>('selection');
    const [selectedFormula, setSelectedFormula] = useState<ScreeningFormula | null>(null);
    const [isModalOpen, setIsModalOpen] = useState(false);
    const [activeMetricCategory, setActiveMetricCategory] = useState<string>(metricCategories[0].id);

    const handleFormulaSelect = (formula: ScreeningFormula) => {
        setSelectedFormula(formula);
        setView('results');
    };
    
    const results = selectedFormula ? (mockResults[selectedFormula.id] || []) : [];
    const columns = selectedFormula ? (formulaColumns[selectedFormula.id] || formulaColumns.default) : [];

    const SelectionView = () => (
        <div className="space-y-8">
            <div className="flex items-end gap-4">
                <div>
                    <label className="text-sm text-slate-300 mb-1 block">Liquidez ADTV - 90d</label>
                    <input type="text" defaultValue="100.000,00" className="bg-slate-800 border border-slate-700 rounded-md p-2 w-48"/>
                </div>
                <div>
                    <label className="text-sm text-slate-300 mb-1 block">Quantidade de empresas</label>
                    <input type="text" defaultValue="10" className="bg-slate-800 border border-slate-700 rounded-md p-2 w-32"/>
                </div>
            </div>
            <div>
                <h3 className="text-lg font-semibold text-white mb-4">Escolha a sua fórmula:</h3>
                <div className="grid grid-cols-2 md:grid-cols-3 lg:grid-cols-5 gap-4">
                    {screeningFormulas.map(f => <FormulaCard key={f.id} formula={f} onClick={() => handleFormulaSelect(f)} />)}
                </div>
            </div>
            <div>
                 <h3 className="text-lg font-semibold text-white mb-4">Defina suas métricas:</h3>
                 <button onClick={() => setIsModalOpen(true)} className="flex items-center gap-2 px-4 py-2 border-2 border-dashed border-slate-600 rounded-lg text-slate-300 hover:border-sky-500 hover:text-sky-400 transition-colors">
                    <PlusIcon /> Adicionar métricas
                 </button>
            </div>
        </div>
    );
    
    const ResultsView = () => (
        <div className="space-y-6">
            <div className="flex justify-between items-center">
                <div>
                    <h2 className="text-2xl font-bold text-white flex items-center gap-2">
                        {selectedFormula?.icon} {selectedFormula?.name}
                    </h2>
                     <div className="flex items-center gap-2 text-sm text-slate-400 mt-2">
                        <label><input type="checkbox" className="form-checkbox rounded bg-slate-700 border-slate-600 text-sky-600" defaultChecked/> Dados atualizados</label>
                        <label><input type="checkbox" className="form-checkbox rounded bg-slate-700 border-slate-600 text-sky-600"/> Dados desatualizados</label>
                     </div>
                </div>
                <div className="flex items-center gap-4">
                     <button onClick={() => setView('selection')} className="text-sm text-sky-400 hover:underline">Voltar</button>
                     <button className="bg-purple-600 text-white px-4 py-2 rounded-md text-sm font-semibold hover:bg-purple-500">Reportar erro</button>
                     <div className="relative"><input type="search" placeholder="Pesquisar" className="bg-slate-800 py-2 pl-8 pr-2 rounded-md border border-slate-700"/><MagnifyingGlassIcon /></div>
                </div>
            </div>

            <div className="bg-slate-800/50 p-4 rounded-lg border border-slate-700 flex items-center gap-4">
                {/* Filters */}
                <div><label className="text-xs text-slate-400">Liquidez ADTV - 90d</label><input type="text" defaultValue="100.000,00" className="mt-1 bg-slate-700 p-2 rounded-md w-40"/></div>
                <div><label className="text-xs text-slate-400">Quantidade de empresas</label><input type="text" defaultValue="10" className="mt-1 bg-slate-700 p-2 rounded-md w-24"/></div>
                <div><label className="text-xs text-slate-400">Período Acumulado</label><input type="text" defaultValue="12 meses" className="mt-1 bg-slate-700 p-2 rounded-md w-32"/></div>
                <div><label className="text-xs text-slate-400">Data</label><input type="text" defaultValue="22/07/2025" className="mt-1 bg-slate-700 p-2 rounded-md w-32"/></div>
                <button className="self-end bg-sky-600 text-white px-6 py-2 rounded-md font-semibold hover:bg-sky-500">Calcular</button>
                 <div className="ml-auto self-end flex items-center gap-2">
                    <button className="bg-slate-700 px-3 py-2 rounded-md">Setores</button>
                    <button className="bg-slate-700 px-3 py-2 rounded-md">Colunas</button>
                 </div>
            </div>

            <div className="overflow-x-auto border border-slate-700 rounded-lg">
                <table className="w-full text-sm text-left text-slate-300">
                    <thead className="text-xs text-slate-400 uppercase bg-slate-700/50">
                        <tr>{columns.map(c => <th key={c} className="px-4 py-3 font-medium whitespace-nowrap">{c}</th>)}</tr>
                    </thead>
                    <tbody>
                        {results.map(item => (
                            <tr key={item.ticker} className="border-b border-slate-700 hover:bg-slate-700/30">
                                {columns.map(colKey => {
                                    const key = colKey.toLowerCase().replace(/ /g, '').replace(/[çã]/g, c => ({'ç':'c', 'ã':'a'})[c] || c);
                                    let value = item[key];
                                    if (typeof value === 'number') {
                                        if (['valor de mercado', 'resultado anualizado'].includes(colKey.toLowerCase())) value = value.toLocaleString('pt-BR', { style: 'currency', currency: 'BRL'});
                                        else value = value.toLocaleString('pt-BR', { minimumFractionDigits: 2, maximumFractionDigits: 2 });
                                    }
                                    return <td key={colKey} className={`px-4 py-2 whitespace-nowrap ${key === 'empresa' ? 'font-semibold text-white' : ''} ${typeof item[key] === 'number' && item[key] > 20 ? 'text-green-400' : ''}`}>{value}</td>
                                })}
                            </tr>
                        ))}
                    </tbody>
                </table>
            </div>
        </div>
    );
    
     const MetricsModal = () => (
        <div className="fixed inset-0 bg-black/60 flex items-center justify-center z-50">
            <div className="bg-slate-800 rounded-lg border border-slate-700 w-full max-w-4xl h-[80vh] flex flex-col">
                <div className="p-4 border-b border-slate-700 flex justify-between items-center">
                    <h2 className="text-xl font-semibold text-white">Métricas</h2>
                    <div className="flex items-center gap-4">
                        <div className="relative w-72"><input type="search" placeholder="Pesquisar" className="bg-slate-700 py-2 pl-8 pr-2 rounded-md w-full"/><MagnifyingGlassIcon /></div>
                        <button onClick={() => setIsModalOpen(false)}><XMarkIcon /></button>
                    </div>
                </div>
                <div className="flex flex-grow overflow-hidden">
                    <div className="w-1/4 border-r border-slate-700 p-2 overflow-y-auto">
                        {metricCategories.map(cat => (
                            <button key={cat.id} onClick={() => setActiveMetricCategory(cat.id)} className={`w-full text-left p-2 my-1 rounded text-sm ${activeMetricCategory === cat.id ? 'bg-sky-600 text-white' : 'hover:bg-slate-700'}`}>{cat.name}</button>
                        ))}
                    </div>
                    <div className="w-3/4 p-4 overflow-y-auto">
                         <h3 className="font-semibold text-white mb-4">{metricCategories.find(c=>c.id === activeMetricCategory)?.name}</h3>
                         <div className="grid grid-cols-2 gap-3">
                            {(metricCategories.find(c => c.id === activeMetricCategory)?.metrics || []).map(metric => (
                                <button key={metric.id} className="w-full p-3 border border-slate-700 rounded-lg text-left text-white hover:bg-slate-700">{metric.name}</button>
                            ))}
                         </div>
                    </div>
                </div>
            </div>
        </div>
     );


    return (
        <div>
            <h1 className="text-2xl font-bold text-white mb-1">Screenings Fundamentalistas <span className="text-xs bg-purple-600 text-white px-2 py-0.5 rounded-full align-middle">BETA</span></h1>
            <p className="text-slate-400 mb-6">Encontre as melhores empresas da bolsa com base em seus critérios.</p>
            
            {view === 'selection' ? <SelectionView /> : <ResultsView />}
            {isModalOpen && <MetricsModal />}
        </div>
    );
};

export default Screening;