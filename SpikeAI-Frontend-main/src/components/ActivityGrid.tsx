import React, { useState, useEffect } from 'react';
import { Loader2, AlertCircle } from "lucide-react";
import { Add as AddIcon, Delete as DeleteIcon } from '@mui/icons-material';
import {
    Card,
    CardContent,
    Button
} from "@/components/ui";
import { JetBrains_Mono } from 'next/font/google';

interface Activity {
    name: string;
    description: string;
    hours_per_week: number;
    activity_type: string;
    position?: string;
    added_at?: string;
}

interface ActivityGridProps {
    activities: Activity[];
    onAddActivity?: (activity: Activity) => void;
    onDeleteActivity?: (activity: Activity) => void;
    isLoading?: boolean;
    currentPage?: number;
    totalPages?: number;
    onPageChange?: (page: number) => void;
    noSuggestionsMessage?: string;
    isCurrentSuggestions?: boolean;
    showAddButton?: boolean;
    showDeleteButton?: boolean;
}

const mono = JetBrains_Mono({ 
    subsets: ['latin'],
    variable: '--font-mono'
});

export function ActivityGrid({
    activities = [],
    onAddActivity,
    onDeleteActivity,
    isLoading = false,
    currentPage = 1,
    totalPages = 1,
    onPageChange,
    noSuggestionsMessage = "No activities found",
    isCurrentSuggestions = false,
    showAddButton = false,
    showDeleteButton = false
}: ActivityGridProps) {
    const [showWarning, setShowWarning] = useState(false);

    useEffect(() => {
        if (isCurrentSuggestions && activities.length > 0 && activities.length < 5) {
            setShowWarning(true);
            // Hide warning after 10 seconds
            const timer = setTimeout(() => {
                setShowWarning(false);
            }, 10000);
            return () => clearTimeout(timer);
        }
    }, [isCurrentSuggestions, activities.length]);

    const renderWarningMessage = () => {
        if (!isCurrentSuggestions || !showWarning) return null;
        
        if (activities.length === 0) {
            return (
                <div className="bg-amber-900/20 border border-amber-500/20 rounded-lg p-4 mb-6">
                    <p className={`text-amber-400 text-sm ${mono.className}`}>
                        Out of all unique suggestions. Please tweak your preferences to find more unique matches.
                    </p>
                </div>
            );
        } else if (activities.length < 5) {
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

    if (isLoading) {
        return (
            <div className="flex justify-center items-center min-h-[200px]">
                <Loader2 className="h-8 w-8 animate-spin text-amber-500" />
            </div>
        );
    }

    if (!activities.length) {
        return (
            <div className="flex flex-col items-center justify-center min-h-[200px] text-center p-6 bg-[#1A1A1A] rounded-lg border border-gray-800">
                {renderWarningMessage()}
                <AlertCircle className="w-12 h-12 text-gray-600 mb-4" />
                <h3 className={`text-xl text-white mb-2 ${mono.className}`}>
                    No Activities Found
                </h3>
                <p className={`text-gray-400 ${mono.className}`}>
                    {noSuggestionsMessage}
                </p>
            </div>
        );
    }

    return (
        <div className="space-y-6">
            {isLoading ? (
                <div className="grid grid-cols-1 gap-6">
                    {[...Array(3)].map((_, i) => (
                        <div key={i} className="h-[200px] bg-gray-800/20 rounded-lg animate-pulse" />
                    ))}
                </div>
            ) : activities.length === 0 ? (
                renderWarningMessage()
            ) : (
                <>
                    <div className="grid grid-cols-1 gap-6">
                        {activities.map((activity, index) => (
                            <Card key={`${activity.name}-${index}`} className="bg-[#1A1A1A] border border-gray-800 hover:border-gray-700 transition-all duration-300 h-[200px]">
                                <CardContent className="p-6 flex flex-col h-full">
                                    <div className="flex justify-between items-start flex-1">
                                        <div className="space-y-2 flex-1 min-w-0">
                                            <h3 className={`${mono.className} text-lg text-white truncate`} title={activity.name}>
                                                {activity.name}
                                            </h3>
                                            <div className="flex items-center gap-2 flex-wrap">
                                                <span className={`${mono.className} px-2 py-1 text-xs bg-gray-800/50 border border-gray-700 rounded-full text-gray-300`}>
                                                    {activity.activity_type}
                                                </span>
                                                <span className={`${mono.className} px-2 py-1 text-xs bg-gray-800/50 border border-gray-700 rounded-full text-gray-300`}>
                                                    {activity.hours_per_week} hrs/week
                                                </span>
                                            </div>
                                            <p className={`text-sm text-gray-400 line-clamp-2 ${mono.className}`}>{activity.description}</p>
                                        </div>
                                        <div className="flex items-start space-x-2 ml-4 shrink-0">
                                            {showAddButton && onAddActivity && (
                                                <Button
                                                    onClick={() => onAddActivity(activity)}
                                                    variant="ghost"
                                                    size="sm"
                                                    className="p-1.5 text-[#E87C3E] hover:bg-[#E87C3E]/10 transition-colors"
                                                >
                                                    <AddIcon className="w-5 h-5" />
                                                </Button>
                                            )}
                                            {showDeleteButton && onDeleteActivity && (
                                                <Button
                                                    onClick={() => onDeleteActivity(activity)}
                                                    variant="ghost"
                                                    size="sm"
                                                    className="p-1.5 text-gray-500 hover:text-red-500 hover:bg-red-500/10 transition-colors"
                                                >
                                                    <DeleteIcon className="w-5 h-5" />
                                                </Button>
                                            )}
                                        </div>
                                    </div>
                                    {activity.added_at && (
                                        <p className={`text-xs text-gray-500 ${mono.className} mt-auto pt-4`}>
                                            Added: {new Date(activity.added_at).toLocaleDateString()}
                                        </p>
                                    )}
                                </CardContent>
                            </Card>
                        ))}
                    </div>
                    {totalPages > 1 && onPageChange && (
                        <div className="flex justify-center mt-6">
                            <nav className="flex items-center space-x-2">
                                {Array.from({ length: totalPages }, (_, i) => i + 1).map((page) => (
                                    <button
                                        key={page}
                                        onClick={() => onPageChange(page)}
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
                </>
            )}
        </div>
    );
} 