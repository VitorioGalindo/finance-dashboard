import React from 'react';
import { LineChart, Line, BarChart, Bar, XAxis, YAxis, Tooltip, Legend, ResponsiveContainer, Cell } from 'recharts';
import { Asset, PortfolioSummary, SuggestedPortfolioAsset, SectorWeight } from '../types';
import PortfolioManager from './PortfolioManager';

const mockAssets: Asset[] = [
  { ticker: 'PROJ3', price: 42.88, dailyChange: 0.47, contribution: 0.02, quantity: 26000, positionValue: 1118310.40, positionPercent: 10.70, targetPercent: 15.00, difference: -4.30, adjustment: 20463 },
  { ticker: 'RAPT4', price: 7.46, dailyChange: 1.63, contribution: 0.12, quantity: 100000, positionValue: 746000.00, positionPercent: 7.14, targetPercent: 11.00, difference: -3.86, adjustment: 54123 },
  { ticker: 'MDNE3', price: 11.21, dailyChange: 3.06, contribution: 0.29, quantity: 47400, positionValue: 1855154.00, positionPercent: 9.62, targetPercent: 9.00, difference: 0.62, adjustment: -3046 },
  { ticker: 'ANIM3', price: 3.65, dailyChange: 2.24, contribution: 0.08, quantity: 110100, positionValue: 401865.00, positionPercent: 3.84, targetPercent: 7.00, difference: -3.16, adjustment: 90354 },
  { ticker: 'SINK3', price: 4.19, dailyChange: 1.45, contribution: 0.05, quantity: 85500, positionValue: 358245.00, positionPercent: 3.43, targetPercent: 7.00, difference: -3.57, adjustment: 89120 },
];

const mockSummary: PortfolioSummary = {
  netLiquidity: 10452249.17,
  quoteValue: 118.3171,
  dailyChange: -0.59,
  buyPosition: 87.16,
  sellPosition: 16.83,
  netLong: 56.36,
  exposure: 84.82,
};

const contributionData = mockAssets.map(a => ({ name: a.ticker, value: a.adjustment })).sort((a,b) => b.value - a.value);
const returnData = Array.from({ length: 12 }, (_, i) => ({
  name: `Jan 202${i < 10 ? '3' : '4'}`,
  'Retorno da Cota': 100 + Math.random() * 50 * Math.sin(i),
  'Retorno do Ibovespa': 100 + Math.random() * 40 * Math.sin(i * 0.8),
}));

const suggestedPortfolioData: SuggestedPortfolioAsset[] = [
    { ticker: 'BPAC11', company: 'BTG Pactual', currency: 'BRL', currentPrice: 40.8, targetPrice: 47.0, upsideDownside: 15, mktCap: 189469, pe26: 9.3, pe5yAvg: 11.5, deltaPe: -19, evEbitda26: 'NM', evEbitda5yAvg: 'NM', deltaEvEbitda: 'NM', epsGrowth26: 15, ibovWeight: 2.5, portfolioWeight: 8.0, owUw: 5.5 },
    { ticker: 'MOTV3', company: 'Motiva', currency: 'BRL', currentPrice: 13.2, targetPrice: 16.8, upsideDownside: 27, mktCap: 26664, pe26: 11.8, pe5yAvg: 16.0, deltaPe: -26, evEbitda26: 5.8, evEbitda5yAvg: 6.2, deltaEvEbitda: -6, epsGrowth26: 26, ibovWeight: 0.6, portfolioWeight: 6.0, owUw: 5.4 },
    { ticker: 'LREN3', company: 'Lojas Renner', currency: 'BRL', currentPrice: 19.2, targetPrice: 24.3, upsideDownside: 27, mktCap: 20301, pe26: 11.6, pe5yAvg: 16.1, deltaPe: -28, evEbitda26: 6.8, evEbitda5yAvg: 8.5, deltaEvEbitda: -20, epsGrowth26: 12, ibovWeight: 0.9, portfolioWeight: 6.0, owUw: 5.1 },
    { ticker: 'SMFT3', company: 'SmartFit', currency: 'BRL', currentPrice: 22.7, targetPrice: 30.0, upsideDownside: 32, mktCap: 13575, pe26: 15.2, pe5yAvg: 54.2, deltaPe: -72, evEbitda26: 8.7, evEbitda5yAvg: 'NM', deltaEvEbitda: 'NM', epsGrowth26: 'NM', ibovWeight: 1.5, portfolioWeight: 6.0, owUw: 4.5 },
    { ticker: 'INBR32', company: 'Inter', currency: 'BRL', currentPrice: 38.2, targetPrice: 52.0, upsideDownside: 36, mktCap: 16784, pe26: 'NM', pe5yAvg: 'NM', deltaPe: 'NM', evEbitda26: 'NM', evEbitda5yAvg: 'NM', deltaEvEbitda: 'NM', epsGrowth26: 'NM', ibovWeight: 1.5, portfolioWeight: 6.0, owUw: 4.5 },
    { ticker: 'RDOR3', company: 'Rede D\'Or', currency: 'BRL', currentPrice: 33.8, targetPrice: 34.5, upsideDownside: 2, mktCap: 77401, pe26: 13.8, pe5yAvg: 24.5, deltaPe: -44, evEbitda26: 7.4, evEbitda5yAvg: 12.1, deltaEvEbitda: -39, epsGrowth26: 24, ibovWeight: 1.9, portfolioWeight: 6.0, owUw: 4.1 },
    { ticker: 'ITSA4', company: 'Itausa', currency: 'BRL', currentPrice: 10.6, targetPrice: 12.0, upsideDownside: 14, mktCap: 116174, pe26: 6.2, pe5yAvg: 6.8, deltaPe: -10, evEbitda26: 'NM', evEbitda5yAvg: 'NM', deltaEvEbitda: 'NM', epsGrowth26: 11, ibovWeight: 11.3, portfolioWeight: 11.0, owUw: -0.3 },
    { ticker: 'VALE3', company: 'Vale', currency: 'BRL', currentPrice: 55.3, targetPrice: 75.0, upsideDownside: 36, mktCap: 250916, pe26: 5.5, pe5yAvg: 5.6, deltaPe: -2, evEbitda26: 3.9, evEbitda5yAvg: 3.6, deltaEvEbitda: 8, epsGrowth26: 3, ibovWeight: 11.2, portfolioWeight: 9.0, owUw: -2.2 },
];

const sectorWeightsData: SectorWeight[] = [
    { sector: 'Retail', ibovWeight: 3.9, portfolioWeight: 15.0, owUw: 11.1 },
    { sector: 'Real Estate', ibovWeight: 0.6, portfolioWeight: 8.0, owUw: 7.4 },
    { sector: 'Financials - Banks', ibovWeight: 21.6, portfolioWeight: 25.0, owUw: 3.4 },
    { sector: 'Healthcare', ibovWeight: 3.1, portfolioWeight: 6.0, owUw: 2.9 },
    { sector: 'Oil & Gas', ibovWeight: 15.8, portfolioWeight: 13.0, owUw: -2.8 },
    { sector: 'Utilities', ibovWeight: 15.2, portfolioWeight: 11.0, owUw: -4.2 },
    { sector: 'Metals & Mining', ibovWeight: 13.3, portfolioWeight: 9.0, owUw: -4.3 },
    { sector: 'Financials - Others', ibovWeight: 5.8, portfolioWeight: 0.0, owUw: -5.8 },
];


const OwUwBar: React.FC<{ value: number }> = ({ value }) => {
    const maxValue = Math.max(...sectorWeightsData.map(d => Math.abs(d.owUw)));
    const percentage = (Math.abs(value) / maxValue) * 50;
    const isOverweight = value > 0;

    return (
        <div className="w-full h-full relative bg-slate-700 rounded-sm">
            <div
                className={`absolute h-full ${isOverweight ? 'bg-sky-500' : 'bg-red-500'} rounded-sm`}
                style={{
                    width: `${percentage}%`,
                    left: isOverweight ? '50%' : `${50 - percentage}%`,
                }}
            ></div>
            <div className="absolute w-full h-full text-center text-xs font-semibold text-white z-10 flex items-center justify-center">
              {value.toFixed(1)}%
            </div>
        </div>
    );
};


const PortfolioDashboard: React.FC = () => {
    return (
        <div className="space-y-6">
            <PortfolioManager initialAssets={mockAssets.map((a,i) => ({id: i, ticker: a.ticker, quantity: a.quantity, targetWeight: a.targetPercent}))}/>
            
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
                                {mockAssets.map((asset) => (
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
                    <div className="space-y-4">
                        <div>
                            <p className="text-sm text-slate-400">Patrimônio Líquido</p>
                            <p className="text-3xl font-bold text-white">R$ {mockSummary.netLiquidity.toLocaleString('pt-BR', { minimumFractionDigits: 2 })}</p>
                        </div>
                        <div>
                            <p className="text-sm text-slate-400">Valor da Cota</p>
                            <div className="flex items-baseline space-x-2">
                                <p className="text-2xl font-bold text-white">R$ {mockSummary.quoteValue.toFixed(4)}</p>
                                <p className={`text-sm font-semibold ${mockSummary.dailyChange > 0 ? 'text-green-400' : 'text-red-400'}`}>
                                    {mockSummary.dailyChange > 0 ? '▲' : '▼'} {Math.abs(mockSummary.dailyChange)}%
                                </p>
                            </div>
                        </div>
                        <div className="border-t border-slate-700 pt-4 space-y-2 text-sm">
                            <div className="flex justify-between"><span className="text-slate-400">Posição Comprada:</span> <span className="font-medium text-white">{mockSummary.buyPosition.toFixed(2)}%</span></div>
                            <div className="flex justify-between"><span className="text-slate-400">Posição Vendida:</span> <span className="font-medium text-white">{mockSummary.sellPosition.toFixed(2)}%</span></div>
                            <div className="flex justify-between"><span className="text-slate-400">Net Long:</span> <span className="font-medium text-white">{mockSummary.netLong.toFixed(2)}%</span></div>
                            <div className="flex justify-between"><span className="text-slate-400">Exposição Total:</span> <span className="font-medium text-white">{mockSummary.exposure.toFixed(2)}%</span></div>
                        </div>
                    </div>
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

            <div className="space-y-6">
                <div className="bg-slate-800/50 rounded-lg p-6 border border-slate-700">
                    <h3 className="text-lg font-semibold text-white mb-2">Carteira Sugerida</h3>
                    <p className="text-xs text-slate-400 mb-4">Fonte: Santander Estimates, Bloomberg. Atualizado em 10 de julho de 2025.</p>
                     <div className="overflow-x-auto">
                        <table className="w-full text-sm text-left text-slate-300">
                            <thead className="text-xs text-slate-400 uppercase bg-slate-700/50">
                                <tr>
                                    {['Ticker', 'Company', 'Currency', 'Current Price', 'Target Price', 'Upside/Downside', 'Mkt Cap (Million)', 'P/E 26', 'P/E 5Y AVG', 'Delta P/E', 'EV/Ebitda 26', 'EV/Ebitda 5Y AVG', 'Delta EV/Ebitda', 'EPS growth 26', 'IBOV Weight', 'Portfolio weight', 'OW/UW'].map(h => 
                                        <th key={h} scope="col" className="px-3 py-3 font-medium whitespace-nowrap">{h}</th>
                                    )}
                                </tr>
                            </thead>
                            <tbody>
                                {suggestedPortfolioData.map((asset) => (
                                    <tr key={asset.ticker} className="border-b border-slate-700 hover:bg-slate-700/30">
                                        <td className="px-3 py-2 font-semibold text-white whitespace-nowrap">{asset.ticker}</td>
                                        <td className="px-3 py-2 whitespace-nowrap">{asset.company}</td>
                                        <td className="px-3 py-2">{asset.currency}</td>
                                        <td className="px-3 py-2">{asset.currentPrice.toFixed(1)}</td>
                                        <td className="px-3 py-2">{asset.targetPrice.toFixed(1)}</td>
                                        <td className={`px-3 py-2 ${asset.upsideDownside > 0 ? 'text-green-400' : 'text-red-400'}`}>{asset.upsideDownside}%</td>
                                        <td className="px-3 py-2">{asset.mktCap.toLocaleString('pt-BR')}</td>
                                        <td className="px-3 py-2">{asset.pe26}</td>
                                        <td className="px-3 py-2">{asset.pe5yAvg}</td>
                                        <td className={`px-3 py-2 ${typeof asset.deltaPe === 'number' && asset.deltaPe > 0 ? 'text-green-400' : 'text-red-400'}`}>{typeof asset.deltaPe === 'number' ? `${asset.deltaPe}%` : asset.deltaPe}</td>
                                        <td className="px-3 py-2">{asset.evEbitda26}</td>
                                        <td className="px-3 py-2">{asset.evEbitda5yAvg}</td>
                                        <td className={`px-3 py-2 ${typeof asset.deltaEvEbitda === 'number' && asset.deltaEvEbitda > 0 ? 'text-green-400' : 'text-red-400'}`}>{typeof asset.deltaEvEbitda === 'number' ? `${asset.deltaEvEbitda}%` : asset.deltaEvEbitda}</td>
                                        <td className={`px-3 py-2 ${typeof asset.epsGrowth26 === 'number' && asset.epsGrowth26 > 0 ? 'text-green-400' : 'text-red-400'}`}>{typeof asset.epsGrowth26 === 'number' ? `${asset.epsGrowth26}%` : asset.epsGrowth26}</td>
                                        <td className="px-3 py-2">{asset.ibovWeight.toFixed(1)}%</td>
                                        <td className="px-3 py-2">{asset.portfolioWeight.toFixed(1)}%</td>
                                        <td className={`px-3 py-2 font-bold ${asset.owUw > 0 ? 'text-sky-400' : 'text-orange-400'}`}>
                                            <div className={`p-1 rounded text-center ${asset.owUw > 0 ? 'bg-sky-500/20' : 'bg-orange-500/20'}`}>
                                                {asset.owUw.toFixed(1)}%
                                            </div>
                                        </td>
                                    </tr>
                                ))}
                            </tbody>
                        </table>
                    </div>
                </div>

                <div className="bg-slate-800/50 rounded-lg p-6 border border-slate-700">
                    <h3 className="text-lg font-semibold text-white mb-2">Pesos por Setor</h3>
                     <p className="text-xs text-slate-400 mb-4">Para mais detalhes, veja Equity Strategy Insights: Updating Brazil Recommended Portfolio, publicado em 29 de junho de 2025.</p>
                    <div className="overflow-x-auto">
                        <table className="w-full text-sm text-left text-slate-300">
                            <thead className="text-xs text-slate-400 uppercase bg-slate-700/50">
                                <tr>
                                    <th className="px-3 py-3 font-medium whitespace-nowrap">Sector</th>
                                    <th className="px-3 py-3 font-medium whitespace-nowrap">Ibov Weight</th>
                                    <th className="px-3 py-3 font-medium whitespace-nowrap">Portfolio Weight</th>
                                    <th className="px-3 py-3 font-medium whitespace-nowrap w-40">OW/UW</th>
                                </tr>
                            </thead>
                            <tbody>
                                {sectorWeightsData.map((item) => (
                                    <tr key={item.sector} className="border-b border-slate-700 hover:bg-slate-700/30">
                                        <td className="px-3 py-2.5 font-semibold text-white whitespace-nowrap">{item.sector}</td>
                                        <td className="px-3 py-2.5 whitespace-nowrap">{item.ibovWeight.toFixed(1)}%</td>
                                        <td className="px-3 py-2.5 whitespace-nowrap">{item.portfolioWeight.toFixed(1)}%</td>
                                        <td className="px-3 py-2.5">
                                            <OwUwBar value={item.owUw} />
                                        </td>
                                    </tr>
                                ))}
                            </tbody>
                        </table>
                    </div>
                </div>
            </div>

        </div>
    );
};

export default PortfolioDashboard;