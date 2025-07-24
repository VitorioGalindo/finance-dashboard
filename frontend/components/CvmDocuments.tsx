
import React, { useState, useEffect } from 'react';
import { CvmDocumentData } from '../types';
import { Search, DownloadCloud, FileText } from 'lucide-react';

const formatDate = (dateString: string | null) => {
    if (!dateString) return 'N/A';
    const date = new Date(dateString);
    return new Intl.DateTimeFormat('pt-BR', {
        day: '2-digit',
        month: '2-digit',
        year: 'numeric',
    }).format(date);
};

const CvmDocuments: React.FC = () => {
    const [documents, setDocuments] = useState<CvmDocumentData[]>([]);
    const [loading, setLoading] = useState(false);
    const [error, setError] = useState<string | null>(null);
    const [cnpj, setCnpj] = useState('09346601000125'); // B3 CNPJ as default
    const [searchTerm, setSearchTerm] = useState('09346601000125');

    const fetchDocuments = async (currentCnpj: string) => {
        if (!currentCnpj) {
            setError('Por favor, insira um CNPJ válido.');
            setDocuments([]);
            return;
        }
        setLoading(true);
        setError(null);
        try {
            const response = await fetch(`/api/companies/${currentCnpj}/documents`);
            if (!response.ok) {
                const errorData = await response.json();
                throw new Error(errorData.error || `Erro ao buscar documentos: ${response.statusText}`);
            }
            const data: CvmDocumentData[] = await response.json();
            
            if (data.length === 0) {
                 setError('Nenhum documento encontrado. Verifique se a tabela "cvm_documents" foi criada e populada pelo ETL.');
            }
            setDocuments(data);

        } catch (err) {
            setError(err instanceof Error ? err.message : 'Ocorreu um erro desconhecido.');
            setDocuments([]);
        } finally {
            setLoading(false);
        }
    };

    useEffect(() => {
        if(cnpj) {
            fetchDocuments(cnpj);
        }
    }, []);

    const handleSearch = (e: React.FormEvent) => {
        e.preventDefault();
        const cleanCnpj = searchTerm.replace(/\D/g, '');
        setCnpj(cleanCnpj);
        fetchDocuments(cleanCnpj);
    };

    return (
        <div className="space-y-6">
            <div className="flex justify-between items-center">
                <h2 className="text-2xl font-semibold text-white">Documentos da CVM (IPE)</h2>
            </div>

            <form onSubmit={handleSearch} className="flex items-center gap-2">
                <div className="relative flex-grow">
                    <Search className="absolute left-3 top-1/2 -translate-y-1/2 h-5 w-5 text-slate-400" />
                    <input 
                        type="text"
                        value={searchTerm}
                        onChange={(e) => setSearchTerm(e.target.value)}
                        placeholder="Digite o CNPJ da empresa (somente números)"
                        className="bg-slate-700 border border-slate-600 rounded-md py-2 pl-10 pr-4 w-full text-white placeholder-slate-400 focus:outline-none focus:ring-1 focus:ring-sky-500"
                    />
                </div>
                <button 
                    type="submit"
                    disabled={loading}
                    className="bg-sky-600 text-white px-4 py-2 rounded-md font-semibold hover:bg-sky-500 disabled:bg-slate-500 disabled:cursor-not-allowed flex items-center gap-2"
                >
                    {loading ? 'Buscando...' : 'Buscar'}
                </button>
            </form>

            {error && (
                <div className="bg-red-900/50 border border-red-700 text-red-300 p-3 rounded-lg text-center">
                    {error}
                </div>
            )}
            
            <div className="bg-slate-800/50 rounded-lg border border-slate-700 overflow-hidden">
                <div className="overflow-x-auto">
                    <table className="w-full text-sm text-left text-slate-300">
                        <thead className="bg-slate-700/50 text-xs text-slate-400 uppercase">
                            <tr>
                                <th scope="col" className="px-6 py-3">Data Ref.</th>
                                <th scope="col" className="px-6 py-3">Empresa</th>
                                <th scope="col" className="px-6 py-3">Categoria</th>
                                <th scope="col" className="px-6 py-3">Assunto</th>
                                <th scope="col" className="px-6 py-3 text-center">Link</th>
                            </tr>
                        </thead>
                        <tbody>
                            {loading ? (
                                <tr>
                                    <td colSpan={5} className="text-center py-8 text-slate-400">
                                        <FileText className="mx-auto h-8 w-8 animate-pulse" />
                                        <p className="mt-2">Carregando documentos...</p>
                                    </td>
                                </tr>
                            ) : documents.length > 0 ? (
                                documents.map((doc) => (
                                    <tr key={doc.id} className="border-b border-slate-700 hover:bg-slate-700/40">
                                        <td className="px-6 py-4 whitespace-nowrap">{formatDate(doc.reference_date)}</td>
                                        <td className="px-6 py-4 font-medium text-white">{doc.company_name}</td>
                                        <td className="px-6 py-4">{doc.category}</td>
                                        <td className="px-6 py-4 max-w-sm truncate" title={doc.subject}>{doc.subject}</td>
                                        <td className="px-6 py-4 text-center">
                                            <a 
                                                href={doc.download_link} 
                                                target="_blank" 
                                                rel="noopener noreferrer" 
                                                className="text-sky-400 hover:text-sky-300 transition-colors"
                                                title="Baixar documento"
                                            >
                                                <DownloadCloud className="h-5 w-5 mx-auto"/>
                                            </a>
                                        </td>
                                    </tr>
                                ))
                            ) : !error && (
                                 <tr>
                                    <td colSpan={5} className="text-center py-8 text-slate-500">
                                        Nenhum documento para exibir. Realize uma busca.
                                    </td>
                                </tr>
                            )}
                        </tbody>
                    </table>
                </div>
            </div>
        </div>
    );
};

export default CvmDocuments;
