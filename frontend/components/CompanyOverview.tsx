// frontend/components/CompanyOverview.tsx

import React, { useState, useEffect } from 'react';
// ... (imports de recharts e icons permanecem os mesmos) ...
import { TechnicalSignal, InsiderDataPoint, RelevantFact, Shareholder, CompanyOverviewData } from '../types'; // Importa o novo tipo
import { BellIcon, ArrowLeftIcon, ArrowTopRightOnSquareIcon, ArrowRightIcon, DocumentTextIcon } from '../constants'; // Adicionado DocumentTextIcon

// --- Seção de Componentes Internos (Tabs) ---
// Os componentes TabButton, FundamentosTab, TecnicoTab e DocumentIcon podem ser mantidos como estavam,
// mas vamos ajustar FundamentosTab para receber os dados da API.

const PIE_COLORS = ['#38bdf8', '#818cf8', '#a78bfa', '#f472b6', '#fb923c', '#4ade80'];

const TabButton: React.FC<{ label: string; isActive: boolean; onClick: () => void }> = ({ label, isActive, onClick }) => (
    <button onClick={onClick} className={`px-4 py-2 text-sm font-semibold rounded-md transition-colors ${isActive ? 'bg-sky-600 text-white' : 'text-slate-300 hover:bg-slate-700'}`}>
        {label}
    </button>
);

// Componente ajustado para receber dados da API
const FundamentosTab: React.FC<{ data: CompanyOverviewData | null }> = ({ data }) => {
    if (!data) return <div className="text-slate-400">Carregando dados fundamentalistas...</div>;

    const formatCurrency = (value: number | undefined) => {
        if (value === undefined || value === null) return 'N/A';
        return `R$ ${(value / 1e9).toFixed(2)}B`; // Formata para bilhões
    };

    // Dados para o grid de fundamentos
    const fundamentalsGrid = {
        'Receita Líquida': formatCurrency(data.financials.receita_liquida?.account_value),
        'Lucro Bruto': formatCurrency(data.financials.lucro_bruto?.account_value),
        'EBIT': formatCurrency(data.financials.ebit?.account_value),
        'Lucro Líquido': formatCurrency(data.financials.lucro_liquido?.account_value),
        'Patrimônio Líquido': formatCurrency(data.financials.patrimonio_liquido?.account_value),
        'Caixa e Equivalentes': formatCurrency(data.financials.disponibilidades?.account_value),
        // Indicadores calculados (placeholders por enquanto)
        'P/L': 'N/A', 'P/VP': 'N/A', 'ROE': 'N/A',
    };

    return (
        <div className="space-y-6 mt-4">
            <div className="bg-slate-800/50 rounded-lg p-6 border border-slate-700">
                <h3 className="text-lg font-semibold text-white mb-4">Principais Indicadores Financeiros (Anual Mais Recente)</h3>
                <div className="grid grid-cols-2 md:grid-cols-3 gap-8">
                    {Object.entries(fundamentalsGrid).map(([key, value]) => (
                         <div key={key} className="flex justify-between text-sm border-b border-slate-700 pb-2">
                            <span className="text-slate-400">{key}</span>
                            <span className="font-semibold text-white">{value}</span>
                         </div>
                    ))}
                </div>
            </div>

            <div className="grid grid-cols-1">
                <div className="bg-slate-800/50 rounded-lg p-6 border border-slate-700">
                    <h3 className="text-lg font-semibold text-white mb-4">Fatos Relevantes Recentes</h3>
                    <div className="space-y-3">
                        {data.relevant_facts.length > 0 ? data.relevant_facts.map((fact) => (
                            <a key={fact.id} href={fact.download_link} target="_blank" rel="noopener noreferrer" className="flex items-center text-sm p-3 rounded-md hover:bg-slate-700/50 transition-colors">
                                <DocumentTextIcon className="w-6 h-6 text-sky-400 flex-shrink-0" />
                                <div className="ml-4 flex-grow">
                                    <p className="font-semibold text-white">{fact.subject}</p>
                                    <p className="text-xs text-slate-400">
                                        Data de Referência: {new Date(fact.reference_date || '').toLocaleDateString('pt-BR')}
                                    </p>
                                </div>
                                <ArrowTopRightOnSquareIcon className="w-4 h-4 text-slate-400 ml-4" />
                            </a>
                        )) : <p className="text-slate-400 text-sm">Nenhum fato relevante recente encontrado.</p>}
                    </div>
                </div>
            </div>
            {/* Outros gráficos como Composição acionária e Insiders seriam adicionados aqui em fases futuras */}
        </div>
    );
};


const TecnicoTab: React.FC = () => (
    <div className="text-center p-8 mt-4">
        <p className="text-slate-400">A aba de Análise Técnica será desenvolvida em uma fase futura.</p>
    </div>
);


// --- COMPONENTE PRINCIPAL ---
const CompanyOverview: React.FC<{ ticker: string }> = ({ ticker }) => {
    const [activeTab, setActiveTab] = useState<'tecnico' | 'fundamentos'>('fundamentos');
    const [overviewData, setOverviewData] = useState<CompanyOverviewData | null>(null);
    const [loading, setLoading] = useState(true);
    const [error, setError] = useState<string | null>(null);

    useEffect(() => {
        const fetchOverviewData = async () => {
            if (!ticker) return;
            
            setLoading(true);
            setError(null);
            try {
                const response = await fetch(`/api/financials/overview/${ticker}`);
                if (!response.ok) {
                    const errData = await response.json();
                    throw new Error(errData.error || `Erro ${response.status}`);
                }
                const data: CompanyOverviewData = await response.json();
                setOverviewData(data);
            } catch (err) {
                setError(err instanceof Error ? err.message : 'Ocorreu um erro desconhecido');
            } finally {
                setLoading(false);
            }
        };

        fetchOverviewData();
    }, [ticker]);

    if (loading) {
        return <div className="text-center text-slate-400 p-8">Carregando dados de {ticker}...</div>;
    }

    if (error) {
        return <div className="bg-red-900/50 border border-red-700 text-red-300 p-4 rounded-lg text-center">Erro ao carregar dados: {error}</div>;
    }
    
    if (!overviewData) {
        return <div className="text-center p-8">Nenhum dado encontrado para {ticker}.</div>
    }
    
    const { company, quote } = overviewData;
    const price = quote?.last_price ?? 0;
    const change = quote ? ((quote.last_price / quote.previous_close) - 1) * 100 : 0;
    const isNegative = change < 0;

    return (
        <div className="space-y-6">
            <div className="flex justify-between items-center">
                <div className="flex items-center gap-4">
                    <span className="text-3xl font-bold text-white">{ticker.toUpperCase()}</span>
                    <div>
                        <h2 className="text-lg font-semibold text-white">{company?.name}</h2>
                        <p className={`font-semibold ${isNegative ? 'text-red-400' : 'text-green-400'}`}>
                            R$ {price.toFixed(2)} ({change.toFixed(2)}%)
                        </p>
                    </div>
                </div>
                {/* ... botões de sino e voltar ... */}
            </div>

            <div className="flex items-center gap-2 p-1 bg-slate-800 border border-slate-700 rounded-lg self-start">
                <TabButton label="Técnico" isActive={activeTab === 'tecnico'} onClick={() => setActiveTab('tecnico')} />
                <TabButton label="Fundamentos" isActive={activeTab === 'fundamentos'} onClick={() => setActiveTab('fundamentos')} />
            </div>

            {activeTab === 'tecnico' ? <TecnicoTab /> : <FundamentosTab data={overviewData} />}
        </div>
    );
};

export default CompanyOverview;