import React from 'react';
import { CvmDocument } from '../types';
import { DocumentTextIcon, ChevronDownIcon, ArrowTopRightOnSquareIcon } from '../constants';

const mockDocuments: CvmDocument[] = [
    { id: '1', date: '18/07/2025', company: 'PRIO S.A.', category: 'Comunicado ao Mercado', subject: '', link: '#' },
    { id: '2', date: '18/07/2025', company: 'PRIO S.A.', category: 'Fato Relevante', subject: '', link: '#' },
    { id: '3', date: '17/07/2025', company: 'PRIO S.A.', category: 'Calendário de Eventos Corporativos', subject: '', link: '#' },
    { id: '4', date: '16/07/2025', company: 'PRIO S.A.', category: 'Fato Relevante', subject: 'Liquidação da 6ª Emissão de Debêntures', link: '#' },
    { id: '5', date: '04/07/2025', company: 'PRIO S.A.', category: 'Fato Relevante', subject: '', link: '#' },
    { id: '6', date: '04/07/2025', company: 'PRIO S.A.', category: 'Reunião da Administração', subject: 'Aditamento - 6ª Emissão Debêntures', link: '#' },
    { id: '7', date: '03/07/2025', company: 'PRIO S.A.', category: 'Valores Mobiliários negociados e detidos (art. 11 da Instr. CVM nº 358)', subject: '', link: '#' },
    { id: '8', date: '03/07/2025', company: 'PRIO S.A.', category: 'Comunicado ao Mercado', subject: 'Dados Operacionais - Junho/2025', link: '#' },
    { id: '9', date: '03/07/2025', company: 'PRIO S.A.', category: 'Valores Mobiliários negociados e detidos (art. 11 da Instr. CVM nº 358)', subject: '', link: '#' },
    { id: '10', date: '30/06/2025', company: 'PRIO S.A.', category: 'Relatório de Sustentabilidade', subject: '', link: '#' },
];

const FilterDropdown: React.FC<{ label: string; options: string[]; selected: string; className?: string; selectedClassName?: string }> = 
({ label, options, selected, className, selectedClassName }) => {
    return (
        <div>
            <label className="block text-sm font-medium text-slate-400 mb-1">{label}</label>
            <div className="relative">
                <select defaultValue={selected} className={`w-full appearance-none bg-slate-700 border border-slate-600 rounded-md py-2 px-3 text-slate-200 focus:outline-none focus:ring-2 focus:ring-sky-500 focus:border-sky-500 ${className} ${selectedClassName}`}>
                    {options.map(opt => <option key={opt}>{opt}</option>)}
                </select>
                <div className="pointer-events-none absolute inset-y-0 right-0 flex items-center px-2 text-slate-400">
                    <ChevronDownIcon />
                </div>
            </div>
        </div>
    );
};


const CvmDocuments: React.FC = () => {
    return (
        <div className="bg-slate-800/50 rounded-lg p-6 md:p-8 space-y-6 border border-slate-700">
            <div className="flex items-center gap-3">
                <DocumentTextIcon className="w-8 h-8 text-sky-400" />
                <h1 className="text-3xl font-bold text-white">Documentos CVM</h1>
            </div>

            <div className="border-b border-slate-700 pb-6">
                <h2 className="text-xl font-semibold text-white mb-4">Filtros</h2>
                <div className="grid grid-cols-1 md:grid-cols-3 gap-6">
                    <FilterDropdown 
                        label="Filtrar por Empresa" 
                        options={['PRIO3 - PRIO S.A.', 'PETR4 - PETROBRAS', 'VALE3 - VALE']}
                        selected="PRIO3 - PRIO S.A."
                        selectedClassName="border-red-500 ring-1 ring-red-500"
                    />
                    <FilterDropdown 
                        label="Filtrar por Categoria"
                        options={['Todas', 'Fato Relevante', 'Comunicado ao Mercado', 'Calendário de Eventos Corporativos']}
                        selected="Todas"
                    />
                     <div>
                        <label className="block text-sm font-medium text-slate-400 mb-1">Filtrar por Período de Publicação</label>
                        <input 
                            type="text" 
                            defaultValue="2025/04/23 – 2025/07/22"
                            className="w-full bg-slate-700 border border-slate-600 rounded-md py-2 px-3 text-slate-200 focus:outline-none focus:ring-2 focus:ring-sky-500 focus:border-sky-500"
                        />
                    </div>
                </div>
            </div>

            <div>
                <p className="text-md font-semibold text-white mb-4">
                    Exibindo {mockDocuments.length} documentos encontrados
                </p>
                <div className="overflow-x-auto border border-slate-700 rounded-lg">
                    <table className="w-full text-sm text-left">
                        <thead className="bg-slate-700/50 text-xs text-slate-400 uppercase">
                            <tr>
                                {['Data', 'Empresa', 'Categoria', 'Assunto', 'Link'].map(h => (
                                    <th key={h} scope="col" className="px-6 py-3 font-medium tracking-wider">{h}</th>
                                ))}
                            </tr>
                        </thead>
                        <tbody className="divide-y divide-slate-700">
                            {mockDocuments.map((doc) => (
                                <tr key={doc.id} className="hover:bg-slate-700/30">
                                    <td className="px-6 py-4 whitespace-nowrap text-slate-300">{doc.date}</td>
                                    <td className="px-6 py-4 whitespace-nowrap font-medium text-white">{doc.company}</td>
                                    <td className="px-6 py-4 whitespace-nowrap text-slate-300">{doc.category}</td>
                                    <td className="px-6 py-4 whitespace-nowrap text-slate-300">{doc.subject}</td>
                                    <td className="px-6 py-4 whitespace-nowrap">
                                        <a href={doc.link} target="_blank" rel="noopener noreferrer" className="flex items-center gap-1 text-sky-400 hover:text-sky-300 font-semibold">
                                            Abrir
                                            <ArrowTopRightOnSquareIcon className="w-4 h-4" />
                                        </a>
                                    </td>
                                </tr>
                            ))}
                        </tbody>
                    </table>
                </div>
            </div>
        </div>
    );
};

export default CvmDocuments;