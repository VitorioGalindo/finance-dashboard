
import React, { useState } from 'react';
import { MagnifyingGlassIcon } from '../constants';

interface HeaderProps {
    onSearch: (ticker: string) => void;
}

const Header: React.FC<HeaderProps> = ({ onSearch }) => {
    const [searchTerm, setSearchTerm] = useState('');

    const handleSubmit = (e: React.FormEvent) => {
        e.preventDefault();
        if (searchTerm.trim()) {
            onSearch(searchTerm.trim());
        }
    };

    return (
        <header className="flex-shrink-0 bg-slate-900 border-b border-slate-800">
            <div className="flex items-center justify-between h-16 px-4 sm:px-6 lg:px-8">
                {/* Left side spacer */}
                <div className="w-1/3"></div>

                {/* Center Search Bar */}
                <div className="w-1/3 flex justify-center">
                    <form onSubmit={handleSubmit} className="w-full max-w-md">
                        <div className="relative">
                            <div className="pointer-events-none absolute inset-y-0 left-0 flex items-center pl-3">
                                <MagnifyingGlassIcon />
                            </div>
                            <input
                                type="search"
                                name="search"
                                id="search"
                                value={searchTerm}
                                onChange={(e) => setSearchTerm(e.target.value)}
                                className="block w-full rounded-md border-0 bg-slate-800 py-2 pl-10 pr-3 text-slate-300 ring-1 ring-inset ring-slate-700 placeholder:text-slate-500 focus:ring-2 focus:ring-inset focus:ring-sky-500 sm:text-sm"
                                placeholder="Buscar ativo ou ferramenta"
                            />
                        </div>
                    </form>
                </div>

                {/* Right side icons */}
                <div className="w-1/3 flex items-center justify-end space-x-4">
                    <button className="p-2 rounded-full text-slate-400 hover:bg-slate-800 hover:text-white">
                        <svg xmlns="http://www.w3.org/2000/svg" className="h-6 w-6" fill="none" viewBox="0 0 24 24" stroke="currentColor"><path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M4 6h16M4 12h16m-7 6h7" /></svg>
                    </button>
                    <button className="p-2 rounded-full text-slate-400 hover:bg-slate-800 hover:text-white">
                        <svg xmlns="http://www.w3.org/2000/svg" className="h-6 w-6" fill="none" viewBox="0 0 24 24" stroke="currentColor"><path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M15 17h5l-1.405-1.405A2.032 2.032 0 0118 14.158V11a6.002 6.002 0 00-4-5.659V5a2 2 0 10-4 0v.341C7.67 6.165 6 8.388 6 11v3.159c0 .538-.214 1.055-.595 1.436L4 17h5m6 0v1a3 3 0 11-6 0v-1m6 0H9" /></svg>
                    </button>
                    <button className="p-2 rounded-full text-slate-400 hover:bg-slate-800 hover:text-white">
                        <svg xmlns="http://www.w3.org/2000/svg" className="h-6 w-6" fill="none" viewBox="0 0 24 24" stroke="currentColor"><path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M12 5v.01M12 12v.01M12 19v.01M12 6a1 1 0 110-2 1 1 0 010 2zm0 7a1 1 0 110-2 1 1 0 010 2zm0 7a1 1 0 110-2 1 1 0 010 2z" /></svg>
                    </button>
                </div>
            </div>
        </header>
    );
};

export default Header;
