import React, { useState } from 'react';
import { SectorNode, StockGuideData } from '../types';
import { sectorTreeData, mockStockGuideData } from '../constants';

const SectorNodeComponent: React.FC<{ node: SectorNode; onSelect: (sector: string) => void; isRoot?: boolean }> = ({ node, onSelect, isRoot = false }) => {
    const hasChildren = node.children && node.children.length > 0;

    const buttonClass = `
        text-white rounded-lg shadow-lg transition-all duration-300 transform hover:-translate-y-1 cursor-pointer
        ${isRoot ? 'px-8 py-3 bg-gradient-to-br from-slate-700 to-slate-800 border-2 border-slate-600' : 'px-6 py-2 bg-gradient-to-br from-sky-700 to-sky-900 border border-sky-600'}
        hover:shadow-sky-500/50
    `;

    return (
        <div className="flex flex-col items-center">
            <button
                onClick={() => onSelect(node.name)}
                className={buttonClass}
            >
                {node.name}
            </button>
            {hasChildren && (
                <div className="flex items-start mt-8 gap-8 relative">
                    <div className="absolute top-[-2rem] left-1/2 -translate-x-1/2 w-px h-8 bg-slate-600"></div>
                     {node.children && node.children.length > 1 && (
                      <div className="absolute top-[-2.05rem] left-1/4 w-1/2 h-px bg-slate-600"></div>
                    )}
                    {node.children?.map((child, index) => (
                        <div key={index} className="flex flex-col items-center relative">
                             <div className="absolute top-[-2rem] left-1/2 -translate-x-1/2 w-px h-8 bg-slate-600"></div>
                            <SectorNodeComponent node={child} onSelect={onSelect} />
                        </div>
                    ))}
                </div>
            )}
        </div>
    );
};

const DataBar: React.FC<{ value: number | string; max: number }> = ({ value, max }) => {
    if (typeof value !== 'number') return <span className="text-slate-400">{value}</span>;
    const percentage = (Math.abs(value) / max) * 100;
    const isPositive = value >= 0;

    return (
        <div className="relative w-full h-5 bg-slate-700/50 rounded-sm overflow-hidden">
            <div
                className={`absolute h-full ${isPositive ? 'bg-sky-600' : 'bg-red-600'}`}
                style={{ width: `${percentage}%` }}
            ></div>
            <span className="absolute inset-0 text-center text-xs font-semibold text-white flex items-center justify-center">
                {value.toFixed(0)}%
            </span>
        </div>
    );
};

const StockGuideTable: React.FC<{ data: StockGuideData[] }> = ({ data }) => {
    const headers = [
        { name: 'Dados Gerais', span: 2 },
        { name: 'Market Cap (R$ mn)', span: 1 },
        { name: 'Volume Negociado (R$ mn)', span: 2 },
        { name: 'Preço (R$)', span: 3 },
        { name: 'Performance (%)', span: 3 },
        { name: 'P/L', span: 2 },
        { name: 'EV/EBITDA', span: 2 },
        { name: 'P/VP', span: 2 },
        { name: 'Dividend Yield (%)', span: 2 },
        { name: 'Dívida Líquida/EBITDA', span: 2 },
        { name: 'Roe (%)', span: 2 },
    ];
    
    const subHeaders = ['Ticker', 'Rating', '', 'Média (12M)', '% da Média', 'Último', 'Alvo', 'Upside (%)', 'Semana', 'Mês', 'Ano', '2025E', '2026E', '2025E', '2026E', '2025E', '2026E', '2025E', '2026E', '2025E', '2026E', '2025E', '2026E'];

    const performanceMax = Math.max(...data.map(d => typeof d.performance.semana === 'number' ? Math.abs(d.performance.semana) : 0).concat(data.map(d => typeof d.performance.mes === 'number' ? Math.abs(d.performance.mes) : 0)).concat(data.map(d => typeof d.performance.ano === 'number' ? Math.abs(d.performance.ano) : 0)));
    const upsideMax = Math.max(...data.map(d => typeof d.price.upside === 'number' ? Math.abs(d.price.upside) : 0));

    const groupedData = data.reduce((acc, item) => {
        (acc[item.sector] = acc[item.sector] || []).push(item);
        return acc;
    }, {} as Record<string, StockGuideData[]>);

    const formatValue = (value: number | string, isCurrency = false, isPercent = false) => {
        if (value === 'n.a.') return <span className="text-slate-500">{value}</span>;
        if (typeof value !== 'number') return value;
        
        let formatted = value.toLocaleString('pt-BR', { minimumFractionDigits: 1, maximumFractionDigits: 1 });
        if(isCurrency) formatted = value.toLocaleString('pt-BR');
        
        return `${formatted}${isPercent ? '%' : ''}`;
    }

    return (
        <div className="overflow-x-auto">
            <table className="w-full text-xs text-left whitespace-nowrap">
                <thead className="text-white bg-[#1a2c49] sticky top-0 z-20">
                    <tr>
                        {headers.map((h, i) => (
                            <th key={i} colSpan={h.span} className="p-2 font-semibold text-center border-x border-slate-700">{h.name}</th>
                        ))}
                    </tr>
                    <tr>
                        {subHeaders.map((sh, i) => (
                             <th key={i} className={`p-2 font-normal bg-slate-700/50 ${['', 'Média (12M)', 'Último', 'Semana', '2025E'].includes(sh) ? 'border-l' : ''} border-r border-slate-600`}>{sh}</th>
                        ))}
                    </tr>
                </thead>
                <tbody className="text-slate-300">
                    {Object.entries(groupedData).map(([sector, items]) => (
                        <React.Fragment key={sector}>
                            <tr className="bg-slate-700/50">
                                <td colSpan={subHeaders.length} className="p-1.5 font-bold text-white text-sm">{sector}</td>
                            </tr>
                            {items.map((item, index) => (
                                <tr key={index} className={`border-b border-slate-800 ${item.isMedian ? 'bg-slate-700 font-bold text-white' : 'hover:bg-slate-700/30'}`}>
                                    <td className="p-1.5">{item.company}</td>
                                    <td className="p-1.5">{item.ticker}</td>
                                    <td className="p-1.5">{item.rating}</td>
                                    <td className="p-1.5 text-right">{formatValue(item.marketCap, true)}</td>
                                    <td className="p-1.5 text-right">{formatValue(item.volume.media12M, true)}</td>
                                    <td className="p-1.5 text-right">{formatValue(item.volume.pctMedia, false, true)}</td>
                                    <td className="p-1.5 text-right">{formatValue(item.price.ultimo)}</td>
                                    <td className="p-1.5 text-right">{formatValue(item.price.alvo)}</td>
                                    <td className="p-1.5"><DataBar value={item.price.upside} max={upsideMax} /></td>
                                    <td className="p-1.5"><DataBar value={item.performance.semana} max={performanceMax} /></td>
                                    <td className="p-1.5"><DataBar value={item.performance.mes} max={performanceMax} /></td>
                                    <td className="p-1.5"><DataBar value={item.performance.ano} max={performanceMax} /></td>
                                    <td className="p-1.5 text-right">{formatValue(item.pl['2025E'])}x</td>
                                    <td className="p-1.5 text-right">{formatValue(item.pl['2026E'])}x</td>
                                    <td className="p-1.5 text-right">{formatValue(item.evEbitda['2025E'])}x</td>
                                    <td className="p-1.5 text-right">{formatValue(item.evEbitda['2026E'])}x</td>
                                    <td className="p-1.5 text-right">{formatValue(item.pvp['2025E'])}x</td>
                                    <td className="p-1.5 text-right">{formatValue(item.pvp['2026E'])}x</td>
                                    <td className="p-1.5 text-right">{formatValue(item.dividendYield['2025E'], false, true)}</td>
                                    <td className="p-1.5 text-right">{formatValue(item.dividendYield['2026E'], false, true)}</td>
                                    <td className="p-1.5 text-right">{formatValue(item.dividaLiquidaEbitda['2025E'])}x</td>
                                    <td className="p-1.5 text-right">{formatValue(item.dividaLiquidaEbitda['2026E'])}x</td>
                                    <td className="p-1.5 text-right">{formatValue(item.roe['2025E'], false, true)}</td>
                                    <td className="p-1.5 text-right">{formatValue(item.roe['2026E'], false, true)}</td>
                                </tr>
                            ))}
                        </React.Fragment>
                    ))}
                </tbody>
            </table>
        </div>
    );
};


const SellSideData: React.FC = () => {
    const [view, setView] = useState<'guide' | 'table'>('guide');
    const [selectedNode, setSelectedNode] = useState<string | null>(null);

    const handleSelectNode = (nodeName: string) => {
        setSelectedNode(nodeName);
        setView('table');
    };
    
    const getSubSectors = (nodeName: string): string[] => {
        const findNode = (nodes: SectorNode[]): SectorNode | null => {
            for (const node of nodes) {
                if (node.name === nodeName) return node;
                if (node.children) {
                    const found = findNode(node.children);
                    if (found) return found;
                }
            }
            return null;
        };
        const node = findNode(sectorTreeData);
        if (!node) return [];
        
        let subSectors: string[] = [];
        const collectNames = (n: SectorNode) => {
            if (!n.children || n.children.length === 0) {
                 subSectors.push(n.name);
            } else {
                n.children.forEach(collectNames);
            }
        };
        collectNames(node);
        return subSectors;
    }

    const filteredData = selectedNode 
        ? mockStockGuideData.filter(d => getSubSectors(selectedNode).includes(d.sector)) 
        : [];

    const renderGuide = () => (
        <div className="bg-slate-800/50 p-8 rounded-lg border border-slate-700">
             <div className="flex justify-between items-center mb-12">
                <h1 className="text-4xl font-bold text-white">Stock Guide</h1>
                <span className="text-lg text-slate-400">21 de julho de 2025</span>
            </div>
            <div className="flex justify-center">
                 <div className="flex flex-col items-center p-8 bg-slate-900/50 rounded-2xl border-2 border-slate-700/50">
                    <div className="mb-8 px-6 py-2 border-2 border-slate-600 rounded-lg text-white font-semibold">Setores</div>
                    <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-3 gap-x-24 gap-y-16">
                        {sectorTreeData.map((sector, index) => (
                            <SectorNodeComponent key={index} node={sector} onSelect={handleSelectNode} isRoot={true} />
                        ))}
                    </div>
                 </div>
            </div>
        </div>
    );

    return (
        <div>
            {view === 'guide' ? (
                renderGuide()
            ) : (
                <div className="bg-slate-800/50 p-6 rounded-lg border border-slate-700">
                    <div className="flex justify-between items-center mb-4">
                        <h2 className="text-2xl font-bold text-white">Stock Guide: {selectedNode}</h2>
                        <button onClick={() => setView('guide')} className="text-sm font-semibold text-sky-400 hover:text-sky-300">
                            &larr; Voltar ao Guia de Setores
                        </button>
                    </div>
                    <StockGuideTable data={filteredData} />
                </div>
            )}
        </div>
    );
};

export default SellSideData;