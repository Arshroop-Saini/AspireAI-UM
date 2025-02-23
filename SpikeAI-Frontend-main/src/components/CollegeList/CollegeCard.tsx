import React from 'react';
import { Add as AddIcon, Delete as DeleteIcon } from '@mui/icons-material';
import { JetBrains_Mono } from 'next/font/google';

const mono = JetBrains_Mono({ 
    subsets: ['latin'],
    variable: '--font-mono'
});

interface CollegeCardProps {
    name: string;
    type: string;
    added_at?: string;
    onAdd?: () => void;
    onDelete?: () => void;
    showAddButton?: boolean;
    showDeleteButton?: boolean;
}

const CollegeCard: React.FC<CollegeCardProps> = ({
    name,
    type,
    added_at,
    onAdd,
    onDelete,
    showAddButton = false,
    showDeleteButton = false,
}) => {
    const handleAdd = (e: React.MouseEvent) => {
        e.stopPropagation();
        if (onAdd) onAdd();
    };

    const handleDelete = (e: React.MouseEvent) => {
        e.stopPropagation();
        if (onDelete) onDelete();
    };

    return (
        <div className="min-h-[140px] p-6 rounded-lg bg-[#1A1A1A] border border-gray-800 hover:border-gray-700 transition-all duration-300">
            <div className="flex justify-between items-start h-full">
                <div className="flex-1 min-w-0 space-y-2">
                    <h3 className={`text-lg text-white truncate ${mono.className}`} title={name}>
                        {name}
                    </h3>
                    <div className="flex items-center gap-2">
                        <span className={`${mono.className} px-2 py-1 text-xs bg-gray-800/50 border border-gray-700 rounded-full text-gray-300`}>
                            {type}
                        </span>
                    </div>
                    {added_at && (
                        <p className={`text-sm text-gray-500 ${mono.className}`}>
                            Added: {new Date(added_at).toLocaleDateString()}
                        </p>
                    )}
                </div>
                <div className="flex items-center space-x-2 ml-4 shrink-0">
                    {showAddButton && onAdd && (
                        <button
                            onClick={handleAdd}
                            className="p-1.5 rounded-md text-[#E87C3E] hover:bg-[#E87C3E]/10 transition-colors"
                            aria-label="add to target list"
                        >
                            <AddIcon className="w-5 h-5" />
                        </button>
                    )}
                    {showDeleteButton && onDelete && (
                        <button
                            onClick={handleDelete}
                            className="p-1.5 rounded-md text-gray-500 hover:text-red-500 hover:bg-red-500/10 transition-colors"
                            aria-label="delete from list"
                        >
                            <DeleteIcon className="w-5 h-5" />
                        </button>
                    )}
                </div>
            </div>
        </div>
    );
};

export default CollegeCard; 