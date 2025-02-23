'use client';

import { useState, useEffect } from 'react';
import { useSession } from 'next-auth/react';
import { Button } from '@/components/ui/button';
import { Input } from '@/components/ui/input';
import { Textarea } from '@/components/ui/textarea';
import { Label } from '@radix-ui/react-label';
import { Alert, AlertDescription } from '@/components/ui/alert';
import EssayThreadList from '@/components/EssayThreadList';
import EssayBrainstormThread from '@/components/EssayBrainstormThread';

interface EssayThread {
    thread_id: string;
    college_name: string;
    essay_prompt: string;
    word_limit: number;
    ideas: Array<{
        content: string;
        created_at: string;
    }>;
    created_at: string;
    updated_at: string;
    status: 'pending' | 'completed' | 'error';
}

interface EssayBrainstormForm {
    college_name: string;
    essay_prompt: string;
    word_limit: number;
}

export default function EssayBrainstormForm() {
    const { data: session } = useSession();
    const [isLoading, setIsLoading] = useState(false);
    const [error, setError] = useState<string | null>(null);
    const [success, setSuccess] = useState<string | null>(null);
    const [threads, setThreads] = useState<EssayThread[]>([]);
    const [selectedThreadId, setSelectedThreadId] = useState<string | null>(null);
    const [formData, setFormData] = useState<EssayBrainstormForm>({
        college_name: '',
        essay_prompt: '',
        word_limit: 0
    });

    useEffect(() => {
        if (session?.user) {
            fetchThreads();
        }
    }, [session]);

    const fetchThreads = async () => {
        try {
            const response = await fetch('/api/essay-brainstorm/threads');
            if (!response.ok) {
                throw new Error('Failed to fetch threads');
            }
            const data = await response.json();
            setThreads(data.threads || []);
        } catch (error) {
            console.error('Error fetching threads:', error);
            setError('Failed to load essay brainstorming threads');
        }
    };

    const handleInputChange = (
        e: React.ChangeEvent<HTMLInputElement | HTMLTextAreaElement>,
        field: keyof EssayBrainstormForm
    ) => {
        setFormData(prev => ({
            ...prev,
            [field]: e.target.value
        }));
    };

    const handleNewThread = () => {
        setSelectedThreadId(null);
        setFormData({
            college_name: '',
            essay_prompt: '',
            word_limit: 0
        });
    };

    const handleThreadSelect = async (threadId: string) => {
        try {
            setSelectedThreadId(threadId);
            const thread = threads.find(t => t.thread_id === threadId);
            if (thread) {
                setFormData({
                    college_name: thread.college_name,
                    essay_prompt: thread.essay_prompt,
                    word_limit: thread.word_limit
                });
            }
        } catch (error) {
            console.error('Error selecting thread:', error);
            setError('Failed to load thread details');
        }
    };

    const handleDeleteThread = async (threadId: string) => {
        try {
            const response = await fetch(`/api/essay-brainstorm/threads?threadId=${threadId}`, {
                method: 'DELETE'
            });

            if (!response.ok) {
                throw new Error('Failed to delete thread');
            }

            await fetchThreads();
            if (selectedThreadId === threadId) {
                handleNewThread();
            }
        } catch (error) {
            console.error('Error deleting thread:', error);
            setError('Failed to delete thread');
        }
    };

    const handleSubmit = async (e: React.FormEvent) => {
        if (e) e.preventDefault();
        setIsLoading(true);
        setError(null);
        setSuccess(null);

        try {
            // Validate required fields for new threads
            if (!selectedThreadId) {
                if (!formData.college_name.trim()) {
                    throw new Error('College name is required');
                }
                if (!formData.essay_prompt.trim()) {
                    throw new Error('Essay prompt is required');
                }
            }

            const requestBody = {
                college_name: formData.college_name,
                essay_prompt: formData.essay_prompt,
                word_limit: formData.word_limit,
                is_new_thread: !selectedThreadId,
                ...(selectedThreadId && { thread_id: selectedThreadId })
            };

            const response = await fetch('/api/essay-brainstorm', {
                method: 'POST',
                headers: {
                    'Content-Type': 'application/json',
                },
                body: JSON.stringify(requestBody),
            });

            const data = await response.json();
            
            if (!response.ok) {
                throw new Error(data.error || 'Failed to generate ideas');
            }

            // If this was a new thread, set it as selected
            if (!selectedThreadId && data.data?.thread_id) {
                setSelectedThreadId(data.data.thread_id);
            }

            // Refresh the threads list
            await fetchThreads();

            // Only reset form if this was a new thread
            if (!selectedThreadId) {
                setFormData({
                    college_name: '',
                    essay_prompt: '',
                    word_limit: 0
                });
            }

            setSuccess('Successfully generated essay ideas!');
        } catch (error) {
            console.error('Error:', error);
            setError(error instanceof Error ? error.message : 'An error occurred');
        } finally {
            setIsLoading(false);
        }
    };

    return (
        <div className="flex h-screen bg-[#000000]">
            {/* Thread List */}
            <div className="w-[280px] border-r border-gray-800 bg-[#000000]">
                <EssayThreadList
                    threads={threads}
                    selectedThreadId={selectedThreadId}
                    onThreadSelect={handleThreadSelect}
                    onNewThread={handleNewThread}
                    onDeleteThread={handleDeleteThread}
                />
            </div>
            
            <div className="flex-1 flex flex-col overflow-hidden">
                {error && (
                    <Alert variant="destructive" className="m-4 bg-red-900 border-red-700">
                        <AlertDescription>{error}</AlertDescription>
                    </Alert>
                )}
                {success && (
                    <Alert className="m-4 bg-green-900 border-green-700">
                        <AlertDescription>{success}</AlertDescription>
                    </Alert>
                )}
                
                {!selectedThreadId ? (
                    // New Essay Form
                    <div className="flex-1 overflow-y-auto">
                        <div className="max-w-2xl mx-auto pt-8 px-4">
                            <div className="space-y-6">
                                <div>
                                    <h2 className="text-lg font-semibold text-white">New Essay</h2>
                                    <p className="text-sm text-zinc-500">
                                        Enter your essay details to get brainstorming ideas.
                                    </p>
                                </div>

                                <form onSubmit={handleSubmit} className="space-y-6">
                                    <div className="space-y-4">
                                        <div className="space-y-2">
                                            <Label htmlFor="college_name" className="text-sm text-zinc-300">College Name</Label>
                                            <Input
                                                id="college_name"
                                                value={formData.college_name}
                                                onChange={(e) => handleInputChange(e, 'college_name')}
                                                placeholder="Enter college name"
                                                disabled={isLoading}
                                                className="h-9 bg-[#0D0D0D] border-gray-800 text-white"
                                            />
                                        </div>
                                        
                                        <div className="space-y-2">
                                            <Label htmlFor="essay_prompt" className="text-sm text-zinc-300">Essay Prompt</Label>
                                            <Textarea
                                                id="essay_prompt"
                                                value={formData.essay_prompt}
                                                onChange={(e) => handleInputChange(e, 'essay_prompt')}
                                                placeholder="Enter essay prompt"
                                                disabled={isLoading}
                                                className="min-h-[100px] resize-none bg-[#0D0D0D] border-gray-800 text-white"
                                            />
                                        </div>
                                        
                                        <div className="space-y-2">
                                            <Label htmlFor="word_limit" className="text-sm text-zinc-300">Word Limit</Label>
                                            <Input
                                                id="word_limit"
                                                type="number"
                                                value={formData.word_limit || ''}
                                                onChange={(e) => handleInputChange(e, 'word_limit')}
                                                placeholder="Enter word limit"
                                                disabled={isLoading}
                                                className="h-9 bg-[#0D0D0D] border-gray-800 text-white"
                                            />
                                        </div>
                                    </div>

                                    <Button
                                        type="submit"
                                        disabled={isLoading}
                                        className="w-full h-9 bg-blue-600 hover:bg-blue-700 text-white"
                                    >
                                        {isLoading ? 'Generating Ideas...' : 'Generate Ideas'}
                                    </Button>
                                </form>
                            </div>
                        </div>
                    </div>
                ) : (
                    // Thread View
                    <div className="flex-1 flex flex-col overflow-hidden">
                        {(() => {
                            const thread = threads.find(t => t.thread_id === selectedThreadId);
                            return thread ? (
                                <EssayBrainstormThread thread={thread} />
                            ) : null;
                        })()}

                        <div className="border-t border-gray-800 bg-[#000000] px-4 py-3">
                            <div className="max-w-3xl mx-auto">
                                <Button
                                    onClick={handleSubmit}
                                    disabled={isLoading}
                                    className="w-full h-9 bg-blue-600 hover:bg-blue-700 text-white"
                                >
                                    {isLoading ? 'Generating Ideas...' : 'Generate More Ideas'}
                                </Button>
                            </div>
                        </div>
                    </div>
                )}
            </div>
        </div>
    );
} 