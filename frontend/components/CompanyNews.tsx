import React, { useState } from 'react';
import { CompanyNewsBlock, CompanyNewsItem } from '../types';
import { geminiService } from '../services/geminiService';
import { PlusIcon, MagnifyingGlassIcon, TrashIcon, SparklesIcon } from '../constants';

const mockInitialBlocks: CompanyNewsBlock[] = [
    {
        ticker: 'MSFT',
        newsItems: [
            {
                id: 'news-1',
                url: 'https://www.example.com/msft-earnings',
                title: 'Microsoft Earnings: Good Quarter From Any Angle',
                summary: 'A Microsoft divulgou um trimestre sólido, superando as expectativas em todas as frentes. O crescimento da receita de nuvem (Azure) continua a ser o principal impulsionador...',
                source: 'Morningstar',
                publishedDate: '2025-04-30T00:00:00Z',
            }
        ]
    },
    {
        ticker: 'PETR4',
        newsItems: []
    }
];

const CompanyNews: React.FC = () => {
    const [blocks, setBlocks] = useState<CompanyNewsBlock[]>(mockInitialBlocks);
    const [activeBlockTicker, setActiveBlockTicker] = useState<string | null>(mockInitialBlocks[0]?.ticker || null);
    const [searchTerm, setSearchTerm] = useState('');
    const [newsUrl, setNewsUrl] = useState('');
    const [isLoading, setIsLoading] = useState(false);
    
    const activeBlock = blocks.find(b => b.ticker === activeBlockTicker);

    const handleAddBlock = () => {
        const ticker = prompt("Digite o ticker da nova empresa (ex: PETR4):");
        if (ticker && !blocks.find(b => b.ticker.toUpperCase() === ticker.toUpperCase())) {
            const newBlock: CompanyNewsBlock = { ticker: ticker.toUpperCase(), newsItems: [] };
            setBlocks([newBlock, ...blocks]);
            setActiveBlockTicker(newBlock.ticker);
        } else if (ticker) {
            alert("Este ticker já existe.");
        }
    };

    const handleAnalyzeAndAdd = async (e: React.FormEvent) => {
        e.preventDefault();
        if (!newsUrl.trim() || !activeBlockTicker) return;

        setIsLoading(true);
        try {
            const summaryData = await geminiService.summarizeNewsFromUrl(newsUrl);
            const newNewsItem: CompanyNewsItem = {
                id: `news-${Date.now()}`,
                url: newsUrl,
                ...summaryData
            };
            
            setBlocks(blocks.map(b => 
                b.ticker === activeBlockTicker 
                    ? { ...b, newsItems: [newNewsItem, ...b.newsItems] }
                    : b
            ));
            setNewsUrl('');

        } catch (error) {
            console.error("Failed to analyze news:", error);
            alert("Falha ao analisar a notícia. Por favor, tente novamente.");
        } finally {
            setIsLoading(false);
        }
    };
    
    const handleDeleteNewsItem = (itemId: string) => {
        if (!activeBlockTicker) return;
        setBlocks(blocks.map(b => 
            b.ticker === activeBlockTicker
                ? { ...b, newsItems: b.newsItems.filter(item => item.id !== itemId) }
                : b
        ));
    };

    const filteredBlocks = blocks.filter(b => b.ticker.toLowerCase().includes(searchTerm.toLowerCase()));

    const formatDate = (dateString: string) => {
        return new Date(dateString).toLocaleString('pt-BR', {
            day: '2-digit', month: 'long', year: 'numeric', hour: '2-digit', minute: '2-digit'
        });
    }

    return (
        <div className="flex h-full bg-slate-800/50 rounded-lg border border-slate-700 overflow-hidden">
            {/* Sidebar de Blocos */}
            <div className="w-1/3 max-w-xs border-r border-slate-700 flex flex-col">
                <div className="p-4 border-b border-slate-700">
                    <h2 className="text-xl font-bold text-white">Notícias da Empresa</h2>
                </div>
                <div className="p-4 space-y-4">
                    <button onClick={handleAddBlock} className="w-full bg-sky-600 text-white font-semibold py-2 rounded-md hover:bg-sky-500 transition-colors flex items-center justify-center gap-2">
                        <PlusIcon className="w-5 h-5" />
                        Novo Bloco
                    </button>
                    <div className="relative">
                         <div className="pointer-events-none absolute inset-y-0 left-0 flex items-center pl-3">
                            <MagnifyingGlassIcon />
                        </div>
                        <input
                            type="text"
                            placeholder="Buscar Ticker..."
                            value={searchTerm}
                            onChange={(e) => setSearchTerm(e.target.value)}
                            className="w-full bg-slate-700 border border-slate-600 rounded-md py-2 pl-10 pr-4 text-white placeholder-slate-400 focus:outline-none focus:ring-2 focus:ring-sky-500"
                        />
                    </div>
                </div>
                <div className="flex-grow overflow-y-auto">
                    {filteredBlocks.map(block => (
                        <div
                            key={block.ticker}
                            onClick={() => setActiveBlockTicker(block.ticker)}
                            className={`p-4 cursor-pointer border-l-4 ${activeBlockTicker === block.ticker ? 'bg-slate-700/50 border-sky-500' : 'border-transparent hover:bg-slate-700/30'}`}
                        >
                            <div className="flex justify-between items-center">
                                <h3 className="font-semibold text-white truncate">{block.ticker}</h3>
                                <span className="text-xs bg-slate-600 text-slate-300 rounded-full px-2 py-0.5">{block.newsItems.length}</span>
                            </div>
                        </div>
                    ))}
                </div>
            </div>

            {/* Area de Conteúdo */}
            <div className="flex-1 flex flex-col">
                {activeBlock ? (
                    <div className="flex flex-col h-full">
                        <div className="p-4 border-b border-slate-700">
                             <form onSubmit={handleAnalyzeAndAdd} className="space-y-2">
                                <label className="text-sm font-medium text-slate-300">Adicionar e Analisar Nova Notícia</label>
                                <div className="flex gap-2">
                                    <input 
                                        type="url"
                                        value={newsUrl}
                                        onChange={(e) => setNewsUrl(e.target.value)}
                                        placeholder="Cole a URL da notícia aqui..."
                                        className="w-full bg-slate-700 border border-slate-600 rounded-md py-2 px-3 text-white placeholder-slate-400 focus:outline-none focus:ring-2 focus:ring-sky-500"
                                        disabled={isLoading}
                                    />
                                    <button type="submit" disabled={isLoading || !newsUrl.trim()} className="bg-sky-600 text-white font-semibold px-4 py-2 rounded-md hover:bg-sky-500 disabled:bg-slate-600 disabled:cursor-not-allowed transition-colors flex items-center justify-center gap-2 shrink-0">
                                        {isLoading ? (
                                            <>
                                                <SparklesIcon className="w-5 h-5 animate-pulse" />
                                                <span>Analisando...</span>
                                            </>
                                        ) : (
                                            'Analisar e Adicionar'
                                        )}
                                    </button>
                                </div>
                             </form>
                        </div>
                        <div className="flex-grow overflow-y-auto p-4 space-y-4">
                            {activeBlock.newsItems.length === 0 && !isLoading && (
                                <div className="text-center text-slate-500 pt-16">
                                    <p>Nenhuma notícia adicionada para {activeBlock.ticker}.</p>
                                    <p>Cole uma URL acima para começar.</p>
                                </div>
                            )}
                            {activeBlock.newsItems.map(item => (
                                <div key={item.id} className="bg-slate-700/40 p-4 rounded-lg border border-slate-700">
                                    <div className="flex justify-between items-start">
                                        <div>
                                            <h3 className="text-lg font-bold text-white">{item.title}</h3>
                                            <p className="text-xs text-slate-400 mt-1">
                                                Por {item.source} • {formatDate(item.publishedDate)}
                                            </p>
                                        </div>
                                         <button onClick={() => handleDeleteNewsItem(item.id)} className="p-1 text-slate-500 hover:text-red-400"><TrashIcon className="w-4 h-4" /></button>
                                    </div>
                                    <p className="text-sm text-slate-300 mt-2">{item.summary}</p>
                                    <a href={item.url} target="_blank" rel="noopener noreferrer" className="inline-block mt-3 bg-slate-600 text-white text-sm font-semibold px-3 py-1 rounded-md hover:bg-slate-500 transition-colors">
                                        Ver Notícia
                                    </a>
                                </div>
                            ))}
                        </div>
                    </div>
                ) : (
                     <div className="flex items-center justify-center h-full text-center text-slate-500">
                        <div>
                            <h2 className="text-xl font-semibold">Nenhum bloco selecionado</h2>
                            <p>Selecione um bloco na lista ou crie um novo para começar.</p>
                        </div>
                    </div>
                )}
            </div>
        </div>
    );
};

export default CompanyNews;
