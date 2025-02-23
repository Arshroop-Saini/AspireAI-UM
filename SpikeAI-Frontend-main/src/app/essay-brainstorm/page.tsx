'use client';

import { useState, useEffect } from 'react';
import { useSession } from 'next-auth/react';
import { format } from 'date-fns';
import { JetBrains_Mono } from 'next/font/google';
import { PlusCircle, Trash2 } from 'lucide-react';
import { cn } from '@/lib/utils';
import { Button } from '@/components/ui/button';
import { Input } from '@/components/ui/input';
import { Textarea } from '@/components/ui/textarea';
import { Label } from '@radix-ui/react-label';
import { Alert, AlertDescription } from '@/components/ui/alert';
import { Card, CardContent, CardDescription, CardHeader, CardTitle } from '@/components/ui/card';
import { Avatar, AvatarFallback } from '@/components/ui/avatar';

interface EssayBrainstormForm {
    college_name: string;
    essay_prompt: string;
    word_limit: number;
}

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

interface RequestBody {
    college_name: string;
    essay_prompt: string;
    word_limit: number;
    is_new_thread: boolean;
    thread_id?: string;  // Optional for new threads
}

const mono = JetBrains_Mono({ subsets: ['latin'] });

export default function EssayBrainstormPage() {
    const { data: session } = useSession();
    const [isLoading, setIsLoading] = useState(false);
    const [threads, setThreads] = useState<EssayThread[]>([]);
    const [selectedThreadId, setSelectedThreadId] = useState<string | null>(null);
    const [success, setSuccess] = useState<string | null>(null);
    const [error, setError] = useState<string | null>(null);
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
        }
    };

    const handleSubmit = async (e: React.FormEvent) => {
        if (e) e.preventDefault();
        setIsLoading(true);
        setError(null);
        setSuccess(null);
        let newThreadId: string | undefined = undefined;

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

            // If this is a new thread, create it first
            if (!selectedThreadId) {
                const createThreadResponse = await fetch('/api/essay-brainstorm/threads', {
                    method: 'POST',
                    headers: {
                        'Content-Type': 'application/json',
                    },
                    body: JSON.stringify({
                        college_name: formData.college_name,
                        essay_prompt: formData.essay_prompt,
                        word_limit: formData.word_limit
                    }),
                });

                const threadData = await createThreadResponse.json();
                
                if (!createThreadResponse.ok || !threadData.success) {
                    throw new Error(threadData.error || 'Failed to create thread');
                }

                newThreadId = threadData.thread_id;
                if (!newThreadId) {
                    throw new Error('No thread ID received from server');
                }

                // Refresh threads and set the new thread as selected
                await fetchThreads();
                setSelectedThreadId(newThreadId);
            }

            const threadIdToUse = selectedThreadId || newThreadId;
            if (!threadIdToUse) {
                throw new Error('No thread ID available');
            }

            // Generate ideas for the thread
            const requestBody: RequestBody = {
                college_name: formData.college_name,
                essay_prompt: formData.essay_prompt,
                word_limit: formData.word_limit,
                is_new_thread: false,
                thread_id: threadIdToUse
            };
            
            const response = await fetch('/api/essay-brainstorm', {
                method: 'POST',
                headers: {
                    'Content-Type': 'application/json',
                },
                body: JSON.stringify(requestBody),
            });

            const data = await response.json();
            
            if (!response.ok || !data.success) {
                throw new Error(data.error || 'Failed to generate ideas');
            }

            // Refresh the threads list to get the latest ideas
            await fetchThreads();

            setIsLoading(false);
            setSuccess('Your essay ideas have been generated successfully.');

            // Scroll to the bottom to show new ideas
            setTimeout(() => {
                const chatContainer = document.querySelector('.overflow-y-auto');
                if (chatContainer) {
                    chatContainer.scrollTop = chatContainer.scrollHeight;
                }
            }, 100);

        } catch (error) {
            console.error('Error submitting essay:', error);
            setIsLoading(false);
            setSuccess(null);
            setError(error instanceof Error ? error.message : 'An error occurred');
        }
    };

    if (!session) {
        return (
            <div className="container mx-auto p-4">
                <Alert>
                    <AlertDescription>
                        Please sign in to use the essay brainstorming feature.
                    </AlertDescription>
                </Alert>
            </div>
        );
    }

    return (
        <div className="flex h-[calc(100vh-4rem)] overflow-hidden">
            <div className="w-80 border-r border-zinc-800/40 h-full bg-[#121214] p-4 space-y-4">
                <Button
                    onClick={handleNewThread}
                    variant="outline"
                    className={`w-full justify-start border-zinc-800/40 bg-[#18181B] hover:bg-[#121214] text-[#E87C3E] hover:text-[#FF8D4E] ${mono.className}`}
                >
                    <PlusCircle className="mr-2 h-4 w-4" />
                    New Essay
                </Button>

                <div className="space-y-2">
                    {threads.map((thread: EssayThread) => (
                        <div
                            key={thread.thread_id}
                            className={cn(
                                'p-3 rounded-lg cursor-pointer transition-all duration-200 group relative',
                                selectedThreadId === thread.thread_id 
                                    ? 'bg-[#18181B] border border-[#E87C3E]/20' 
                                    : 'hover:bg-[#18181B] border border-zinc-800/40'
                            )}
                            onClick={() => handleThreadSelect(thread.thread_id)}
                        >
                            <h3 className={`font-medium truncate pr-8 text-white ${mono.className}`}>{thread.college_name}</h3>
                            <p className={`text-sm text-zinc-400 truncate ${mono.className}`}>
                                {thread.essay_prompt}
                            </p>
                            <p className={`text-xs text-zinc-500 mt-1 ${mono.className}`}>
                                {format(new Date(thread.created_at), 'PPp')}
                            </p>
                            
                            <Button
                                variant="ghost"
                                size="sm"
                                className="absolute right-2 top-2 opacity-0 group-hover:opacity-100 transition-opacity p-0 h-8 w-8 hover:bg-red-500/10"
                                onClick={(e) => {
                                    e.stopPropagation();
                                    handleDeleteThread(thread.thread_id);
                                }}
                            >
                                <Trash2 className="h-4 w-4 text-red-400 hover:text-red-300" />
                            </Button>
                        </div>
                    ))}
                </div>
            </div>
            <div className="flex-1 flex flex-col bg-[#0A0A0B]">
                {selectedThreadId ? (
                    <>
                        <div className="sticky top-0 z-10 flex flex-col gap-1 bg-[#121214] px-6 py-4 border-b border-zinc-800/40">
                            <h2 className={`text-lg text-white ${mono.className}`}>
                                {threads.find(t => t.thread_id === selectedThreadId)?.college_name}
                            </h2>
                            <p className={`text-sm text-zinc-400 ${mono.className}`}>
                                {threads.find(t => t.thread_id === selectedThreadId)?.essay_prompt}
                            </p>
                            <p className={`text-xs text-zinc-500 ${mono.className}`}>
                                {threads.find(t => t.thread_id === selectedThreadId)?.created_at && 
                                 format(new Date(threads.find(t => t.thread_id === selectedThreadId)!.created_at), 'PPp')}
                            </p>
                        </div>

                        <div className="flex-1 overflow-y-auto p-6 space-y-6">
                            {threads.find(t => t.thread_id === selectedThreadId)?.ideas.map((idea, index) => (
                                <div key={index} className="flex gap-4">
                                    <Avatar className="h-8 w-8">
                                        <AvatarFallback className={`bg-[#18181B] text-white text-sm ${mono.className}`}>
                                            AI
                                        </AvatarFallback>
                                    </Avatar>
                                    <div className="flex-1 space-y-4">
                                        <div className={`p-4 rounded-lg bg-[#121214] border border-zinc-800/40 text-white ${mono.className}`}>
                                            {idea.content}
                                        </div>
                                        <div className={`text-xs text-zinc-500 ${mono.className}`}>
                                            {format(new Date(idea.created_at), 'PPp')}
                                        </div>
                                    </div>
                                </div>
                            ))}
                        </div>

                        <div className="p-4 bg-[#121214] border-t border-zinc-800/40">
                            <Button 
                                onClick={handleSubmit} 
                                disabled={isLoading}
                                className={`w-full bg-[#E87C3E] hover:bg-[#FF8D4E] text-white ${mono.className} h-11 transition-colors disabled:opacity-50 disabled:cursor-not-allowed disabled:hover:bg-[#E87C3E]`}
                            >
                                {isLoading ? 'Generating Ideas...' : 'Generate New Ideas'}
                            </Button>
                        </div>
                    </>
                ) : (
                    <div className="flex-1 p-6 overflow-y-auto">
                        <Card className="border border-zinc-800/40 bg-[#121214] shadow-xl">
                            <CardHeader className="space-y-2 pb-6">
                                <CardTitle className={`text-2xl text-white ${mono.className} tracking-tight`}>Essay Brainstorming</CardTitle>
                                <CardDescription className={`${mono.className} text-zinc-400 text-sm`}>
                                    Get AI-powered ideas and inspiration for your college application essay
                                </CardDescription>
                            </CardHeader>
                            <CardContent>
                                <form onSubmit={handleSubmit} className="space-y-8">
                                    <div className="space-y-4">
                                        <div className="space-y-2">
                                            <Label htmlFor="college_name" className={`text-sm text-zinc-300 ${mono.className}`}>College Name</Label>
                                            <Input
                                                id="college_name"
                                                value={formData.college_name}
                                                onChange={(e) => handleInputChange(e, 'college_name')}
                                                placeholder="Enter college name"
                                                required
                                                className={`h-11 bg-[#18181B] border-zinc-800/40 text-white ${mono.className} placeholder:text-zinc-600 focus:border-[#E87C3E] focus:ring-0 focus-visible:ring-0 focus-visible:ring-offset-0 transition-colors hover:border-zinc-700`}
                                            />
                                        </div>

                                        <div className="space-y-2">
                                            <Label htmlFor="essay_prompt" className={`text-sm text-zinc-300 ${mono.className}`}>Essay Prompt</Label>
                                            <Textarea
                                                id="essay_prompt"
                                                value={formData.essay_prompt}
                                                onChange={(e) => handleInputChange(e, 'essay_prompt')}
                                                placeholder="Enter the essay prompt"
                                                required
                                                className={`min-h-[120px] resize-none bg-[#18181B] border-zinc-800/40 text-white ${mono.className} placeholder:text-zinc-600 focus:border-[#E87C3E] focus:ring-0 focus-visible:ring-0 focus-visible:ring-offset-0 transition-colors hover:border-zinc-700`}
                                            />
                                        </div>

                                        <div className="space-y-2">
                                            <Label htmlFor="word_limit" className={`text-sm text-zinc-300 ${mono.className}`}>Word Limit</Label>
                                            <Input
                                                id="word_limit"
                                                type="number"
                                                min="0"
                                                value={formData.word_limit || ''}
                                                onChange={(e) => handleInputChange(e, 'word_limit')}
                                                placeholder="Enter maximum word limit"
                                                className={`h-11 bg-[#18181B] border-zinc-800/40 text-white ${mono.className} placeholder:text-zinc-600 focus:border-[#E87C3E] focus:ring-0 focus-visible:ring-0 focus-visible:ring-offset-0 transition-colors hover:border-zinc-700`}
                                            />
                                        </div>
                                    </div>

                                    {success && (
                                        <Alert variant="default" className="bg-green-500/10 border-green-500/20">
                                            <AlertDescription className={`text-green-400 ${mono.className}`}>{success}</AlertDescription>
                                        </Alert>
                                    )}

                                    {error && (
                                        <Alert variant="destructive" className="bg-red-500/10 border-red-500/20">
                                            <AlertDescription className={`text-red-400 ${mono.className}`}>{error}</AlertDescription>
                                        </Alert>
                                    )}

                                    <Button 
                                        type="submit" 
                                        disabled={isLoading}
                                        className={`w-full bg-[#E87C3E] hover:bg-[#FF8D4E] text-white ${mono.className} h-11 transition-colors disabled:opacity-50 disabled:cursor-not-allowed disabled:hover:bg-[#E87C3E]`}
                                    >
                                        {isLoading ? 'Generating Ideas...' : 'Generate Ideas'}
                                    </Button>
                                </form>
                            </CardContent>
                        </Card>
                    </div>
                )}
            </div>
        </div>
    );
} 