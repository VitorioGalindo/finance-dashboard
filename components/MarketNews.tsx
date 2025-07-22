
import React, { useState } from 'react';
import { MarketNewsArticle, AiAnalysis } from '../types';
import { StarIcon, CurrencyDollarIcon, XMarkIcon, ArrowRightIcon } from '../constants';

const mockAiAnalysis: AiAnalysis = {
    summary: 'O Brasil precisa adotar uma posição estratégica em relação à produção nacional de fertilizantes, para que o país fique menos dependente das importações de insumos para a produção agrícola. A avaliação foi feita por Guilherme Bastos, ex-secretário de Política Agrícola do Ministério da Agricultura, durante o X Congresso Brasileiro da Soja, em Campinas (SP).',
    sentiment: 'Neutro',
    mentionedCompanies: [
        { ticker: 'VALE3', name: 'Vale S.A.', relevance: 0.85 },
        { ticker: 'PETR4', name: 'Petrobras', relevance: 0.60 },
        { ticker: 'AGRO3', name: 'BrasilAgro', relevance: 0.90 },
    ],
    relatedNews: [
        { id: 'rn1', headline: 'IBOVESPA REVERTE TRAJETÓRIA DE ALTA; REQUA 0,01%, AOS 134.157 PTS' },
        { id: 'rn2', headline: 'ÍNDICE DÓLAR DXY OPERA EM QUEDA DE 0,45%, COTADO A 97,4 PTS' },
    ],
    relatedEvents: [
        { id: 're1', title: 'Congresso Brasileiro da Soja' },
    ]
};


const mockNewsData: MarketNewsArticle[] = [
  {
    id: '1',
    headline: 'Brasil precisa adotar posição estratégica no setor de fertilizantes, diz FGV Agro',
    source: 'Globo Rural',
    timestamp: '22/07 às 15:22:00',
    imageUrl: 'https://s2-g1.glbimg.com/co_Q3qfQf23aX_8c-3_D-2g3aB8=/0x0:1920x1080/984x0/smart/filters:strip_icc()/i.s3.glbimg.com/v1/AUTH_59edd422c0c84a879bd37670ae4f538a/internal_photos/bs/2022/U/q/fMylA9T26u2xtANd3lAQ/agro-2.jpg',
    content: `O Brasil precisa adotar uma posição estratégica em relação à produção nacional de fertilizantes, para que o país fique menos dependente das importações de insumos para a produção agrícola. A avaliação foi feita por Guilherme Bastos, ex-secretário de Política Agrícola do Ministério da Agricultura e coordenador do Centro de Estudos em Agronegócio da Fundação Getulio Vargas (FGV Agro), durante o X Congresso Brasileiro da Soja, em Campinas (SP).

Bastos, que hoje é diretor de Relações Institucionais da Associação Brasileira dos Produtores de Soja (Aprosoja Brasil), afirmou que o Brasil tem grande potencial para aumentar a produção de fertilizantes e reduzir a dependência externa. "Temos as matérias-primas, temos o conhecimento técnico, mas precisamos de um ambiente de negócios mais favorável e de políticas públicas que incentivem o investimento no setor", disse.

Ele destacou que a volatilidade dos preços internacionais dos fertilizantes, agravada por conflitos geopolíticos, representa um risco para a segurança alimentar e para a competitividade do agronegócio brasileiro. "Não podemos ficar à mercê das flutuações do mercado global. Aumentar a produção interna é uma questão de soberania nacional", concluiu.`,
    tags: ['COMMODITIES', 'MERCADOS', 'EMPRESAS'],
    aiAnalysis: mockAiAnalysis,
  },
   {
    id: '2',
    headline: 'IBOVESPA REVERTE TRAJETÓRIA DE ALTA; REQUA 0,01%, AOS 134.157 PTS',
    source: 'MOVER',
    timestamp: '22/07 às 15:18:27',
    imageUrl: 'https://s2.glbimg.com/xPOAFkM3sA3a3zXG4X2QzXJ4Jz8=/0x0:1280x853/984x0/smart/filters:strip_icc()/i.s3.glbimg.com/v1/AUTH_59edd422c0c84a879bd37670ae4f538a/internal_photos/bs/2023/q/m/Qe7B5gT8q3Y3X2QzXJ/b3.jpg',
    content: 'O Ibovespa, principal índice da bolsa de valores brasileira, reverteu a tendência de alta da manhã e opera com leve queda de 0,01%, aos 134.157 pontos, nesta tarde de segunda-feira (22). A mudança de rumo é influenciada pela cautela dos investidores antes da decisão sobre a taxa de juros nos Estados Unidos, que será anunciada pelo Federal Reserve (Fed) na quarta-feira (24).',
    tags: ['MERCADO DE CAPITAIS', 'IBOVESPA'],
    aiAnalysis: { ...mockAiAnalysis, sentiment: 'Negativo' },
  },
  {
    id: '3',
    headline: 'MORE OZZY OSBOURNE, ASTRO DO HEAVY METAL E LÍDER DO BLACK SABBATH',
    source: 'THE SUN',
    timestamp: '22/07 às 15:12:00',
    imageUrl: 'https://www.google.com/images/branding/googlelogo/1x/googlelogo_color_272x92dp.png',
    content: 'Esta é uma notícia não relacionada a finanças para demonstrar a filtragem.',
    tags: ['MÚSICA', 'CELEBRIDADES'],
    aiAnalysis: { ...mockAiAnalysis, sentiment: 'Neutro' },
  },
];

const MarketNews: React.FC = () => {
    const [activeTab, setActiveTab] = useState('Últimas');
    const [selectedArticle, setSelectedArticle] = useState<MarketNewsArticle>(mockNewsData[0]);

    return (
        <div className="flex h-full gap-4 text-slate-300">
            {/* Coluna Esquerda: Feed de Notícias */}
            <div className="w-1/3 max-w-sm flex flex-col bg-slate-800/50 p-3 rounded-lg border border-slate-700">
                <div className="flex items-center justify-between mb-3 border-b border-slate-700 pb-3">
                    <div className="flex items-center space-x-1">
                        <button onClick={() => setActiveTab('Últimas')} className={`px-3 py-1 text-sm font-semibold rounded-md ${activeTab === 'Últimas' ? 'bg-slate-700 text-white' : 'hover:bg-slate-700/50'}`}>Últimas</button>
                        <button onClick={() => setActiveTab('Populares')} className="flex items-center gap-1 px-3 py-1 text-sm font-semibold rounded-md hover:bg-slate-700/50">
                            <StarIcon /> Populares
                        </button>
                        <button onClick={() => setActiveTab('Cripto')} className="flex items-center gap-1 px-3 py-1 text-sm font-semibold rounded-md hover:bg-slate-700/50">
                            <CurrencyDollarIcon /> Cripto
                        </button>
                    </div>
                </div>
                <div className="flex-grow overflow-y-auto pr-1">
                    {mockNewsData.map(news => (
                        <div key={news.id} onClick={() => setSelectedArticle(news)} className={`p-2.5 rounded-md cursor-pointer mb-1 ${selectedArticle?.id === news.id ? 'bg-slate-700' : 'hover:bg-slate-700/50'}`}>
                            <p className="text-sm font-semibold text-white leading-tight">{news.headline}</p>
                            <div className="flex items-center justify-between mt-1.5">
                                <span className="text-xs text-slate-400">{news.source.toUpperCase()}</span>
                                <span className="text-xs text-slate-500">{news.timestamp}</span>
                            </div>
                        </div>
                    ))}
                </div>
                 <div className="border-t border-slate-700 mt-2 pt-2 text-center text-xs text-slate-500">
                    Finalize seu cadastro para desbloquear notícias exclusivas.
                </div>
            </div>

            {/* Coluna Central: Artigo */}
            <div className="flex-1 flex flex-col bg-slate-800/50 p-4 rounded-lg border border-slate-700 overflow-y-auto">
                 {selectedArticle ? (
                    <>
                        <div className="flex justify-between items-start mb-4">
                             <div>
                                <h1 className="text-2xl font-bold text-white">{selectedArticle.headline}</h1>
                                <p className="text-sm text-slate-400 mt-1">{selectedArticle.timestamp} • {selectedArticle.source}</p>
                            </div>
                            <button onClick={() => setSelectedArticle(mockNewsData[0])} className="p-1 text-slate-400 hover:text-white rounded-full hover:bg-slate-700">
                                <XMarkIcon className="w-5 h-5"/>
                            </button>
                        </div>
                        <img src={selectedArticle.imageUrl} alt={selectedArticle.headline} className="w-full h-64 object-cover rounded-lg mb-4" />
                        <div className="prose prose-invert prose-sm text-slate-300 max-w-none whitespace-pre-line">
                            {selectedArticle.content}
                        </div>
                        <div className="mt-4 flex gap-2">
                           {selectedArticle.tags.map(tag => (
                               <span key={tag} className="bg-slate-700 text-xs font-semibold px-2 py-1 rounded">{tag}</span>
                           ))}
                        </div>
                    </>
                ) : <div className="flex items-center justify-center h-full text-slate-500">Selecione uma notícia para ler</div>}
            </div>

            {/* Coluna Direita: Análise */}
            <div className="w-1/3 max-w-sm flex flex-col gap-4">
                 {selectedArticle && (
                    <>
                    <div className="bg-slate-800/50 p-4 rounded-lg border border-slate-700">
                        <h3 className="text-base font-semibold text-white mb-2">Análise por IA</h3>
                        <p className="text-sm text-slate-400 mb-1">Sentimento: <span className={`font-semibold ${
                            selectedArticle.aiAnalysis.sentiment === 'Positivo' ? 'text-green-400' : 
                            selectedArticle.aiAnalysis.sentiment === 'Negativo' ? 'text-red-400' : 'text-amber-400'
                        }`}>{selectedArticle.aiAnalysis.sentiment}</span></p>
                        <p className="text-sm text-slate-300">{selectedArticle.aiAnalysis.summary}</p>
                    </div>

                    <div className="flex-grow bg-slate-800/50 p-4 rounded-lg border border-slate-700 flex flex-col">
                        <h3 className="text-base font-semibold text-white mb-3">Ativos Mencionados</h3>
                        <div className="space-y-3 flex-grow overflow-y-auto">
                             {selectedArticle.aiAnalysis.mentionedCompanies.map(company => (
                                <div key={company.ticker}>
                                    <div className="flex justify-between items-center mb-1">
                                        <span className="text-sm font-semibold text-white">{company.name} ({company.ticker})</span>
                                        <span className="text-xs text-slate-400">{ (company.relevance * 100).toFixed(0) }%</span>
                                    </div>
                                    <div className="w-full bg-slate-700 rounded-full h-1.5">
                                        <div className="bg-sky-500 h-1.5 rounded-full" style={{ width: `${company.relevance * 100}%` }}></div>
                                    </div>
                                </div>
                             ))}
                        </div>
                         <div className="border-t border-slate-700 mt-3 pt-3">
                             <h3 className="text-base font-semibold text-white mb-2">Notícias Relacionadas</h3>
                             <div className="space-y-2 text-sm">
                                {selectedArticle.aiAnalysis.relatedNews.map(item => (
                                     <a href="#" key={item.id} className="flex items-center justify-between text-slate-300 hover:text-sky-400 group">
                                         <span>{item.headline}</span>
                                         <ArrowRightIcon />
                                     </a>
                                ))}
                             </div>
                         </div>
                    </div>
                    </>
                 )}
            </div>
        </div>
    );
};

export default MarketNews;