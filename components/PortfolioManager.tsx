import React, { useState } from 'react';
import { EditableAsset, DailyMetric } from '../types';
import { ChevronUpIcon, PencilSquareIcon, TrashIcon, PlusIcon } from '../constants';

interface PortfolioManagerProps {
    initialAssets: EditableAsset[];
}

const initialMetrics: DailyMetric[] = [
    { id: 'cotaD1', label: 'Cota D-1', value: 118.9751 },
    { id: 'qtdCotas', label: 'Quantidade de Cotas', value: 88341 },
    { id: 'caixaBruto', label: 'Caixa Bruto', value: 5204127.00 },
    { id: 'outros', label: 'Outros', value: -15831.00 },
    { id: 'outrasDespesas', label: 'Outras Despesas', value: 0.00 },
];

const PortfolioManager: React.FC<PortfolioManagerProps> = ({ initialAssets }) => {
    const [isOpen, setIsOpen] = useState(false);
    const [assets, setAssets] = useState<EditableAsset[]>(initialAssets);
    const [metrics, setMetrics] = useState<DailyMetric[]>(initialMetrics);

    const handleAssetChange = (id: number, field: keyof EditableAsset, value: string | number) => {
        setAssets(assets.map(asset => asset.id === id ? { ...asset, [field]: value } : asset));
    };
    
    const handleAddAsset = () => {
        const newId = assets.length > 0 ? Math.max(...assets.map(a => a.id)) + 1 : 1;
        setAssets([...assets, { id: newId, ticker: '', quantity: 0, targetWeight: 0 }]);
    };

    const handleDeleteAsset = (id: number) => {
        setAssets(assets.filter(asset => asset.id !== id));
    };

    const handleMetricChange = (id: string, newValue: number) => {
        setMetrics(metrics.map(metric => metric.id === id ? { ...metric, value: newValue } : metric));
    };
    
    const adjustMetric = (id: string, amount: number) => {
        const metric = metrics.find(m => m.id === id);
        if (metric) {
            let precision = 0;
            // Handle precision for decimal values
            if (metric.label.includes('Cota')) {
                precision = 4;
            } else if (String(metric.value).includes('.')) {
                precision = 2;
            }
            const newValue = parseFloat((metric.value + amount).toFixed(precision));
            handleMetricChange(id, newValue);
        }
    };
    
    if (!isOpen) {
        return (
            <div className="bg-slate-800/50 rounded-lg p-2 border border-slate-700">
                <button onClick={() => setIsOpen(true)} className="w-full flex justify-between items-center px-4 py-2 text-white">
                    <div className="flex items-center gap-2">
                        <PencilSquareIcon />
                        <span className="font-semibold">Gerenciar Ativos e Métricas</span>
                    </div>
                    <ChevronUpIcon />
                </button>
            </div>
        )
    }

    return (
        <div className="bg-slate-800/50 rounded-lg p-4 border border-slate-700">
            <button onClick={() => setIsOpen(false)} className="w-full flex justify-between items-center mb-4 text-white">
                 <div className="flex items-center gap-2">
                    <PencilSquareIcon />
                    <span className="font-semibold">Gerenciar Ativos e Métrica</span>
                </div>
                <ChevronUpIcon className="w-5 h-5 transform rotate-180" />
            </button>
            
            <div className="grid grid-cols-1 lg:grid-cols-2 gap-6">
                {/* Gerenciar Ativos da Carteira */}
                <div>
                    <h3 className="text-lg font-semibold text-white mb-2">Gerenciar Ativos da Carteira</h3>
                    <div className="bg-sky-900/50 text-sky-200 text-sm p-3 rounded-md mb-4 border border-sky-800">
                        Adicione, edite ou remova linhas. Depois, clique em 'Salvar Carteira'.
                    </div>
                    <div className="max-h-96 overflow-y-auto pr-2">
                        <table className="w-full text-sm text-left text-slate-300">
                             <thead className="text-xs text-slate-400 uppercase bg-slate-700/50 sticky top-0">
                                <tr>
                                    <th className="px-3 py-2">Ticker</th>
                                    <th className="px-3 py-2">Quantidade</th>
                                    <th className="px-3 py-2">% Alvo</th>
                                    <th className="px-3 py-2"></th>
                                </tr>
                            </thead>
                            <tbody>
                                {assets.map(asset => (
                                    <tr key={asset.id} className="border-b border-slate-700">
                                        <td className="p-1">
                                            <input type="text" value={asset.ticker} onChange={e => handleAssetChange(asset.id, 'ticker', e.target.value.toUpperCase())} className="w-full bg-slate-600 rounded-md p-2 border border-slate-500 focus:ring-sky-500 focus:border-sky-500"/>
                                        </td>
                                        <td className="p-1">
                                            <input type="number" value={asset.quantity} onChange={e => handleAssetChange(asset.id, 'quantity', Number(e.target.value))} className="w-full bg-slate-600 rounded-md p-2 border border-slate-500 focus:ring-sky-500 focus:border-sky-500"/>
                                        </td>
                                        <td className="p-1">
                                            <input type="number" value={asset.targetWeight} onChange={e => handleAssetChange(asset.id, 'targetWeight', Number(e.target.value))} className="w-full bg-slate-600 rounded-md p-2 border border-slate-500 focus:ring-sky-500 focus:border-sky-500"/>
                                        </td>
                                        <td className="p-1 text-center">
                                            <button onClick={() => handleDeleteAsset(asset.id)} className="p-2 text-slate-400 hover:text-red-400"><TrashIcon /></button>
                                        </td>
                                    </tr>
                                ))}
                            </tbody>
                        </table>
                    </div>
                     <div className="flex justify-between items-center mt-4">
                        <button onClick={handleAddAsset} className="flex items-center gap-1 text-sm text-sky-400 hover:text-sky-300">
                           <PlusIcon className="w-4 h-4" /> Adicionar Ativo
                        </button>
                        <button onClick={() => console.log('Saving assets:', assets)} className="bg-sky-600 text-white px-4 py-2 rounded-md text-sm font-semibold hover:bg-sky-500">
                            Salvar Carteira
                        </button>
                    </div>
                </div>

                {/* Editar Métricas Diárias */}
                <div>
                     <h3 className="text-lg font-semibold text-white mb-2">Editar Métricas Diárias</h3>
                     <div className="bg-slate-700/50 p-4 rounded-lg space-y-3">
                        {metrics.map(metric => (
                             <div key={metric.id}>
                                <label className="text-sm text-slate-400">{metric.label}</label>
                                <div className="flex items-center gap-2 mt-1">
                                    <button onClick={() => adjustMetric(metric.id, -1)} className="px-2 py-1 bg-slate-600 rounded-md hover:bg-slate-500">-</button>
                                    <input 
                                      type="number"
                                      value={metric.value}
                                      onChange={e => handleMetricChange(metric.id, Number(e.target.value))}
                                      className="w-full text-center bg-slate-800 rounded-md p-2 border border-slate-600 focus:ring-sky-500 focus:border-sky-500"
                                    />
                                    <button onClick={() => adjustMetric(metric.id, 1)} className="px-2 py-1 bg-slate-600 rounded-md hover:bg-slate-500">+</button>
                                </div>
                             </div>
                        ))}
                         <button onClick={() => console.log('Updating metrics:', metrics)} className="w-full bg-slate-600 text-white mt-4 px-4 py-2 rounded-md text-sm font-semibold hover:bg-slate-500">
                            Atualizar Métricas
                        </button>
                     </div>
                </div>
            </div>
        </div>
    )
}

export default PortfolioManager;