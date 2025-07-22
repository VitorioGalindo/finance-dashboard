
import React, { useState } from 'react';
import { FinancialHistoryRow } from '../types';
import { InformationCircleIcon, ChevronUpIcon } from '../constants';

const years = [2017, 2018, 2019, 2020, 2021, 2022, 2023, 2024, 'TTM'];

const mockFinancialData: FinancialHistoryRow[] = [
    { id: 'dre', metric: 'Histórico de DRE', level: 0, isHeader: true, data: {} },
    {
        id: 'receita_liquida', metric: 'Receita líquida de vendas', level: 1, data: {
            2017: { value: 532.12, variance: 180.05 }, 2018: { value: 1644.33, variance: 100.00 },
            2019: { value: 1390.93, variance: -57.75 }, 2020: { value: 1803.94, variance: 130.00 },
            2021: { value: 4799.47, variance: 130.00 }, 2022: { value: 6302.48, variance: 100.00 },
            2023: { value: 11905.04, variance: 100.00 }, 2024: { value: 14268.65, variance: 88.04 },
            TTM: { value: 15681.28 }
        },
        subRows: [
            { id: 'custo_bens', metric: 'Custo dos bens e/ou serviços vendidos', level: 2, data: {
                2017: { value: -230.12, variance: 100.00 }, 2018: { value: -424.49, variance: 70.00 },
                2019: { value: -624.09, variance: 41.00 }, 2020: { value: -446.98, variance: -34.88 },
                2021: { value: -1286.93, variance: 105.00 }, 2022: { value: -3194.30, variance: 101.55 },
                2023: { value: -7569.80, variance: 23.32 }, 2024: { value: -8624.78, variance: 60.02 },
                TTM: { value: -9692.15 }
            }},
        ]
    },
    { id: 'lucro_bruto', metric: 'Lucro bruto', level: 1, data: {
        2017: { value: 324.40, variance: 160.00 }, 2018: { value: 1122.97, variance: 702.87 },
        2019: { value: 765.91, variance: -12.22 }, 2020: { value: 917.26, variance: 69.43 },
        2021: { value: 3672.26, variance: 59.63 }, 2022: { value: 4220.17, variance: 79.91 },
        2023: { value: 7690.90, variance: 78.68 }, 2024: { value: 6664.92, variance: 4.90 },
        TTM: { value: 6802.15 }
    }},
    { id: 'despesas_operacionais', metric: 'Despesas com vendas', level: 1, data: {
        2017: { value: 0.00, variance: 0.00 }, 2018: { value: 0.00, variance: 0.00 },
        2019: { value: -245.71, variance: -14.94 }, 2020: { value: -277.54, variance: -16.44 },
        2021: { value: -315.64, variance: -26.70 }, 2022: { value: -267.38, variance: -7.17 },
        2023: { value: -477.17, variance: -21.78 }, 2024: { value: -682.17, variance: -21.17 },
        TTM: { value: -686.15 }
    }},
    { id: 'bp', metric: 'Balanço Patrimonial', level: 0, isHeader: true, data: {} },
    { id: 'ativo_total', metric: 'Ativo Total', level: 1, data: {
        2017: { value: 1891.44, variance: 48.30 }, 2018: { value: 2720.16, variance: 8.18 },
        2019: { value: 8940.38, variance: 70.53 }, 2020: { value: 18839.27, variance: 71.91 },
        2021: { value: 27111.41, variance: 61.68 }, 2022: { value: 50962.53, variance: 82.23 },
        2023: { value: 70107.50, variance: 3.93 }, 2024: { value: 83954.16, variance: 7.16 },
        TTM: { value: 92926.33 }
    }},
    { id: 'ativo_circulante', metric: 'Ativo circulante', level: 1, data: {
        2017: { value: 234.30, variance: 42.40 }, 2018: { value: 929.40, variance: 22.70 },
        2019: { value: 2795.70, variance: 76.50 }, 2020: { value: 9161.20, variance: 116.70 },
        2021: { value: 15124.90, variance: 98.11 }, 2022: { value: 30062.60, variance: 111.90 },
        2023: { value: 18104.50, variance: -28.92 }, 2024: { value: 27072.80, variance: 4.10 },
        TTM: { value: 27851.36 }
    }},
];

const QuickAccessButton: React.FC<{ label: string; onClick: () => void }> = ({ label, onClick }) => (
    <button
        onClick={onClick}
        className="px-3 py-1.5 text-xs font-semibold text-slate-200 bg-slate-700/50 rounded-full hover:bg-slate-600 transition-colors"
    >
        {label}
    </button>
);


const HistoricalData: React.FC<{ ticker: string }> = ({ ticker }) => {
    const [expandedRows, setExpandedRows] = useState<Set<string>>(new Set(['receita_liquida']));

    const toggleRow = (rowId: string) => {
        setExpandedRows(prev => {
            const newSet = new Set(prev);
            if (newSet.has(rowId)) {
                newSet.delete(rowId);
            } else {
                newSet.add(rowId);
            }
            return newSet;
        });
    };
    
    const scrollToSection = (sectionId: string) => {
        const element = document.getElementById(`section-${sectionId}`);
        if(element) {
            element.scrollIntoView({ behavior: 'smooth', block: 'center' });
        }
    }


    const renderRow = (row: FinancialHistoryRow) => {
        const isExpanded = expandedRows.has(row.id);
        
        if (row.isHeader) {
            return (
                 <tr id={`section-${row.id}`} key={row.id} className="bg-slate-700/60 sticky-header">
                    <td colSpan={years.length * 2 + 1} className="px-4 py-2 text-sm font-bold text-white uppercase tracking-wider">
                        {row.metric}
                    </td>
                </tr>
            )
        }
        
        const formatValue = (value: any) => {
            if (value === null || value === undefined) return '-';
            if (typeof value === 'number') {
                 if (Number.isInteger(value)) return value.toLocaleString('pt-BR');
                 return value.toLocaleString('pt-BR', { minimumFractionDigits: 2, maximumFractionDigits: 2 });
            }
            return value;
        }

        const formatVariance = (value: any) => {
            if (value === null || value === undefined) return '-';
            return `${value.toFixed(2)}%`;
        }

        const varianceColor = (value: any) => {
            if (value === null || value === undefined) return 'text-slate-400';
            return value > 0 ? 'text-green-400' : 'text-red-400';
        }
        
        return (
            <React.Fragment key={row.id}>
                <tr className="border-b border-slate-700/50 hover:bg-slate-800/60">
                    <td className="px-4 py-2.5 text-sm font-medium text-white whitespace-nowrap bg-slate-800/80 backdrop-blur-sm sticky left-0 z-10" style={{ paddingLeft: `${row.level * 1.5}rem` }}>
                        <div className="flex items-center gap-2">
                           {row.subRows && (
                                <button onClick={() => toggleRow(row.id)} className="text-slate-400 hover:text-white">
                                    <ChevronUpIcon className={`w-4 h-4 transition-transform ${isExpanded ? '' : 'transform rotate-180'}`} />
                                </button>
                            )}
                            <span className={!row.subRows ? 'pl-6' : ''}>{row.metric}</span>
                            <InformationCircleIcon className="w-4 h-4 text-slate-500 hover:text-sky-400 cursor-pointer" />
                        </div>
                    </td>
                    {years.map(year => (
                        <React.Fragment key={year}>
                            <td className="px-4 py-2.5 text-sm text-right text-slate-200 whitespace-nowrap">
                                {formatValue(row.data[year]?.value)}
                            </td>
                            {year !== 'TTM' && (
                                <td className={`px-4 py-2.5 text-sm text-right whitespace-nowrap ${varianceColor(row.data[year]?.variance)}`}>
                                    {formatVariance(row.data[year]?.variance)}
                                </td>
                            )}
                        </React.Fragment>
                    ))}
                    {/* Empty cell for TTM variance */}
                     {years.includes('TTM') && <td className="px-4 py-2.5"></td>}
                </tr>
                {isExpanded && row.subRows && row.subRows.map(subRow => renderRow(subRow))}
            </React.Fragment>
        );
    };

    return (
        <div className="space-y-6">
            <div className="flex justify-between items-start">
                <div>
                    <h1 className="text-2xl font-bold text-white">{ticker} - PETRORIO</h1>
                    <p className="text-sm text-slate-400">Petróleo, Gás e Biocombustíveis</p>
                </div>
                <div className="flex items-center gap-2">
                     <button className="px-4 py-2 text-sm font-semibold text-white bg-slate-700/50 border border-slate-600 rounded-md hover:bg-slate-700">Adicione a watchlist</button>
                     <button className="px-4 py-2 text-sm font-semibold text-white bg-slate-700/50 border border-slate-600 rounded-md hover:bg-slate-700">Peça um alalce</button>
                     <button className="px-4 py-2 text-sm font-semibold text-white bg-sky-600 rounded-md hover:bg-sky-500">Visão Geral</button>
                </div>
            </div>

            <div className="grid grid-cols-2 md:grid-cols-4 lg:grid-cols-6 gap-4 text-center">
                 <div><p className="text-sm text-slate-400">Valor de Ação</p><p className="text-xl font-bold text-white">R$ 42,66</p></div>
                 <div><p className="text-sm text-slate-400">LPA</p><p className="text-xl font-bold text-white">12,94</p></div>
                 <div><p className="text-sm text-slate-400">VPA</p><p className="text-xl font-bold text-white">29,66</p></div>
            </div>

            <div className="bg-slate-800/50 rounded-lg p-4 border border-slate-700">
                <div className="flex justify-between items-center mb-4">
                    <div className="flex items-center gap-2">
                        <span className="text-sm font-semibold text-white">Acesso rápido</span>
                        <QuickAccessButton label="Histórico de DRE" onClick={() => scrollToSection('dre')} />
                        <QuickAccessButton label="Balanço patrimonial" onClick={() => scrollToSection('bp')} />
                    </div>
                     <div className="flex items-center gap-2">
                        <span className="text-sm font-semibold text-white">Tipos de análise</span>
                        <button className="px-3 py-1.5 text-xs font-semibold text-slate-200 bg-slate-700 rounded-md hover:bg-slate-600">Análise Horizontal</button>
                        <button className="px-3 py-1.5 text-xs font-semibold text-slate-200 bg-slate-700 rounded-md hover:bg-slate-600">Análise Vertical</button>
                    </div>
                </div>
                <div className="overflow-x-auto border border-slate-700 rounded-lg">
                    <table className="w-full text-sm text-left text-slate-300">
                        <thead className="text-xs text-slate-400 uppercase bg-slate-700/50 sticky top-0 z-20">
                            <tr>
                                <th scope="col" className="px-4 py-3 font-medium whitespace-nowrap bg-slate-800/80 backdrop-blur-sm sticky left-0 z-10">Histórico de DRE</th>
                                {years.map(year => (
                                    <React.Fragment key={year}>
                                        <th scope="col" className="px-4 py-3 font-medium text-right whitespace-nowrap">{year}</th>
                                        {year !== 'TTM' && <th scope="col" className="px-4 py-3 font-medium text-right whitespace-nowrap">H - var%</th>}
                                    </React.Fragment>
                                ))}
                                {/* Empty header for TTM variance */}
                                {years.includes('TTM') && <th className="px-4 py-3"></th>}
                            </tr>
                        </thead>
                        <tbody className="divide-y divide-slate-700/50">
                            {mockFinancialData.map(row => renderRow(row))}
                        </tbody>
                    </table>
                </div>
            </div>
        </div>
    );
};

export default HistoricalData;