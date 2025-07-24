
import React, { useState, useEffect } from 'react';
import { LineChart, Line, BarChart, Bar, XAxis, YAxis, Tooltip, Legend, ResponsiveContainer, Cell } from 'recharts';
import { Asset, PortfolioSummary, EditableAsset, DailyMetric } from '../types';
import PortfolioManager from './PortfolioManager';

// Tipos para os dados da API
interface PortfolioConfigData {
    id: number;
    ticker: string;
    quantity: number;
    target_weight: number;
}

interface PortfolioHistoryData {
    id: number;
    date: string;
    net_liquidity: number;
    quote_value: number;
    daily_change: number;
    buy_position: number;
    sell_position: number;
    net_long: number;
    exposure: number;
}

interface PortfolioMetricData {
    id: number;
    metric_name: string;
    metric_value: number;
}


const PortfolioDashboard: React.FC = () => {
    // Estados para os dados da API
    const [assets, setAssets] = useState<Asset[]>([]);
    const [summary, setSummary] = useState<PortfolioSummary | null>(null);
    const [history, setHistory] = useState<PortfolioHistoryData[]>([]);
    const [metrics, setMetrics] = useState<DailyMetric[]>([]);
    const [loading, setLoading] = useState(true);
    const [error, setError] = useState<string | null>(null);

    useEffect(() => {
        const fetchData = async () => {
            try {
                setLoading(true);
                
                // Busca os dados em paralelo
                const [configRes, historyRes, metricsRes] = await Promise.all([
                    fetch('/api/portfolio/config'),
                    fetch('/api/portfolio/history'),
                    fetch('/api/portfolio/metrics')
                ]);

                if (!configRes.ok || !historyRes.ok || !metricsRes.ok) {
                    throw new Error('Falha ao buscar dados do portfólio');
                }

                const configData: PortfolioConfigData[] = await configRes.json();
                const historyData: PortfolioHistoryData[] = await historyRes.json();
                const metricsData: PortfolioMetricData[] = await metricsRes.json();

                // Processa e atualiza os estados
                // NOTA: A lógica para 'price', 'dailyChange', 'contribution', etc. precisará
                // de uma fonte de dados de mercado em tempo real, que não temos ainda.
                // Por enquanto, usaremos valores mockados para esses campos.
                const processedAssets: Asset[] = configData.map(item => ({
                    ticker: item.ticker,
                    quantity: item.quantity,
                    targetPercent: item.target_weight,
                    // Mocked data for now:
                    price: Math.random() * 100,
                    dailyChange: (Math.random() - 0.5) * 5,
                    contribution: (Math.random() - 0.5) * 0.5,
                    positionValue: item.quantity * (Math.random() * 100),
                    positionPercent: Math.random() * 10,
                    difference: Math.random() * 2,
                    adjustment: Math.floor(Math.random() * 1000)
                }));
                setAssets(processedAssets);
                
                // Pega o último registro do histórico para o resumo
                if (historyData.length > 0) {
                    const latestHistory = historyData[historyData.length - 1];
                    setSummary({
                        netLiquidity: latestHistory.net_liquidity,
                        quoteValue: latestHistory.quote_value,
                        dailyChange: latestHistory.daily_change,
                        buyPosition: latestHistory.buy_position,
                        sellPosition: latestHistory.sell_position,
                        netLong: latestHistory.net_long,
                        exposure: latestHistory.exposure,
                    });
                }
                setHistory(historyData);
                
                const processedMetrics: DailyMetric[] = metricsData.map(item => ({
                    id: item.id.toString(),
                    label: item.metric_name,
                    value: item.metric_value
                }));
                setMetrics(processedMetrics);

            } catch (err) {
                setError(err instanceof Error ? err.message : 'Ocorreu um erro desconhecido');
            } finally {
                setLoading(false);
            }
        };

        fetchData();
    }, []);

    // Dados para os gráficos (derivados dos estados)
    const contributionData = assets.map(a => ({ name: a.ticker, value: a.adjustment })).sort((a,b) => b.value - a.value);
    const returnData = history.map(h => ({
        name: new Date(h.date).toLocaleDateString('pt-BR', { month: 'short', year: '2-digit'}),
        'Retorno da Cota': h.quote_value,
        // Mocked Ibovespa return for now
        'Retorno do Ibovespa': (h.quote_value * (1 + (Math.random() - 0.5) * 0.1)), 
    }));
    
    // Transforma a config para o formato que o PortfolioManager espera
    const editableAssets: EditableAsset[] = assets.map((a, i) => ({
        id: i, // Usando index como ID temporário
        ticker: a.ticker,
        quantity: a.quantity,
        targetWeight: a.targetPercent
    }));

    if (loading) {
        return <div className="text-center text-slate-400 p-8">Carregando dados do portfólio...</div>;
    }

    if (error) {
        return <div className="bg-red-900/50 border border-red-700 text-red-300 p-4 rounded-lg text-center">Erro: {error}</div>;
    }

    return (
        <div className="space-y-6">
            <PortfolioManager initialAssets={editableAssets} />
            
            <div className="grid grid-cols-1 lg:grid-cols-3 gap-6">
                <div className="lg:col-span-2 bg-slate-800/50 rounded-lg p-6 border border-slate-700">
                    <h2 className="text-xl font-semibold text-white mb-4">Composição da Carteira</h2>
                    <div className="overflow-x-auto">
                        <table className="w-full text-sm text-left text-slate-300">
                             <thead className="text-xs text-slate-400 uppercase bg-slate-700/50">
                                <tr>
                                    {['Ativo', 'Cotação', 'Var. Dia (%)', 'Contrib. (%)', 'Quantidade', 'Posição (R$)', 'Posição (%)', 'Posição %-Alvo', 'Diferença', 'Ajuste (Qtd.)'].map(h => 
                                        <th key={h} scope="col" className="px-4 py-3 whitespace-nowrap">{h}</th>
                                    )}
                                </tr>
                            </thead>
                            <tbody>
                                {assets.map((asset) => (
                                    <tr key={asset.ticker} className="border-b border-slate-700 hover:bg-slate-700/30">
                                        <td className="px-4 py-3 font-medium text-white whitespace-nowrap">{asset.ticker}</td>
                                        <td className="px-4 py-3">R$ {asset.price.toFixed(2)}</td>
                                        <td className={`px-4 py-3 ${asset.dailyChange > 0 ? 'text-green-400' : 'text-red-400'}`}>{asset.dailyChange.toFixed(2)}%</td>
                                        <td className={`px-4 py-3 ${asset.contribution > 0 ? 'text-green-400' : 'text-red-400'}`}>{asset.contribution.toFixed(2)}%</td>
                                        <td className="px-4 py-3">{asset.quantity.toLocaleString('pt-BR')}</td>
                                        <td className="px-4 py-3">R$ {asset.positionValue.toLocaleString('pt-BR', { minimumFractionDigits: 2 })}</td>
                                        <td className="px-4 py-3">{asset.positionPercent.toFixed(2)}%</td>
                                        <td className="px-4 py-3">{asset.targetPercent.toFixed(2)}%</td>
                                        <td className={`px-4 py-3 ${asset.difference > 0 ? 'text-green-400' : 'text-red-400'}`}>{asset.difference.toFixed(2)}%</td>
                                        <td className={`px-4 py-3 ${asset.adjustment > 0 ? 'text-green-400' : 'text-red-400'}`}>{asset.adjustment.toLocaleString('pt-BR')}</td>
                                    </tr>
                                ))}
                            </tbody>
                        </table>
                    </div>
                </div>

                <div className="bg-slate-800/50 rounded-lg p-6 border border-slate-700 h-fit">
                    <h2 className="text-xl font-semibold text-white mb-4">Resumo do Portfólio</h2>
                    {summary && (
                        <div className="space-y-4">
                            <div>
                                <p className="text-sm text-slate-400">Patrimônio Líquido</p>
                                <p className="text-3xl font-bold text-white">R$ {summary.netLiquidity.toLocaleString('pt-BR', { minimumFractionDigits: 2 })}</p>
                            </div>
                            <div>
                                <p className="text-sm text-slate-400">Valor da Cota</p>
                                <div className="flex items-baseline space-x-2">
                                    <p className="text-2xl font-bold text-white">R$ {summary.quoteValue.toFixed(4)}</p>
                                    <p className={`text-sm font-semibold ${summary.dailyChange > 0 ? 'text-green-400' : 'text-red-400'}`}>
                                        {summary.dailyChange > 0 ? '▲' : '▼'} {Math.abs(summary.dailyChange)}%
                                    </p>
                                </div>
                            </div>
                            <div className="border-t border-slate-700 pt-4 space-y-2 text-sm">
                                <div className="flex justify-between"><span className="text-slate-400">Posição Comprada:</span> <span className="font-medium text-white">{summary.buyPosition.toFixed(2)}%</span></div>
                                <div className="flex justify-between"><span className="text-slate-400">Posição Vendida:</span> <span className="font-medium text-white">{summary.sellPosition.toFixed(2)}%</span></div>
                                <div className="flex justify-between"><span className="text-slate-400">Net Long:</span> <span className="font-medium text-white">{summary.netLong.toFixed(2)}%</span></div>
                                <div className="flex justify-between"><span className="text-slate-400">Exposição Total:</span> <span className="font-medium text-white">{summary.exposure.toFixed(2)}%</span></div>
                            </div>
                        </div>
                    )}
                </div>
            </div>

            <div className="grid grid-cols-1 lg:grid-cols-2 gap-6">
                <div className="bg-slate-800/50 rounded-lg p-6 border border-slate-700">
                    <h3 className="text-lg font-semibold text-white mb-4">Contribuição para Variação Diária</h3>
                    <ResponsiveContainer width="100%" height={300}>
                        <BarChart data={contributionData} margin={{ top: 5, right: 20, left: -10, bottom: 5 }}>
                            <XAxis dataKey="name" stroke="#94a3b8" fontSize={12} tickLine={false} axisLine={false} />
                            <YAxis stroke="#94a3b8" fontSize={12} tickLine={false} axisLine={false} tickFormatter={(value) => `${(Number(value)/1000)}k`} />
                            <Tooltip
                                contentStyle={{ backgroundColor: '#1e293b', border: '1px solid #334155', color: '#cbd5e1' }}
                                cursor={{ fill: 'rgba(148, 163, 184, 0.1)' }}
                            />
                            <Bar dataKey="value">
                                {contributionData.map((entry, index) => (
                                    <Cell key={`cell-${index}`} fill={entry.value > 0 ? '#4ade80' : '#f87171'} />
                                ))}
                            </Bar>
                        </BarChart>
                    </ResponsiveContainer>
                </div>
                <div className="bg-slate-800/50 rounded-lg p-6 border border-slate-700">
                    <h3 className="text-lg font-semibold text-white mb-4">Retorno Acumulado: Cota vs. Ibovespa</h3>
                    <ResponsiveContainer width="100%" height={300}>
                        <LineChart data={returnData} margin={{ top: 5, right: 20, left: -10, bottom: 5 }}>
                            <XAxis dataKey="name" stroke="#94a3b8" fontSize={12} tickLine={false} axisLine={false} />
                            <YAxis stroke="#94a3b8" fontSize={12} tickLine={false} axisLine={false} />
                            <Tooltip
                                contentStyle={{ backgroundColor: '#1e293b', border: '1px solid #334155', color: '#cbd5e1' }}
                            />
                            <Legend wrapperStyle={{fontSize: "14px"}}/>
                            <Line type="monotone" dataKey="Retorno da Cota" stroke="#38bdf8" strokeWidth={2} dot={false} />
                            <Line type="monotone" dataKey="Retorno do Ibovespa" stroke="#a78bfa" strokeWidth={2} dot={false} />
                        </LineChart>
                    </ResponsiveContainer>
                </div>
            </div>
        </div>
    );
};

export default PortfolioDashboard;
