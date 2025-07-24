
import React, { useState, useEffect } from 'react';
import { FundamentalIndicator, FinancialStatementItem } from '../types';

// Tipos para o resultado da API /api/financials/overview/<ticker_symbol>
interface CompanyOverviewData {
    company: {
        cnpj: string;
        name: string;
        created_at: string;
        updated_at: string;
    } | null;
    quote: {
        ticker: string;
        last_price: number;
        previous_close: number;
        updated_at: string;
    } | null;
    relevant_facts: {
        id: number;
        company_cnpj: string;
        company_name: string;
        cvm_code: string;
        category: string;
        doc_type: string;
        species: string;
        subject: string;
        reference_date: string;
        delivery_date: string;
        delivery_protocol: string;
        download_link: string;
    }[];
    financials: {
        [key: string]: {
            id: number;
            company_cnpj: string;
            company_name: string;
            cvm_code: string;
            report_version: number;
            reference_date: string;
            fiscal_year_start: string;
            fiscal_year_end: string;
            account_code: string;
            account_description: string;
            account_value: number;
            currency_scale: string;
            currency: string;
            fiscal_year_order: string;
            report_type: string;
            period: string;
        };
    };
}

// Mapeamento de chaves da API para nomes amigáveis para exibição no DRE/Balanço
const FINANCIAL_ITEM_MAP: { [key: string]: string } = {
    'receita_liquida': 'Receita Líquida',
    'lucro_bruto': 'Lucro Bruto',
    'ebit': 'EBIT',
    'lucro_liquido': 'Lucro Líquido',
    'patrimonio_liquido': 'Patrimônio Líquido',
    'divida_bruta': 'Dívida Bruta',
    'divida_liquida': 'Dívida Líquida',
    'disponibilidades': 'Disponibilidades',
};

// Função para formatar números grandes em uma forma mais legível (ex: 1.23T, 45.6B, 789M)
const formatValue = (value: number | null): string => {
    if (value === null) return 'N/A';
    if (Math.abs(value) >= 1e12) {
        return `R$ ${(value / 1e12).toFixed(2)}T`;
    }
    if (Math.abs(value) >= 1e9) {
        return `R$ ${(value / 1e9).toFixed(2)}B`;
    }
    if (Math.abs(value) >= 1e6) {
        return `R$ ${(value / 1e6).toFixed(2)}M`;
    }
    if (Math.abs(value) >= 1e3) {
        return `R$ ${(value / 1e3).toFixed(2)}K`;
    }
    return `R$ ${value.toFixed(2)}`;
};


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

const StatementTable: React.FC<{ title: string; data: FinancialStatementItem[]; isLoading: boolean }> = ({ title, data, isLoading }) => (
    <div className="bg-slate-800/50 rounded-lg p-6 border border-slate-700">
        <h3 className="text-lg font-semibold text-white mb-4">{title}</h3>
        {isLoading ? (
            <div className="text-center text-slate-400">Carregando...</div>
        ) : data.length > 0 ? (
            <table className="w-full text-sm text-left text-slate-300">
                <tbody>
                    {data.map(item => (
                        <tr key={item.item} className="border-b border-slate-700 last:border-b-0">
                            <td className="py-3 pr-4 font-medium">{item.item}</td>
                            <td className="py-3 text-right font-semibold text-white">{item.value}</td>
                        </tr>
                    ))}
                </tbody>
            </table>
        ) : (
             <div className="text-center text-slate-500">Dados não disponíveis.</div>
        )}
    </div>
);


const Fundamentalist: React.FC = () => {
    const [ticker, setTicker] = useState('PETR4'); // Ticker padrão
    const [overviewData, setOverviewData] = useState<CompanyOverviewData | null>(null);
    const [dreData, setDreData] = useState<FinancialStatementItem[]>([]);
    const [balanceSheetData, setBalanceSheetData] = useState<FinancialStatementItem[]>([]);
    const [loading, setLoading] = useState(false);
    const [error, setError] = useState<string | null>(null);

    const handleAnalyse = async () => {
        if (!ticker) {
            setError('Ticker é necessário para a busca.');
            return;
        }
        setLoading(true);
        setError(null);
        setOverviewData(null); // Limpa dados antigos
        setDreData([]);
        setBalanceSheetData([]);

        try {
            // --- CORREÇÃO: Usa a nova rota de overview ---
            const response = await fetch(`/api/financials/overview/${ticker}`);
            if (!response.ok) {
                const errorData = await response.json();
                throw new Error(errorData.error || `Erro na API: ${response.statusText}`);
            }
            const data: CompanyOverviewData = await response.json();
            setOverviewData(data);
            
            // Processa os dados financeiros para exibição nas tabelas
            const currentDre: FinancialStatementItem[] = [];
            const currentBalanceSheet: FinancialStatementItem[] = [];

            if (data.financials) {
                // Filtra e mapeia as contas para DRE e Balanço
                Object.entries(data.financials).forEach(([key, statement]) => {
                    if (FINANCIAL_ITEM_MAP[key]) {
                        if (['receita_liquida', 'lucro_bruto', 'ebit', 'lucro_liquido'].includes(key)) {
                            currentDre.push({
                                item: FINANCIAL_ITEM_MAP[key],
                                value: formatValue(statement.account_value),
                            });
                        } else if (['patrimonio_liquido', 'divida_bruta', 'divida_liquida', 'disponibilidades'].includes(key)) {
                             currentBalanceSheet.push({
                                item: FINANCIAL_ITEM_MAP[key],
                                value: formatValue(statement.account_value),
                            });
                        }
                    }
                });
            }

            setDreData(currentDre);
            setBalanceSheetData(currentBalanceSheet);

        } catch (err) {
            setError(err instanceof Error ? err.message : 'Ocorreu um erro desconhecido');
            setOverviewData(null);
            setDreData([]);
            setBalanceSheetData([]);
        } finally {
            setLoading(false);
        }
    };

    // Busca inicial ao carregar o componente
    useEffect(() => {
      handleAnalyse();
    }, []);

    const handleTickerChange = (e: React.ChangeEvent<HTMLInputElement>) => {
        setTicker(e.target.value.toUpperCase());
    };

    // Dados mockados para indicadores (ainda sem cálculo no backend)
     const mockIndicators: FundamentalIndicator[] = [
        { label: 'P/L', value: 'N/A' },
        { label: 'P/VP', value: 'N/A' },
        { label: 'Dividend Yield', value: 'N/A' },
        { label: 'ROE', value: 'N/A' },
        { label: 'ROIC', value: 'N/A' },
        { label: 'Dív. Líquida/EBITDA', value: 'N/A' },
        { label: 'Margem Bruta', value: 'N/A' },
        { label: 'Margem Líquida', value: 'N/A' },
    ];


    return (
        <div className="space-y-6">
            <div className="flex flex-wrap justify-between items-center gap-4">
                <h2 className="text-xl font-semibold text-white">Análise Fundamentalista</h2>
                <div className="flex items-center gap-2">
                    <input 
                        type="text" 
                        value={ticker}
                        onChange={handleTickerChange}
                        placeholder="Ex: PETR4"
                        className="bg-slate-700 border border-slate-600 rounded-md py-1.5 px-3 w-32 text-white placeholder-slate-400 focus:outline-none focus:ring-1 focus:ring-sky-500"
                    />
                    <button 
                      onClick={handleAnalyse}
                      disabled={loading || !ticker}
                      className="bg-sky-600 text-white px-4 py-1.5 rounded-md text-sm font-semibold hover:bg-sky-500 disabled:bg-slate-500 disabled:cursor-not-allowed"
                    >
                        {loading ? 'Analisando...' : 'Analisar'}
                    </button>
                </div>
            </div>

            {error && <div className="bg-red-900/50 border border-red-700 text-red-300 p-3 rounded-lg">{error}</div>}

            <div className="bg-slate-800/50 rounded-lg p-6 border border-slate-700">
                <div className="flex justify-between items-start mb-4">
                    <div>
                        {/* Exibe nome da empresa e ticker do overviewData */}
                        <h3 className="text-2xl font-bold text-white">{overviewData?.company?.name || ticker || 'N/A'} ({overviewData?.quote?.ticker || ticker || 'N/A'})</h3>
                        <p className="text-slate-400">{overviewData?.company ? `${overviewData.company.cnpj}` : 'N/A'}</p>
                    </div>
                    {/* Exibe cotação e variação do overviewData */}
                    <div className="text-right">
                         <p className="text-3xl font-bold text-white">R$ {overviewData?.quote?.last_price.toFixed(2) || '--.--'}</p>
                         {overviewData?.quote && overviewData.quote.previous_close > 0 && (
                             <p className={`text-md font-semibold ${overviewData.quote.last_price >= overviewData.quote.previous_close ? 'text-green-400' : 'text-red-400'}`}>
                                 {overviewData.quote.last_price >= overviewData.quote.previous_close ? '▲' : '▼'}
                                 {((overviewData.quote.last_price / overviewData.quote.previous_close - 1) * 100).toFixed(2)}%
                            </p>
                         )}
                    </div>
                </div>
                 {/* Indicadores Fundamentalistas (ainda mockados) */}
                <IndicatorGrid indicators={mockIndicators} />
            </div>

            <div className="grid grid-cols-1 lg:grid-cols-2 gap-6">
                 {/* Tabelas DRE e Balanço exibindo dados da API */}
                <StatementTable title="DRE Consolidado (Último Período)" data={dreData} isLoading={loading} />
                <StatementTable title="Balanço Patrimonial (Consolidado)" data={balanceSheetData} isLoading={loading} />
            </div>
            
            {/* Seção para Fatos Relevantes, se houver dados */}
            {overviewData?.relevant_facts && overviewData.relevant_facts.length > 0 && (
                <div className="bg-slate-800/50 rounded-lg p-6 border border-slate-700">
                    <h3 className="text-lg font-semibold text-white mb-4">Últimos Fatos Relevantes</h3>
                    <ul className="space-y-3 text-sm text-slate-300">
                        {overviewData.relevant_facts.map(fact => (
                            <li key={fact.id} className="border-b border-slate-700 pb-2 last:border-b-0 last:pb-0">
                                <a href={fact.download_link} target="_blank" rel="noopener noreferrer" className="text-sky-400 hover:underline">
                                    <span className="font-medium text-white">[{formatDate(fact.reference_date)}]</span> {fact.subject}
                                </a>
                            </li>
                        ))}
                    </ul>
                </div>
            )}

        </div>
    );
};

export default Fundamentalist;
