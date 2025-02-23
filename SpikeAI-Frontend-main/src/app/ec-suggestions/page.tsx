'use client';

import { useState, useEffect } from 'react';
import { useSession } from 'next-auth/react';
import { Loader2, AlertCircle, RefreshCw, Lock } from 'lucide-react';
import { useSubscriptionStatus } from '@/hooks/useSubscriptionStatus';
import { toast } from 'sonner';
import { ActivityGrid } from '@/components/ActivityGrid';
import { JetBrains_Mono } from 'next/font/google';
import {
    Button,
    Input,
    Select,
    SelectContent,
    SelectItem,
    SelectTrigger,
    SelectValue,
} from "@/components/ui";

const mono = JetBrains_Mono({ 
    subsets: ['latin'],
    variable: '--font-mono'
});

interface Activity {
    name: string;
    description: string;
    hours_per_week: number;
    activity_type: string;
    position?: string;
    added_at?: string;
}

const ACTIVITY_TYPES = [
    'Academic',
    'Athletic',
    'Arts',
    'Community Service',
    'Leadership',
    'Work Experience',
    'Research',
    'Other'
];

export default function ECRecommendationsPage() {
    const { data: session } = useSession();
    const [isLoading, setIsLoading] = useState(false);
    const [error, setError] = useState<string | null>(null);
    const { isSubscribed } = useSubscriptionStatus();
    
    // Input states
    const [activityType, setActivityType] = useState<string>('');
    const [hoursPerWeek, setHoursPerWeek] = useState<string>('');
    
    // Column states
    const [pastSuggestions, setPastSuggestions] = useState<Activity[]>([]);
    const [currentSuggestions, setCurrentSuggestions] = useState<Activity[]>([]);
    const [targetActivities, setTargetActivities] = useState<Activity[]>([]);
    
    // Pagination states
    const [pastPage, setPastPage] = useState(1);
    const [targetPage, setTargetPage] = useState(1);
    const [pastTotalPages, setPastTotalPages] = useState(1);
    const [targetTotalPages, setTargetTotalPages] = useState(1);

    // Loading states
    const [isPastLoading, setIsPastLoading] = useState(false);
    const [isCurrentLoading, setIsCurrentLoading] = useState(false);
    const [isTargetLoading, setIsTargetLoading] = useState(false);

    const fetchPastSuggestions = async (page = pastPage) => {
        if (!session?.user?.email) return;
        try {
            const response = await fetch(`/api/ec-suggestions/past-suggestions?page=${page}`);
            const data = await response.json();
            if (response.ok && data.success) {
                setPastSuggestions(data.data?.suggestions || []);
                setPastTotalPages(data.data?.total_pages || 1);
                return true;
            } else {
                throw new Error(data.error || 'Failed to fetch past suggestions');
            }
        } catch (error) {
            console.error('Failed to fetch past suggestions:', error);
            if (!isPastLoading) {
                toast.error('Failed to fetch past suggestions');
            }
            return false;
        }
    };

    const fetchCurrentSuggestions = async () => {
        if (!session?.user?.email) return;
        try {
            const response = await fetch('/api/ec-suggestions/current-suggestions');
            const data = await response.json();
            if (response.ok && data.success) {
                setCurrentSuggestions(data.data?.suggestions || []);
                return true;
            } else {
                throw new Error(data.error || 'Failed to fetch current suggestions');
            }
        } catch (error) {
            console.error('Failed to fetch current suggestions:', error);
            if (!isCurrentLoading) { // Only show error if not part of initial load
                toast.error('Failed to fetch current suggestions');
            }
            return false;
        }
    };

    const fetchTargetActivities = async (page = targetPage) => {
        if (!session?.user?.email) return;
        try {
            const response = await fetch(`/api/ec-suggestions/target-activities?page=${page}`);
            const data = await response.json();
            if (response.ok && data.success) {
                setTargetActivities(data.data?.activities || []);
                setTargetTotalPages(data.data?.total_pages || 1);
                return true;
            } else {
                throw new Error(data.error || 'Failed to fetch target activities');
            }
        } catch (error) {
            console.error('Failed to fetch target activities:', error);
            if (!isTargetLoading) { // Only show error if not part of initial load
                toast.error('Failed to fetch target activities');
            }
            return false;
        }
    };

    const handlePastPageChange = (page: number) => {
        setPastPage(page);
        setIsPastLoading(true);
        fetchPastSuggestions(page).finally(() => setIsPastLoading(false));
    };

    const handleTargetPageChange = (page: number) => {
        setTargetPage(page);
        setIsTargetLoading(true);
        fetchTargetActivities(page).finally(() => setIsTargetLoading(false));
    };

    const handleRefreshPast = () => {
        setIsPastLoading(true);
        fetchPastSuggestions(pastPage).finally(() => setIsPastLoading(false));
    };

    const handleRefreshCurrent = () => {
        setIsCurrentLoading(true);
        fetchCurrentSuggestions().finally(() => setIsCurrentLoading(false));
    };

    const handleRefreshTarget = () => {
        setIsTargetLoading(true);
        fetchTargetActivities(targetPage).finally(() => setIsTargetLoading(false));
    };

    const generateRecommendations = async () => {
        if (!session?.user?.email) {
            toast.error('Please sign in to generate recommendations');
            return;
        }

        if (!activityType) {
            toast.error('Please select an activity type');
            return;
        }

        if (!hoursPerWeek || isNaN(Number(hoursPerWeek)) || Number(hoursPerWeek) <= 0) {
            toast.error('Please enter valid hours per week');
            return;
        }

        setIsLoading(true);
        setError(null);

        try {
            const response = await fetch('/api/ec-suggestions', {
                method: 'POST',
                headers: {
                    'Content-Type': 'application/json',
                },
                body: JSON.stringify({
                    activity_type: activityType,
                    hrs_per_wk: Number(hoursPerWeek)
                }),
            });

            const data = await response.json();

            if (!response.ok || !data.success) {
                throw new Error(data.error || 'Failed to generate recommendations');
            }

            // Refresh all columns after generating new recommendations
            await Promise.all([
                fetchCurrentSuggestions(),
                fetchPastSuggestions(),
                fetchTargetActivities()
            ]);

            toast.success('Successfully generated recommendations');
        } catch (err) {
            console.error('Failed to generate recommendations:', err);
            setError(err instanceof Error ? err.message : 'An error occurred');
            toast.error('Failed to generate recommendations');
        } finally {
            setIsLoading(false);
        }
    };

    const handleAddActivity = async (activity: Activity, source: 'past' | 'current') => {
        if (!session?.user?.email) {
            toast.error('Please sign in to add activities to your list');
            return;
        }

        try {
            setIsCurrentLoading(true);
            setIsPastLoading(true);
            setIsTargetLoading(true);

            const response = await fetch('/api/ec-suggestions/add-target', {
                method: 'POST',
                headers: {
                    'Content-Type': 'application/json',
                },
                body: JSON.stringify({
                    activity: {
                        name: activity.name,
                        description: activity.description,
                        hours_per_week: activity.hours_per_week,
                        activity_type: activity.activity_type,
                        position: activity.position
                    },
                    source
                }),
            });

            const data = await response.json();

            if (!response.ok) {
                throw new Error(data.error || 'Failed to add activity');
            }

            // Refresh all columns
            await Promise.all([
                fetchCurrentSuggestions(),
                fetchPastSuggestions(pastPage),
                fetchTargetActivities(targetPage)
            ]);

            toast.success(`Added ${activity.name} to your target list`);
        } catch (err) {
            console.error('Failed to add activity:', err);
            toast.error(err instanceof Error ? err.message : 'Failed to add activity to target list');
        } finally {
            setIsCurrentLoading(false);
            setIsPastLoading(false);
            setIsTargetLoading(false);
        }
    };

    const handleDeleteActivity = async (activity: Activity, source: 'past' | 'current' | 'target') => {
        if (!session?.user?.email) {
            toast.error('Please sign in to delete activities');
            return;
        }

        try {
            // Only set loading state for the affected column
            if (source === 'current') setIsCurrentLoading(true);
            if (source === 'past') setIsPastLoading(true);
            if (source === 'target') setIsTargetLoading(true);

            const response = await fetch('/api/ec-suggestions/delete-activity', {
                method: 'POST',
                headers: {
                    'Content-Type': 'application/json',
                },
                body: JSON.stringify({
                    activity: {
                        name: activity.name
                    },
                    source
                }),
            });

            const data = await response.json();

            if (!response.ok) {
                throw new Error(data.error || 'Failed to delete activity');
            }

            // Only refresh the affected column
            if (source === 'current') await fetchCurrentSuggestions();
            if (source === 'past') await fetchPastSuggestions(pastPage);
            if (source === 'target') await fetchTargetActivities(targetPage);

            toast.success(`Deleted ${activity.name} from your ${source} list`);
        } catch (err) {
            console.error('Failed to delete activity:', err);
            toast.error(err instanceof Error ? err.message : 'Failed to delete activity');
        } finally {
            // Only reset loading state for the affected column
            if (source === 'current') setIsCurrentLoading(false);
            if (source === 'past') setIsPastLoading(false);
            if (source === 'target') setIsTargetLoading(false);
        }
    };

    // Fetch initial data
    useEffect(() => {
        let mounted = true;
        
        const fetchData = async () => {
            if (!session?.user?.email || !mounted) return;
            
            try {
                setIsPastLoading(true);
                setIsCurrentLoading(true);
                setIsTargetLoading(true);
                
                // Fetch all data in parallel
                const results = await Promise.allSettled([
                    fetchPastSuggestions(pastPage),
                    fetchCurrentSuggestions(),
                    fetchTargetActivities(targetPage)
                ]);
                
                // Handle any errors that occurred
                results.forEach((result, index) => {
                    if (result.status === 'rejected') {
                        console.error(`Failed to fetch data for column ${index}:`, result.reason);
                        toast.error('Failed to load some data. Please try refreshing.');
                    }
                });
            } catch (error) {
                console.error('Failed to fetch initial data:', error);
                toast.error('Failed to load data. Please try refreshing.');
            } finally {
                if (mounted) {
                    setIsPastLoading(false);
                    setIsCurrentLoading(false);
                    setIsTargetLoading(false);
                }
            }
        };

        fetchData();
        
        // Cleanup function
        return () => {
            mounted = false;
        };
    }, [session?.user?.email]); // Only re-run when session email changes

    return (
        <div className="container mx-auto px-4 py-8">
            <div className="flex justify-between items-start mb-8">
                <div>
                    <h1 className={`text-4xl font-bold mb-2 text-white ${mono.className}`}>EC Recommendations</h1>
                    <p className="text-gray-400">Get personalized extracurricular activity suggestions based on your interests</p>
                </div>
                <div className="flex items-center gap-6">
                    <div className="relative">
                        <Select
                            value={activityType}
                            onValueChange={setActivityType}
                        >
                            <SelectTrigger className={`w-[200px] h-[48px] bg-[#1A1A1A] border-2 border-gray-800 text-white hover:border-[#E87C3E] focus:border-[#E87C3E] transition-all rounded-xl ${mono.className}`}>
                                <SelectValue placeholder="Activity type" />
                            </SelectTrigger>
                            <SelectContent className="bg-[#1A1A1A] border-2 border-gray-800">
                                {ACTIVITY_TYPES.map(type => (
                                    <SelectItem 
                                        key={type} 
                                        value={type.toLowerCase()}
                                        className={`hover:bg-gray-800/50 focus:bg-gray-800/50 ${mono.className}`}
                                    >
                                        {type}
                                    </SelectItem>
                                ))}
                            </SelectContent>
                        </Select>
                    </div>
                    
                    <Input
                        type="number"
                        placeholder="Hours per week"
                        value={hoursPerWeek}
                        onChange={(e) => setHoursPerWeek(e.target.value)}
                        className={`w-[200px] h-[48px] bg-[#1A1A1A] border-2 border-gray-800 text-white placeholder:text-gray-500 hover:border-[#E87C3E] focus:border-[#E87C3E] transition-all rounded-xl ${mono.className}`}
                        min="1"
                    />
                    
                    <Button
                        onClick={generateRecommendations}
                        disabled={isLoading || !isSubscribed}
                        className={`h-[48px] px-8 bg-[#E87C3E] hover:bg-[#FF8D4E] text-white transition-all rounded-xl font-medium ${mono.className} disabled:opacity-50 disabled:cursor-not-allowed flex items-center gap-3`}
                    >
                        {isLoading ? (
                            <>
                                <Loader2 className="h-5 w-5 animate-spin" />
                                <span>Loading...</span>
                            </>
                        ) : !isSubscribed ? (
                            <>
                                <Lock className="h-5 w-5" />
                                <span>Upgrade</span>
                            </>
                        ) : (
                            <>
                                <RefreshCw className="h-5 w-5" />
                                <span>Recommend</span>
                            </>
                        )}
                    </Button>
                </div>
            </div>

            {error && (
                <div className="bg-red-900/20 border border-red-500/20 rounded-lg p-4 mb-8 flex items-start space-x-3">
                    <AlertCircle className="h-5 w-5 text-red-500 mt-0.5" />
                    <div>
                        <h3 className="text-red-500 font-medium">Error</h3>
                        <p className="text-red-400 text-sm mt-1">{error}</p>
                    </div>
                </div>
            )}

            {/* Three-column layout */}
            <div className="grid grid-cols-1 md:grid-cols-3 gap-6">
                {/* Past Suggestions */}
                <div className="bg-[#1A1A1A] rounded-lg border border-gray-800 p-4">
                    <div className="flex justify-between items-center mb-4">
                        <h2 className={`text-xl font-semibold text-white ${mono.className}`}>Past Suggestions</h2>
                        <Button
                            variant="outline"
                            size="sm"
                            onClick={handleRefreshPast}
                            disabled={isPastLoading}
                            className="border-gray-700 hover:bg-gray-800/50 text-gray-400"
                        >
                            {isPastLoading ? (
                                <Loader2 className="h-4 w-4 animate-spin" />
                            ) : (
                                <RefreshCw className="h-4 w-4" />
                            )}
                        </Button>
                    </div>
                    <ActivityGrid
                        activities={pastSuggestions}
                        onAddActivity={(activity) => handleAddActivity(activity, 'past')}
                        onDeleteActivity={(activity) => handleDeleteActivity(activity, 'past')}
                        isLoading={isPastLoading}
                        currentPage={pastPage}
                        totalPages={pastTotalPages}
                        onPageChange={handlePastPageChange}
                        noSuggestionsMessage="No past suggestions"
                        showAddButton
                        showDeleteButton
                    />
                </div>

                {/* Current Suggestions */}
                <div className="bg-[#1A1A1A] rounded-lg border border-gray-800 p-4">
                    <div className="flex justify-between items-center mb-4">
                        <h2 className={`text-xl font-semibold text-white ${mono.className}`}>Current Suggestions</h2>
                        <Button
                            variant="outline"
                            size="sm"
                            onClick={handleRefreshCurrent}
                            disabled={isCurrentLoading}
                            className="border-gray-700 hover:bg-gray-800/50 text-gray-400"
                        >
                            {isCurrentLoading ? (
                                <Loader2 className="h-4 w-4 animate-spin" />
                            ) : (
                                <RefreshCw className="h-4 w-4" />
                            )}
                        </Button>
                    </div>
                    <ActivityGrid
                        activities={currentSuggestions}
                        onAddActivity={(activity) => handleAddActivity(activity, 'current')}
                        onDeleteActivity={(activity) => handleDeleteActivity(activity, 'current')}
                        isLoading={isCurrentLoading}
                        noSuggestionsMessage="No current suggestions"
                        isCurrentSuggestions={true}
                        showAddButton
                        showDeleteButton
                    />
                </div>

                {/* Target Activities */}
                <div className="bg-[#1A1A1A] rounded-lg border border-gray-800 p-4">
                    <div className="flex justify-between items-center mb-4">
                        <h2 className={`text-xl font-semibold text-white ${mono.className}`}>Target Activities</h2>
                        <Button
                            variant="outline"
                            size="sm"
                            onClick={handleRefreshTarget}
                            disabled={isTargetLoading}
                            className="border-gray-700 hover:bg-gray-800/50 text-gray-400"
                        >
                            {isTargetLoading ? (
                                <Loader2 className="h-4 w-4 animate-spin" />
                            ) : (
                                <RefreshCw className="h-4 w-4" />
                            )}
                        </Button>
                    </div>
                    <ActivityGrid
                        activities={targetActivities}
                        onDeleteActivity={(activity) => handleDeleteActivity(activity, 'target')}
                        isLoading={isTargetLoading}
                        currentPage={targetPage}
                        totalPages={targetTotalPages}
                        onPageChange={handleTargetPageChange}
                        noSuggestionsMessage="No target activities"
                        showDeleteButton
                    />
                </div>
            </div>
        </div>
    );
} 