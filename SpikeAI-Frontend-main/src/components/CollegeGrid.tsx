import React from 'react';
import { CircularProgress } from '@mui/material';
import CollegeCard from './CollegeList/CollegeCard';
import { School as SchoolIcon } from '@mui/icons-material';
import { JetBrains_Mono } from 'next/font/google';

const mono = JetBrains_Mono({ 
    subsets: ['latin'],
    variable: '--font-mono'
});

interface College {
    name: string;
    type: string;
    added_at?: string;
}

interface CollegeGridProps {
    colleges: College[];
    onAddCollege?: (college: College) => void;
    onDeleteCollege?: (college: College) => void;
    isLoading?: boolean;
    noSuggestionsMessage?: string;
    isCurrentSuggestions?: boolean;
    totalPages?: number;
    currentPage?: number;
    onPageChange?: (page: number) => void;
}

export const CollegeGrid: React.FC<CollegeGridProps> = ({
    colleges,
    onAddCollege,
    onDeleteCollege,
    isLoading = false,
    noSuggestionsMessage = 'No colleges found',
    isCurrentSuggestions = false,
    totalPages = 1,
    currentPage = 1,
    onPageChange
}) => {
    const renderWarningMessage = () => {
        if (!isCurrentSuggestions) return null;

        if (colleges.length === 0) {
            return (
                <div className="bg-amber-900/20 border border-amber-500/20 rounded-lg p-4 mb-6">
                    <p className={`text-amber-400 text-sm ${mono.className}`}>
                        Out of all unique suggestions. Please tweak your preferences to find more unique matches.
                    </p>
                </div>
            );
        } else if (colleges.length < 5) {
            return (
                <div className="bg-amber-900/20 border border-amber-500/20 rounded-lg p-4 mb-6">
                    <p className={`text-amber-400 text-sm ${mono.className}`}>
                        Limited suggestions: Running out of unique suggestions. Please edit some of your preferences to get newer suggestions.
                    </p>
                </div>
            );
        }
        return null;
    };

    const handlePageChange = (value: number) => {
        if (onPageChange) {
            onPageChange(value);
        }
    };

    if (isLoading) {
        return (
            <div className="flex justify-center items-center min-h-[200px]">
                <CircularProgress sx={{ color: '#E87C3E' }} />
            </div>
        );
    }

    if (!colleges.length) {
        return (
            <div className="flex flex-col items-center justify-center min-h-[200px] text-center p-6">
                {renderWarningMessage()}
                <SchoolIcon className="w-12 h-12 text-gray-600 mb-4" />
                <h3 className={`text-xl text-white mb-2 ${mono.className}`}>
                    No Colleges Found
                </h3>
                <p className={`text-gray-400 ${mono.className}`}>
                    {noSuggestionsMessage}
                </p>
            </div>
        );
    }

    return (
        <div className="w-full">
            {renderWarningMessage()}
            <div className="space-y-4">
                {colleges.map((college, index) => (
                    <CollegeCard
                        key={`${college.name}-${index}`}
                        name={college.name}
                        type={college.type}
                        added_at={college.added_at}
                        onAdd={onAddCollege ? () => onAddCollege(college) : undefined}
                        onDelete={onDeleteCollege ? () => onDeleteCollege(college) : undefined}
                        showAddButton={!!onAddCollege}
                        showDeleteButton={!!onDeleteCollege}
                    />
                ))}
            </div>
            {totalPages > 1 && (
                <div className="flex justify-center mt-6">
                    <nav className="flex items-center space-x-2">
                        {Array.from({ length: totalPages }, (_, i) => i + 1).map((page) => (
                            <button
                                key={page}
                                onClick={() => handlePageChange(page)}
                                className={`px-3 py-1 rounded-md text-sm ${mono.className} ${
                                    currentPage === page
                                        ? 'bg-[#E87C3E] text-white'
                                        : 'text-gray-400 hover:bg-gray-800'
                                }`}
                            >
                                {page}
                            </button>
                        ))}
                    </nav>
                </div>
            )}
        </div>
    );
}; 