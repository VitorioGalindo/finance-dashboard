import React, { useState, useEffect } from 'react';
import { ResearchNote } from '../types';
import { PlusIcon, MagnifyingGlassIcon, TrashIcon } from '../constants';

const mockNotes: ResearchNote[] = [
    {
        id: 'note-1',
        title: 'Tese de Investimento - PETR4',
        content: '## Análise da Petrobras (PETR4)\n\n### Pontos Positivos:\n- **Produção do Pré-Sal:** Custos de extração baixos e volumes crescentes.\n- **Política de Dividendos:** Histórico recente de pagamentos robustos aos acionistas.\n- **Redução da Dívida:** A empresa tem focado em desalavancagem, o que reduz o risco financeiro.\n\n### Riscos:\n- **Interferência Política:** Mudanças na diretoria ou na estratégia de preços por influência governamental.\n- **Volatilidade do Petróleo:** A receita é diretamente impactada pelas cotações do barril de petróleo no mercado internacional.\n- **Transição Energética:** A longo prazo, a demanda por combustíveis fósseis pode diminuir.',
        lastUpdated: '2025-07-28T10:30:00Z',
    },
    {
        id: 'note-2',
        title: 'Resultados 2T25 - VALE3',
        content: '## Análise dos Resultados do 2º Trimestre de 2025 da Vale (VALE3)\n\nO resultado veio em linha com as expectativas do mercado. Destaque para o aumento no volume de vendas de minério de ferro, impulsionado pela demanda asiática. A margem EBITDA, no entanto, foi pressionada pelo aumento dos custos com frete marítimo.\n\n- **Receita Líquida:** R$ 50,2 bilhões (+5% vs 2T24)\n- **EBITDA Ajustado:** R$ 22,1 bilhões (-2% vs 2T24)\n- **Lucro Líquido:** R$ 15,8 bilhões (+10% vs 2T24)',
        lastUpdated: '2025-07-25T15:00:00Z',
    },
];

const Research: React.FC = () => {
    const [notes, setNotes] = useState<ResearchNote[]>(mockNotes);
    const [activeNoteId, setActiveNoteId] = useState<string | null>(mockNotes[0]?.id || null);
    const [searchTerm, setSearchTerm] = useState('');

    const activeNote = notes.find(note => note.id === activeNoteId);

    const handleNewNote = () => {
        const newNote: ResearchNote = {
            id: `note-${Date.now()}`,
            title: 'Nova Anotação',
            content: '',
            lastUpdated: new Date().toISOString(),
        };
        setNotes([newNote, ...notes]);
        setActiveNoteId(newNote.id);
    };

    const handleDeleteNote = (noteId: string) => {
        setNotes(notes.filter(note => note.id !== noteId));
        if (activeNoteId === noteId) {
            setActiveNoteId(notes.length > 1 ? notes.filter(n => n.id !== noteId)[0].id : null);
        }
    };
    
    const handleUpdateNote = (field: 'title' | 'content', value: string) => {
        if (!activeNoteId) return;
        setNotes(notes.map(note => 
            note.id === activeNoteId 
                ? { ...note, [field]: value, lastUpdated: new Date().toISOString() }
                : note
        ));
    };

    const filteredNotes = notes.filter(note => 
        note.title.toLowerCase().includes(searchTerm.toLowerCase()) || 
        note.content.toLowerCase().includes(searchTerm.toLowerCase())
    );

    const formatDate = (dateString: string) => {
        return new Date(dateString).toLocaleString('pt-BR', {
            day: '2-digit', month: 'short', year: 'numeric'
        });
    }

    return (
        <div className="flex h-full bg-slate-800/50 rounded-lg border border-slate-700 overflow-hidden">
            {/* Sidebar de Notas */}
            <div className="w-1/3 max-w-sm border-r border-slate-700 flex flex-col">
                <div className="p-4 border-b border-slate-700 flex items-center justify-between">
                    <h2 className="text-xl font-bold text-white">Pesquisa & Estudos</h2>
                </div>
                <div className="p-4 space-y-4">
                    <button onClick={handleNewNote} className="w-full bg-sky-600 text-white font-semibold py-2 rounded-md hover:bg-sky-500 transition-colors flex items-center justify-center gap-2">
                        <PlusIcon className="w-5 h-5" />
                        Nova Nota
                    </button>
                    <div className="relative">
                        <MagnifyingGlassIcon />
                        <input
                            type="text"
                            placeholder="Buscar notas..."
                            value={searchTerm}
                            onChange={(e) => setSearchTerm(e.target.value)}
                            className="w-full bg-slate-700 border border-slate-600 rounded-md py-2 pl-10 pr-4 text-white placeholder-slate-400 focus:outline-none focus:ring-2 focus:ring-sky-500"
                        />
                    </div>
                </div>
                <div className="flex-grow overflow-y-auto">
                    {filteredNotes.map(note => (
                        <div
                            key={note.id}
                            onClick={() => setActiveNoteId(note.id)}
                            className={`p-4 cursor-pointer border-l-4 ${activeNoteId === note.id ? 'bg-slate-700/50 border-sky-500' : 'border-transparent hover:bg-slate-700/30'}`}
                        >
                            <h3 className="font-semibold text-white truncate">{note.title}</h3>
                            <p className="text-sm text-slate-400 truncate mt-1">
                                {note.content.split('\n')[0] || 'Nenhum conteúdo adicional'}
                            </p>
                            <p className="text-xs text-slate-500 mt-2">{formatDate(note.lastUpdated)}</p>
                        </div>
                    ))}
                </div>
            </div>

            {/* Editor Principal */}
            <div className="flex-1 flex flex-col">
                {activeNote ? (
                    <>
                        <div className="p-4 border-b border-slate-700 flex justify-between items-center">
                            <p className="text-sm text-slate-400">Última atualização: {formatDate(activeNote.lastUpdated)}</p>
                            <button onClick={() => handleDeleteNote(activeNote.id)} className="p-2 text-slate-400 hover:text-red-400 hover:bg-slate-700 rounded-full">
                                <TrashIcon className="w-5 h-5" />
                            </button>
                        </div>
                        <div className="flex-grow flex flex-col overflow-y-auto">
                           <input 
                                type="text"
                                value={activeNote.title}
                                onChange={(e) => handleUpdateNote('title', e.target.value)}
                                className="w-full p-4 text-2xl font-bold bg-transparent text-white focus:outline-none placeholder-slate-500"
                                placeholder="Título da nota"
                           />
                           <textarea
                                value={activeNote.content}
                                onChange={(e) => handleUpdateNote('content', e.target.value)}
                                className="w-full h-full flex-grow p-4 bg-transparent text-slate-300 focus:outline-none resize-none placeholder-slate-500"
                                placeholder="Comece a escrever sua análise aqui..."
                           />
                        </div>
                    </>
                ) : (
                    <div className="flex items-center justify-center h-full text-center text-slate-500">
                        <div>
                            <h2 className="text-xl font-semibold">Nenhuma nota selecionada</h2>
                            <p>Selecione uma nota da lista ou crie uma nova para começar.</p>
                        </div>
                    </div>
                )}
            </div>
        </div>
    );
};

export default Research;
