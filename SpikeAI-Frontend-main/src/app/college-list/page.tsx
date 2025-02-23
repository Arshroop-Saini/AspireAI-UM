'use client';

import { useState, useEffect } from 'react';
import { useSession } from 'next-auth/react';
import { Button } from '@/components/ui/button';
import { Loader2, AlertCircle, Plus, Lock, RefreshCw, ChevronDown } from 'lucide-react';
import { useSubscriptionStatus } from '@/hooks/useSubscriptionStatus';
import { toast } from 'sonner';
import { CollegeGrid } from '@/components/CollegeGrid';
import {
    DropdownMenu,
    DropdownMenuContent,
    DropdownMenuItem,
    DropdownMenuTrigger,
} from "@/components/ui/dropdown-menu";
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

interface CollegeListResponse {
    success: boolean;
    data?: {
        college_list: string;
    };
    error?: string;
}

export default function CollegeListPage() {
    const { data: session } = useSession();
    const [isLoading, setIsLoading] = useState(false);
    const [error, setError] = useState<string | null>(null);
    const { isSubscribed, isLoading: isSubscriptionLoading } = useSubscriptionStatus();
    
    // State for each column
    const [pastSuggestions, setPastSuggestions] = useState<College[]>([]);
    const [currentSuggestions, setCurrentSuggestions] = useState<College[]>([]);
    const [targetColleges, setTargetColleges] = useState<College[]>([]);
    
    // Pagination states
    const [pastPage, setPastPage] = useState(1);
    const [targetPage, setTargetPage] = useState(1);
    const [pastTotalPages, setPastTotalPages] = useState(1);
    const [targetTotalPages, setTargetTotalPages] = useState(1);

    // Loading states for each column
    const [isPastLoading, setIsPastLoading] = useState(false);
    const [isCurrentLoading, setIsCurrentLoading] = useState(false);
    const [isTargetLoading, setIsTargetLoading] = useState(false);

    const fetchPastSuggestions = async (page = pastPage) => {
        if (!session?.user?.email) return;
        setIsPastLoading(true);
        try {
            const response = await fetch(`/api/college-list/past-suggestions?page=${page}`, {
                headers: {
                    'Content-Type': 'application/json'
                }
            });
            const data = await response.json();
            if (response.ok) {
                setPastSuggestions(data.suggestions || []);
                setPastTotalPages(data.total_pages || 1);
            } else {
                throw new Error(data.error || 'Failed to fetch past suggestions');
            }
        } catch (error) {
            console.error('Failed to fetch past suggestions:', error);
            toast.error('Failed to fetch past suggestions');
        } finally {
            setIsPastLoading(false);
        }
    };

    const fetchCurrentSuggestions = async () => {
        if (!session?.user?.email) return;
        setIsCurrentLoading(true);
        try {
            const response = await fetch('/api/college-list/current-suggestions', {
                headers: {
                    'Content-Type': 'application/json'
                }
            });
            const data = await response.json();
            if (response.ok && data.success) {
                setCurrentSuggestions(data.data?.suggestions || []);
            } else {
                throw new Error(data.error || 'Failed to fetch current suggestions');
            }
        } catch (error) {
            console.error('Failed to fetch current suggestions:', error);
            toast.error('Failed to fetch current suggestions');
        } finally {
            setIsCurrentLoading(false);
        }
    };

    const fetchTargetColleges = async (page = targetPage) => {
        if (!session?.user?.email) return;
        setIsTargetLoading(true);
        try {
            const response = await fetch(`/api/college-list/target-colleges?page=${page}`, {
                headers: {
                    'Content-Type': 'application/json'
                }
            });
            const data = await response.json();
            if (response.ok) {
                setTargetColleges(data.colleges || []);
                setTargetTotalPages(data.total_pages || 1);
            } else {
                throw new Error(data.error || 'Failed to fetch target colleges');
            }
        } catch (error) {
            console.error('Failed to fetch target colleges:', error);
            toast.error('Failed to fetch target colleges');
        } finally {
            setIsTargetLoading(false);
        }
    };

    const handlePastPageChange = (page: number) => {
        setPastPage(page);
        fetchPastSuggestions(page);
    };

    const handleTargetPageChange = (page: number) => {
        setTargetPage(page);
        fetchTargetColleges(page);
    };

    const generateCollegeList = async (type: 'safety' | 'target' | 'reach') => {
        if (!session?.user?.email) {
            toast.error('Please sign in to generate college suggestions');
            return;
        }

        setIsLoading(true);
        setError(null);

        try {
            const response = await fetch('/api/college-list', {
                method: 'POST',
                headers: {
                    'Content-Type': 'application/json',
                },
                body: JSON.stringify({
                    email: session.user.email,
                    type
                }),
            });

            const data: CollegeListResponse = await response.json();

            if (!data.success || !data.data) {
                throw new Error(data.error || 'Failed to generate college list');
            }

            // Refresh all columns after generating new list
            await Promise.all([
                fetchCurrentSuggestions(),
                fetchPastSuggestions(),
                fetchTargetColleges()
            ]);
        } catch (err) {
            setError(err instanceof Error ? err.message : 'An error occurred');
            toast.error('Failed to generate college list');
        } finally {
            setIsLoading(false);
        }
    };

    const handleAddCollege = async (college: College, source: 'past' | 'current') => {
        if (!session?.user?.email) {
            toast.error('Please sign in to add colleges to your list');
            return;
        }

        try {
            // Map source to backend expected values
            const mappedSource = source === 'current' ? 'temp' : 'permanent';

            const response = await fetch('/api/college-list/add-target', {
                method: 'POST',
                headers: {
                    'Content-Type': 'application/json',
                },
                body: JSON.stringify({
                    college_name: college.name,
                    source: mappedSource
                }),
            });

            const data = await response.json();

            if (!response.ok) {
                throw new Error(data.error || 'Failed to add college');
            }

            // Refresh all columns after adding college
            await Promise.all([
                fetchCurrentSuggestions(),
                fetchPastSuggestions(),
                fetchTargetColleges()
            ]);

            toast.success(`Added ${college.name} to your target list`);
        } catch (err) {
            console.error('Failed to add college:', err);
            toast.error(err instanceof Error ? err.message : 'Failed to add college');
        }
    };

    const handleDeleteCollege = async (college: College, source: 'target' | 'past' | 'current') => {
        try {
            const response = await fetch('/api/college-list/delete-college', {
                method: 'POST',
                headers: {
                    'Content-Type': 'application/json',
                },
                body: JSON.stringify({
                    college_name: college.name,
                    source,
                }),
            });

            const data = await response.json();
            if (data.success) {
                // Update local state based on source
                if (source === 'target') {
                    setTargetColleges(prev => prev.filter(c => c.name !== college.name));
                } else if (source === 'past') {
                    setPastSuggestions(prev => prev.filter(c => c.name !== college.name));
                } else if (source === 'current') {
                    setCurrentSuggestions(prev => prev.filter(c => c.name !== college.name));
                }
                toast.success(`Successfully removed ${college.name} from your ${source} list`);
            } else {
                toast.error(data.error || 'Failed to remove college');
            }
        } catch (error) {
            console.error('Error deleting college:', error);
            toast.error('Failed to remove college');
        }
    };

    // Add useEffect to fetch initial data
    useEffect(() => {
        if (session?.user?.email) {
            Promise.all([
                fetchCurrentSuggestions(),
                fetchPastSuggestions(),
                fetchTargetColleges()
            ]);
        }
    }, [session?.user?.email]);

    return (
        <div className="min-h-screen bg-black">
            <div className="container mx-auto px-4 py-8">
                <div className="space-y-8">
                    <div className="flex flex-col md:flex-row justify-between items-start md:items-center gap-4">
                        <div>
                            <h1 className={`text-4xl font-bold text-white ${mono.className}`}>College List Generator</h1>
                            <p className="text-gray-400 mt-2 text-lg">
                                Get personalized college suggestions based on your profile
                            </p>
                        </div>
                        {!isSubscriptionLoading && (
                            <DropdownMenu>
                                <DropdownMenuTrigger asChild>
                                    <Button
                                        disabled={isLoading || !isSubscribed}
                                        className={`flex items-center space-x-2 bg-[#E87C3E] hover:bg-[#FF8D4E] text-white ${mono.className}`}
                                    >
                                        {isLoading ? (
                                            <>
                                                <Loader2 className="h-5 w-5 animate-spin" />
                                                <span>Generating...</span>
                                            </>
                                        ) : !isSubscribed ? (
                                            <>
                                                <Lock className="h-5 w-5" />
                                                <span>Upgrade to Generate</span>
                                            </>
                                        ) : (
                                            <>
                                                <Plus className="h-5 w-5" />
                                                <span>Generate New List</span>
                                                <ChevronDown className="h-5 w-5 ml-2" />
                                            </>
                                        )}
                                    </Button>
                                </DropdownMenuTrigger>
                                <DropdownMenuContent align="end" className="w-56 bg-[#1A1A1A] border border-gray-800">
                                    <DropdownMenuItem
                                        onClick={() => generateCollegeList('safety')}
                                        className="cursor-pointer text-gray-200 hover:bg-gray-800 focus:bg-gray-800"
                                    >
                                        Generate Safety Schools
                                    </DropdownMenuItem>
                                    <DropdownMenuItem
                                        onClick={() => generateCollegeList('target')}
                                        className="cursor-pointer text-gray-200 hover:bg-gray-800 focus:bg-gray-800"
                                    >
                                        Generate Target Schools
                                    </DropdownMenuItem>
                                    <DropdownMenuItem
                                        onClick={() => generateCollegeList('reach')}
                                        className="cursor-pointer text-gray-200 hover:bg-gray-800 focus:bg-gray-800"
                                    >
                                        Generate Reach Schools
                                    </DropdownMenuItem>
                                </DropdownMenuContent>
                            </DropdownMenu>
                        )}
                    </div>

                    {error && (
                        <div className="bg-red-900/20 border border-red-500/20 rounded-xl p-4 flex items-start space-x-3">
                            <AlertCircle className="h-5 w-5 text-red-500 mt-0.5" />
                            <div>
                                <h3 className="text-red-500 font-medium">Error</h3>
                                <p className="text-red-400 text-sm mt-1">{error}</p>
                            </div>
                        </div>
                    )}

                    <div className="grid grid-cols-1 md:grid-cols-3 gap-8">
                        {/* Past Suggestions Column */}
                        <div className="bg-[#1A1A1A] rounded-xl border border-gray-800 p-6">
                            <div className="flex justify-between items-center mb-6">
                                <h2 className={`text-2xl font-semibold text-white ${mono.className}`}>Past Suggestions</h2>
                                <Button
                                    variant="outline"
                                    size="sm"
                                    onClick={() => fetchPastSuggestions(1)}
                                    disabled={isPastLoading}
                                    className="bg-transparent border-gray-800 text-gray-400 hover:text-white hover:border-[#E87C3E] hover:bg-[#E87C3E]/10 transition-colors"
                                >
                                    {isPastLoading ? (
                                        <Loader2 className="h-4 w-4 animate-spin text-[#E87C3E]" />
                                    ) : (
                                        <RefreshCw className="h-4 w-4" />
                                    )}
                                </Button>
                            </div>
                            <CollegeGrid
                                colleges={pastSuggestions}
                                onAddCollege={(college) => handleAddCollege(college, 'past')}
                                onDeleteCollege={(college) => handleDeleteCollege(college, 'past')}
                                isLoading={isPastLoading}
                                noSuggestionsMessage="No past suggestions"
                                totalPages={pastTotalPages}
                                currentPage={pastPage}
                                onPageChange={handlePastPageChange}
                            />
                        </div>

                        {/* Current Suggestions Column */}
                        <div className="bg-[#1A1A1A] rounded-xl border border-gray-800 p-6">
                            <div className="flex justify-between items-center mb-6">
                                <h2 className={`text-2xl font-semibold text-white ${mono.className}`}>Current Suggestions</h2>
                                <Button
                                    variant="outline"
                                    size="sm"
                                    onClick={fetchCurrentSuggestions}
                                    disabled={isCurrentLoading}
                                    className="bg-transparent border-gray-800 text-gray-400 hover:text-white hover:border-[#E87C3E] hover:bg-[#E87C3E]/10 transition-colors"
                                >
                                    {isCurrentLoading ? (
                                        <Loader2 className="h-4 w-4 animate-spin text-[#E87C3E]" />
                                    ) : (
                                        <RefreshCw className="h-4 w-4" />
                                    )}
                                </Button>
                            </div>
                            <CollegeGrid
                                colleges={currentSuggestions}
                                onAddCollege={(college) => handleAddCollege(college, 'current')}
                                onDeleteCollege={(college) => handleDeleteCollege(college, 'current')}
                                isLoading={isCurrentLoading}
                                noSuggestionsMessage="No current suggestions"
                                isCurrentSuggestions={true}
                            />
                        </div>

                        {/* Target Colleges Column */}
                        <div className="bg-[#1A1A1A] rounded-xl border border-gray-800 p-6">
                            <div className="flex justify-between items-center mb-6">
                                <h2 className={`text-2xl font-semibold text-white ${mono.className}`}>Target Colleges</h2>
                                <Button
                                    variant="outline"
                                    size="sm"
                                    onClick={() => fetchTargetColleges(1)}
                                    disabled={isTargetLoading}
                                    className="bg-transparent border-gray-800 text-gray-400 hover:text-white hover:border-[#E87C3E] hover:bg-[#E87C3E]/10 transition-colors"
                                >
                                    {isTargetLoading ? (
                                        <Loader2 className="h-4 w-4 animate-spin text-[#E87C3E]" />
                                    ) : (
                                        <RefreshCw className="h-4 w-4" />
                                    )}
                                </Button>
                            </div>
                            <CollegeGrid
                                colleges={targetColleges}
                                onDeleteCollege={(college) => handleDeleteCollege(college, 'target')}
                                isLoading={isTargetLoading}
                                noSuggestionsMessage="No target colleges"
                                totalPages={targetTotalPages}
                                currentPage={targetPage}
                                onPageChange={handleTargetPageChange}
                            />
                        </div>
                    </div>
                </div>
            </div>
        </div>
    );
} 