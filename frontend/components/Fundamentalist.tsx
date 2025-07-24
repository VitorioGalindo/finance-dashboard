
import React, { useState, useEffect } from 'react';
import { FundamentalIndicator, FinancialStatementItem, RawFinancialStatement } from '../types';

// Mapeamento de códigos de conta para nomes amigáveis
const ACCOUNT_CODE_MAP: { [key: string]: string } = {
    '3.01': 'Receita Líquida',
    '3.11': 'Lucro Bruto',
    '3.99.01.01': 'Lucro Líquido Consolidado', // Exemplo, pode precisar de ajuste
    '3.99.01.02': 'Lucro Líquido Atribuído aos Controladores',
    '3.99': 'Resultado do Período',
    // Adicionar outros códigos importantes aqui
};


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

// Função para formatar números grandes em uma forma mais legível (ex: 1.23T, 45.6B, 789M)
const formatValue = (value: number): string => {
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
        ) : (
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
        )}
    </div>
);


const Fundamentalist: React.FC = () => {
    const [ticker, setTicker] = useState('B3SA3'); // Ticker padrão
    const [cnpj, setCnpj] = useState('09346601000125'); // CNPJ correspondente ao ticker padrão
    const [statements, setStatements] = useState<RawFinancialStatement[]>([]);
    const [dreData, setDreData] = useState<FinancialStatementItem[]>([]);
    const [balanceSheetData, setBalanceSheetData] = useState<FinancialStatementItem[]>([]);
    const [loading, setLoading] = useState(false);
    const [error, setError] = useState<string | null>(null);
    const [companyName, setCompanyName] = useState('B3 S.A. - Brasil, Bolsa, Balcão');

    const handleAnalyse = async () => {
        if (!cnpj) {
            setError('CNPJ é necessário para a busca.');
            return;
        }
        setLoading(true);
        setError(null);
        try {
            const response = await fetch(`/api/companies/${cnpj}/financials`);
            if (!response.ok) {
                const errorData = await response.json();
                throw new Error(errorData.error || `Erro na API: ${response.statusText}`);
            }
            const data: RawFinancialStatement[] = await response.json();
            setStatements(data);
            if(data.length > 0) {
              setCompanyName(data[0].company_name);
            }
        } catch (err) {
            setError(err instanceof Error ? err.message : 'Ocorreu um erro desconhecido');
            setStatements([]);
        } finally {
            setLoading(false);
        }
    };

    useEffect(() => {
        // Processar os dados brutos sempre que eles mudarem
        const processStatements = () => {
            const latestStatements = statements
                .filter(s => s.fiscal_year_order === 'ÚLTIMO')
                .sort((a, b) => new Date(b.reference_date).getTime() - new Date(a.reference_date).getTime());

            const dreItems: FinancialStatementItem[] = [];
            const balanceItems: FinancialStatementItem[] = [];
            
            const addedDRECodes = new Set<string>();
            const addedBalanceCodes = new Set<string>();

            for (const s of latestStatements) {
                const accountCode = s.account_code;
                
                // Mapeamento para DRE (códigos que começam com '3')
                if (accountCode.startsWith('3') && ACCOUNT_CODE_MAP[accountCode] && !addedDRECodes.has(accountCode)) {
                    dreItems.push({
                        item: ACCOUNT_CODE_MAP[accountCode],
                        value: formatValue(s.account_value),
                    });
                    addedDRECodes.add(accountCode);
                }

                // Mapeamento para Balanço Patrimonial (códigos que começam com '1' ou '2')
                if ((accountCode.startsWith('1') || accountCode.startsWith('2')) && ACCOUNT_CODE_MAP[accountCode] && !addedBalanceCodes.has(accountCode)) {
                    balanceItems.push({
                        item: ACCOUNT_CODE_MAP[accountCode],
                        value: formatValue(s.account_value),
                    });
                    addedBalanceCodes.add(accountCode);
                }
            }

            setDreData(dreItems);
            setBalanceSheetData(balanceItems);
        };

        if (statements.length > 0) {
            processStatements();
        } else {
            setDreData([]);
            setBalanceSheetData([]);
        }
    }, [statements]);
    
    // Busca inicial ao carregar o componente
    useEffect(() => {
      handleAnalyse();
    }, []);

    const handleTickerChange = (e: React.ChangeEvent<HTMLInputElement>) => {
        const newTicker = e.target.value.toUpperCase();
        setTicker(newTicker);
        // Lógica simples para mapear ticker para CNPJ (idealmente viria de uma API)
        if (newTicker === 'PETR4') {
            setCnpj('33000167000101');
        } else if (newTicker === 'VALE3') {
            setCnpj('33592510000154');
        } else if (newTicker === 'ITUB4') {
            setCnpj('60701190000104');
        } else if (newTicker === 'B3SA3') {
            setCnpj('09346601000125');
        } else {
            setCnpj(''); // Limpa se não for um ticker conhecido
        }
    };


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
                      disabled={loading || !cnpj}
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
                        <h3 className="text-2xl font-bold text-white">{ticker || 'N/A'}</h3>
                        <p className="text-slate-400">{companyName}</p>
                    </div>
                    <div className="text-right">
                         <p className="text-3xl font-bold text-white">R$ --.--</p>
                         <p className="text-md font-semibold text-slate-400">--.-- (--.--)%</p>
                    </div>
                </div>
                <IndicatorGrid indicators={mockIndicators} />
            </div>

            <div className="grid grid-cols-1 lg:grid-cols-2 gap-6">
                <StatementTable title="DRE Consolidado (Último Período)" data={dreData} isLoading={loading} />
                <StatementTable title="Balanço Patrimonial (Consolidado)" data={balanceSheetData} isLoading={loading} />
            </div>
        </div>
    );
};

export default Fundamentalist;
